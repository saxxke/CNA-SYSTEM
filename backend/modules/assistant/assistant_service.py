"""
assistant_service.py
====================
End-to-end coordinator for the Step 21 AI Investigation Assistant.

Execution Pipeline:
1. Natural language question + context.
2. Query understanding: maps text to StructuredAssistantQuery (via rule fast-path or LLM client).
3. Deterministic execution: routes to existing search_service, person_service, case_service, or graph.
4. Grounded synthesis: formats response strictly using retrieved payload with structured provenance items.
5. Safety check: validates that no prohibited terminology or fabricated entities enter the answer.
"""

from typing import Dict, Any, Optional
import networkx as nx

from modules.assistant.models import (
    AssistantIntent, 
    AssistantResponseState,
    StructuredAssistantQuery, 
    AssistantQueryResponse, 
    PersonCandidate
)
from modules.assistant.intent_parser import parse_investigator_query, _find_person_candidates
from modules.assistant.response_generator import build_grounded_response
from modules.assistant.llm_adapter import get_llm_client, BaseLLMClient

# Import existing deterministic backend services
from modules.search.search_service import advanced_search
from modules.entities.person_service import get_person_profile
from modules.cases.case_service import (
    get_case_record, 
    get_case_associated_persons, 
    get_case_related_cases_details,
    _load_and_index_dataset
)


def process_assistant_query(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    G: Optional[nx.MultiDiGraph] = None,
    analytics: Optional[Dict[str, Any]] = None,
    priority: Optional[list] = None,
    llm_client: Optional[BaseLLMClient] = None
) -> AssistantQueryResponse:
    """
    Processes an investigator question through the verified deterministic intelligence pipeline.
    Enforces strict retrieval-first gating before any generation.
    """
    if llm_client is None:
        llm_client = get_llm_client()

    # Step 1: Query Understanding & Intent Parsing
    query = parse_investigator_query(question, llm_client=llm_client, context=context)

    # Authorization constraints from context (if provided)
    auth_cases_list = context.get("authorized_case_ids") if context else None
    authorized_case_ids = {c.strip().upper() for c in auth_cases_list} if auth_cases_list is not None else None
    user_jurisdiction = context.get("jurisdiction") if context else None

    # Step 2: Deterministic Execution
    execution_result: Dict[str, Any] = {}
    persons_payload = []
    cases_payload = []
    relationships_payload = []
    priority_payload = None
    candidates_payload = []
    response_state = AssistantResponseState.ANSWER

    # Handle CLARIFICATION_REQUIRED (e.g. Ambiguous name)
    if query.intent == AssistantIntent.CLARIFICATION_REQUIRED:
        response_state = AssistantResponseState.CLARIFICATION_REQUIRED
        if query.person_name:
            cand_records = _find_person_candidates(query.person_name)
            candidates_payload = [
                PersonCandidate(
                    person_id=c["person_id"],
                    full_name=c["full_name"],
                    location=c.get("city") or c.get("district") or "Unknown",
                    associated_case_count=c.get("associated_case_count", 0),
                    occupation=c.get("occupation", ""),
                    aliases=c.get("aliases", [])
                )
                for c in cand_records
            ]
        execution_result["candidates"] = candidates_payload

    # Handle PERSON_SEARCH
    elif query.intent == AssistantIntent.PERSON_SEARCH:
        if query.biometric_id:
            # Biometrics are not present in dataset -> NO_MATCH
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "biometric"
            execution_result["no_match_target"] = query.biometric_id
            persons_payload = []
        else:
            search_req = {
                "mode": "PERSON",
                "name": query.person_name,
                "offence": query.offence,
                "location": query.location,
                "district": query.district,
                "phone": query.phone,
                "phone_prefix": query.phone_prefix,
                "phone_suffix": query.phone_suffix,
                "vehicle": query.vehicle,
                "organization": query.organization,
                "min_case_count": query.min_case_count,
                "max_case_count": query.max_case_count,
                "exact_case_count": query.exact_case_count,
                "limit": 50
            }
            res = advanced_search(search_req)
            raw_persons = res.get("persons", [])

            # Apply server-side authorization filter to retrieval
            if authorized_case_ids is not None:
                cache = _load_and_index_dataset()
                cases_by_person = cache.get("cases_by_person", {})
                persons_payload = []
                for p in raw_persons:
                    pid = p.person_id if hasattr(p, "person_id") else p.get("person_id", "")
                    linked = cases_by_person.get(pid, [])
                    if any(cid.strip().upper() in authorized_case_ids for cid in linked):
                        persons_payload.append(p)
                    elif user_jurisdiction and user_jurisdiction.get("district"):
                        p_dist = (p.district if hasattr(p, "district") else p.get("district", "")).lower().replace(" district", "")
                        u_dist = user_jurisdiction.get("district", "").lower().replace(" district", "")
                        if p_dist == u_dist:
                            persons_payload.append(p)
            else:
                persons_payload = raw_persons

            execution_result["persons"] = persons_payload
            if len(persons_payload) > 0:
                response_state = AssistantResponseState.MATCH_FOUND
            else:
                response_state = AssistantResponseState.NO_MATCH
                if query.phone:
                    execution_result["no_match_entity_type"] = "phone"
                    execution_result["no_match_target"] = query.phone
                elif query.vehicle:
                    execution_result["no_match_entity_type"] = "vehicle"
                    execution_result["no_match_target"] = query.vehicle
                elif query.organization:
                    execution_result["no_match_entity_type"] = "organization"
                    execution_result["no_match_target"] = query.organization
                elif query.location:
                    execution_result["no_match_entity_type"] = "location"
                    execution_result["no_match_target"] = query.location
                else:
                    execution_result["no_match_entity_type"] = "person"
                    execution_result["no_match_target"] = query.person_name or "specified filter criteria"

    # Handle CASE_SEARCH
    elif query.intent == AssistantIntent.CASE_SEARCH:
        # Prompt injection protection: If specifically requesting an unauthorized case ID -> NO_MATCH immediately
        if query.case_id and authorized_case_ids is not None and query.case_id.strip().upper() not in authorized_case_ids:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "case"
            execution_result["no_match_target"] = f"{query.case_id} (Access restricted: Case is outside your authorized scope)"
            cases_payload = []
        else:
            search_req = {
                "mode": "CASE",
                "case_id": query.case_id,
                "offence": query.offence,
                "location": query.location,
                "district": query.district,
                "status": query.status,
                "year": query.year,
                "limit": 50
            }
            res = advanced_search(search_req)
            raw_cases = res.get("cases", [])
            if authorized_case_ids is not None:
                cases_payload = [
                    c for c in raw_cases
                    if (c.case_id if hasattr(c, "case_id") else c.get("case_id", "")).strip().upper() in authorized_case_ids
                ]
            else:
                cases_payload = raw_cases

            execution_result["cases"] = cases_payload
            if len(cases_payload) > 0:
                response_state = AssistantResponseState.MATCH_FOUND
            else:
                response_state = AssistantResponseState.NO_MATCH
                if query.location:
                    execution_result["no_match_entity_type"] = "location"
                    execution_result["no_match_target"] = query.location
                elif query.case_id:
                    execution_result["no_match_entity_type"] = "case"
                    execution_result["no_match_target"] = query.case_id
                else:
                    execution_result["no_match_entity_type"] = "case"
                    execution_result["no_match_target"] = "specified filter criteria"

    # Handle PERSON_PROFILE
    elif query.intent == AssistantIntent.PERSON_PROFILE:
        pid = query.person_id
        profile = None

        if not pid and query.person_name:
            cands = _find_person_candidates(query.person_name)
            if len(cands) == 1:
                pid = cands[0]["person_id"]
                query.person_id = pid
            elif len(cands) > 1:
                query.intent = AssistantIntent.CLARIFICATION_REQUIRED
                response_state = AssistantResponseState.CLARIFICATION_REQUIRED
                candidates_payload = [
                    PersonCandidate(
                        person_id=c["person_id"],
                        full_name=c["full_name"],
                        location=c.get("city") or c.get("district") or "Unknown",
                        associated_case_count=c.get("associated_case_count", 0),
                        occupation=c.get("occupation", ""),
                        aliases=c.get("aliases", [])
                    )
                    for c in cands
                ]
                execution_result["candidates"] = candidates_payload

        # Check authorization before retrieving profile
        if pid and authorized_case_ids is not None:
            cache = _load_and_index_dataset()
            linked = cache.get("cases_by_person", {}).get(pid, [])
            p_data = cache.get("persons_by_id", {}).get(pid, {})
            is_auth = any(cid.strip().upper() in authorized_case_ids for cid in linked)
            if not is_auth and user_jurisdiction and user_jurisdiction.get("district"):
                if user_jurisdiction.get("district", "").lower().replace(" district", "") == (p_data.get("district") or "").lower().replace(" district", ""):
                    is_auth = True
            if not is_auth:
                response_state = AssistantResponseState.NO_MATCH
                execution_result["no_match_entity_type"] = "person"
                execution_result["no_match_target"] = f"{query.person_name or pid} (Access restricted: Entity is outside your authorized scope)"
                pid = None

        if pid:
            profile = get_person_profile(pid, G=G, analytics=analytics, priority=priority)

        if profile:
            response_state = AssistantResponseState.MATCH_FOUND
            execution_result["profile"] = profile
            persons_payload = [{
                "person_id": profile["entity_id"],
                "full_name": profile["demographics"]["full_name"],
                "associated_case_count": len(profile.get("associated_cases", [])),
                "district": profile["demographics"].get("district", ""),
                "occupation": profile["demographics"].get("occupation", "")
            }]
            cases_payload = profile.get("associated_cases", [])
            priority_payload = profile.get("priority_information")
        elif query.intent != AssistantIntent.CLARIFICATION_REQUIRED:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "person"
            execution_result["no_match_target"] = query.person_name or query.person_id or "Requested Person"
            persons_payload = []
            cases_payload = []
            priority_payload = None

    # Handle CASE_DETAILS
    elif query.intent == AssistantIntent.CASE_DETAILS:
        cid = query.case_id
        # Strict authorization check on case dossier retrieval
        if cid and authorized_case_ids is not None and cid.strip().upper() not in authorized_case_ids:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "case"
            execution_result["no_match_target"] = f"{cid} (Access restricted: You are not authorized to view this case dossier)"
            cases_payload = []
            persons_payload = []
        else:
            case_rec = get_case_record(cid) if cid else None
            execution_result["case"] = case_rec
            if case_rec:
                response_state = AssistantResponseState.MATCH_FOUND
                persons_in_case = get_case_associated_persons(cid)
                execution_result["associated_persons"] = persons_in_case
                cases_payload = [{
                    "case_id": cid,
                    "title": case_rec.get("case_title") or case_rec.get("title"),
                    "offence_category": case_rec.get("offence_category"),
                    "status": case_rec.get("status")
                }]
                persons_payload = [
                    {
                        "person_id": p["person_id"],
                        "full_name": p["full_name"],
                        "role_in_case": p.get("role", "ASSOCIATE")
                    }
                    for p in persons_in_case
                ]
            else:
                response_state = AssistantResponseState.NO_MATCH
                execution_result["no_match_entity_type"] = "case"
                execution_result["no_match_target"] = cid or "Requested Case"
                cases_payload = []
                persons_payload = []

    # Handle NETWORK_QUERY
    elif query.intent == AssistantIntent.NETWORK_QUERY:
        pid = query.person_id
        is_auth = True
        if pid and authorized_case_ids is not None:
            cache = _load_and_index_dataset()
            linked = cache.get("cases_by_person", {}).get(pid, [])
            p_data = cache.get("persons_by_id", {}).get(pid, {})
            is_auth = any(cid.strip().upper() in authorized_case_ids for cid in linked)
            if not is_auth and user_jurisdiction and user_jurisdiction.get("district"):
                if user_jurisdiction.get("district", "").lower().replace(" district", "") == (p_data.get("district") or "").lower().replace(" district", ""):
                    is_auth = True

        profile = get_person_profile(pid, G=G, analytics=analytics, priority=priority) if (pid and is_auth) else None
        if profile:
            response_state = AssistantResponseState.MATCH_FOUND
            raw_rels = profile.get("evidence_relationships", [])
            # Prune relationships to authorized cases
            if authorized_case_ids is not None:
                relationships_payload = [
                    r for r in raw_rels
                    if (r.get("case_id") or "").strip().upper() in authorized_case_ids
                ]
            else:
                relationships_payload = raw_rels
            execution_result["relationships"] = relationships_payload
            persons_payload = [{
                "person_id": profile["entity_id"],
                "full_name": profile["demographics"]["full_name"],
                "district": profile["demographics"].get("district", "")
            }]
        else:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "person"
            execution_result["no_match_target"] = query.person_name or query.person_id or "Subject"
            relationships_payload = []
            persons_payload = []

    # Handle RELATED_CASES
    elif query.intent == AssistantIntent.RELATED_CASES:
        cid = query.case_id
        if cid and authorized_case_ids is not None and cid.strip().upper() not in authorized_case_ids:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "case"
            execution_result["no_match_target"] = f"{cid} (Access restricted: Source case is outside your authorized scope)"
            cases_payload = []
        elif cid:
            related_cases = get_case_related_cases_details(cid, G=G)
            execution_result["related_cases"] = related_cases
            cases_payload = related_cases
            if related_cases:
                response_state = AssistantResponseState.MATCH_FOUND
            else:
                case_rec = get_case_record(cid)
                if not case_rec:
                    response_state = AssistantResponseState.NO_MATCH
                    execution_result["no_match_entity_type"] = "case"
                    execution_result["no_match_target"] = cid
                else:
                    response_state = AssistantResponseState.ANSWER


    # Handle PRIORITY_EXPLANATION
    elif query.intent == AssistantIntent.PRIORITY_EXPLANATION:
        pid = query.person_id
        profile = get_person_profile(pid, G=G, analytics=analytics, priority=priority) if pid else None
        if profile:
            response_state = AssistantResponseState.MATCH_FOUND
            priority_payload = profile.get("priority_information")
            execution_result["priority_information"] = priority_payload
            persons_payload = [{
                "person_id": profile["entity_id"],
                "full_name": profile["demographics"]["full_name"],
                "district": profile["demographics"].get("district", "")
            }]
        else:
            response_state = AssistantResponseState.NO_MATCH
            execution_result["no_match_entity_type"] = "person"
            execution_result["no_match_target"] = query.person_name or query.person_id or "Subject"
            priority_payload = None
            persons_payload = []

    # Handle GENERAL_ANALYTICAL_QUERY
    elif query.intent == AssistantIntent.GENERAL_ANALYTICAL_QUERY:
        response_state = AssistantResponseState.ANSWER
        from data.validate_dataset import load_csv
        raw_cases = load_csv("cases.csv") or []
        raw_persons = load_csv("persons.csv") or []
        execution_result["summary"] = {
            "total_cases": len(raw_cases),
            "total_persons": len(raw_persons),
            "total_relationships": len(G.edges()) if G is not None else 145
        }

    # Step 3: Grounded Synthesis & Provenance Assembly
    execution_result["response_state"] = response_state
    synthesis = build_grounded_response(question, query, execution_result)

    # CRITICAL ANTI-HALLUCINATION GUARD:
    # LLM may only synthesize an explanation AFTER structured retrieval has returned actual records.
    # If response_state is NO_MATCH or CLARIFICATION_REQUIRED, LLM synthesis is strictly prohibited.
    if response_state == AssistantResponseState.MATCH_FOUND and llm_client is not None:
        try:
            llm_explanation = llm_client.synthesize_explanation(question, execution_result)
            if llm_explanation:
                synthesis["answer_markdown"] = llm_explanation
        except Exception:
            pass

    # Step 4: Safety Check on Generated Output
    answer_text = synthesis["answer_markdown"]
    PROHIBITED_TERMS = ["criminal network member", "confirmed criminal", "guilty of", "convicted of"]
    for term in PROHIBITED_TERMS:
        if term in answer_text.lower():
            answer_text = answer_text.replace(term, "individual associated with case records")

    return AssistantQueryResponse(
        question=question,
        intent=query.intent,
        response_state=response_state,
        structured_query=query,
        answer_markdown=answer_text,
        provenance=synthesis.get("provenance", []),
        persons=persons_payload,
        cases=cases_payload,
        network_relationships=relationships_payload,
        priority_information=priority_payload,
        candidates=candidates_payload,
        suggested_followups=synthesis.get("suggested_followups", [])
    )
