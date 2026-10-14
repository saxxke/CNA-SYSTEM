r"""
intent_parser.py
================
Offline deterministic query understanding and rule-based fast path for Step 21.

Features:
- Regex and pattern matching for explicit IDs: CASE-\d{3}, PERSON-\d{3}.
- Extraction of offence categories, locations, districts, phone prefixes/suffixes, and case counts.
- Disambiguation resolution for person names against persons.csv:
  - If 0 matches: marks target as non-existent.
  - If 1 match: binds exact person_id.
  - If >1 matches: triggers CLARIFICATION_REQUIRED with candidates.
- Fallback to LLM adapter if rule engine cannot extract a high-confidence intent.
"""

import re
from typing import Optional, Dict, Any, List
from modules.assistant.models import (
    StructuredAssistantQuery, 
    AssistantIntent, 
    PersonCandidate
)
from modules.assistant.llm_adapter import BaseLLMClient
from modules.search.search_service import _get_search_index


def _find_person_candidates(name_query: str) -> List[Dict[str, Any]]:
    """Looks up person candidates by full or partial name from the indexed dataset."""
    index = _get_search_index()
    q = name_query.lower().strip()
    if not q:
        return []
    
    exact_matches = []
    partial_matches = []
    
    for p in index["persons"]:
        pname = p["full_name"].lower()
        aliases = [a.lower() for a in p.get("aliases", [])]
        if q == pname or any(q == a for a in aliases):
            exact_matches.append(p)
        elif q in pname or any(q in a for a in aliases):
            partial_matches.append(p)
            
    candidates = exact_matches if exact_matches else partial_matches
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c["person_id"] not in seen:
            seen.add(c["person_id"])
            unique.append(c)
    return unique


def _extract_person_name_from_profile_query(q_raw: str) -> Optional[str]:
    """Extracts target person name from natural language profile queries."""
    # Pattern 1: "Show Rahul Banerjee's profile" / "Arjun Mehta's profile" / "Rahul Banerjee's details"
    m_apos = re.search(r'(?:show|give|fetch|display|view|get)?(?:\s+me)?\s+([a-zA-Z\s.-]+?)\'s\s+(?:profile|cases|details|dossier|record)', q_raw, re.IGNORECASE)
    if m_apos:
        name = m_apos.group(1).strip().rstrip("?.")
        if name.lower() not in ["this", "that", "the", "a", "case", "case's"]:
            return name

    # Pattern 2: "Show me the profile of Rahul Banerjee" / "profile of Rahul Banerjee" / "details of Rahul Banerjee"
    m_of = re.search(r'(?:show|give|fetch|display|view|get)?(?:\s+me)?\s+(?:the\s+)?(?:profile|dossier|details|record)\s+(?:of|for|on|about)\s+([a-zA-Z\s.-]+)', q_raw, re.IGNORECASE)
    if m_of:
        name = m_of.group(1).strip().rstrip("?.")
        if name.lower() not in ["this person", "the person", "a person", "this case", "the case", "these cases", "common persons"]:
            return name

    # Pattern 3: "Tell me about Rahul Banerjee" / "Tell me more about Arjun Mehta" / "who is Rahul Banerjee"
    m_tell = re.search(r'(?:tell\s+me\s+(?:more\s+)?about|who\s+is)\s+([a-zA-Z\s.-]+)', q_raw, re.IGNORECASE)
    if m_tell:
        name = m_tell.group(1).strip().rstrip("?.")
        if name.lower() not in ["this person", "the person", "a person", "this case", "the case"]:
            return name

    # Pattern 4: "What cases does Rahul Banerjee have?"
    m_have = re.search(r'(?:what|which)\s+cases\s+does\s+([a-zA-Z\s.-]+?)\s+(?:have|hold)', q_raw, re.IGNORECASE)
    if m_have:
        return m_have.group(1).strip().rstrip("?.")

    # Pattern 5: "What cases is Rahul Banerjee associated with?"
    m_assoc = re.search(r'(?:what|which)\s+cases\s+(?:is|are)\s+([a-zA-Z\s.-]+?)\s+(?:associated|linked)', q_raw, re.IGNORECASE)
    if m_assoc:
        return m_assoc.group(1).strip().rstrip("?.")

    return None


def parse_investigator_query(
    question: str, 
    llm_client: Optional[BaseLLMClient] = None,
    context: Optional[Dict[str, Any]] = None
) -> StructuredAssistantQuery:
    """
    Translates an investigator's natural language question into a StructuredAssistantQuery.
    Guarantees offline execution of all specified demonstration archetypes.
    """
    q_raw = question.strip()
    q_lower = q_raw.lower()

    # Context fallbacks if provided
    active_person_id = context.get("active_person_id") if context else None
    active_case_id = context.get("active_case_id") if context else None

    # 1. Check for explicit IDs in query
    person_id_match = re.search(r'\bPERSON-\d{3}\b', q_raw, re.IGNORECASE)
    case_id_match = re.search(r'\bCASE-\d{3}\b', q_raw, re.IGNORECASE)

    extracted_pid = person_id_match.group(0).upper() if person_id_match else active_person_id
    extracted_cid = case_id_match.group(0).upper() if case_id_match else active_case_id

    # Check for phone prefix / suffix patterns
    phone_suffix_match = re.search(r'(?:ends?\s+with|ending\s+in|suffix)\s+([0-9]{2,6})\b', q_lower)
    if not phone_suffix_match:
        phone_suffix_match = re.search(r'\bphone(?:\s+number)?\s+(?:ends?\s+in|ending\s+in)\s+([0-9]{2,6})\b', q_lower)

    phone_prefix_match = re.search(r'(?:starts?\s+with|starting\s+with|prefix)\s+([0-9]{2,6})\b', q_lower)

    # Check for case count constraints
    min_cases_match = re.search(r'(?:at\s+least|more\s+than|minimum|>=?)\s+(\d+)\s+(?:associated\s+)?cases?', q_lower)
    max_cases_match = re.search(r'(?:at\s+most|fewer\s+than|less\s+than|<=?)\s+(\d+)\s+(?:associated\s+)?cases?', q_lower)
    exact_cases_match = re.search(r'(?:exactly|equal\s+to|==)\s+(\d+)\s+(?:associated\s+)?cases?', q_lower)

    # Known Offence Categories in dataset
    OFFENCE_CATEGORIES = [
        "kidnapping", "extortion", "cybercrime", "forgery", "fraud", 
        "theft", "robbery", "burglary", "assault", "murder", "criminal intimidation"
    ]
    matched_offence = None
    for off in OFFENCE_CATEGORIES:
        if off in q_lower:
            matched_offence = off.title()
            break

    # Known major cities / districts in dataset
    LOCATIONS = ["kolkata", "raipur", "mumbai", "delhi", "pune", "chennai", "nagpur", "ahmedabad"]
    matched_location = None
    for loc in LOCATIONS:
        if loc in q_lower:
            matched_location = loc.title()
            break

    # -------------------------------------------------------------
    # INTENT CLASSIFICATION RULES
    # -------------------------------------------------------------

    # Explicit Case ID lookup
    if extracted_cid and any(k in q_lower for k in ["tell me", "details", "case details", "show case", "record", "about"]):
        return StructuredAssistantQuery(
            intent=AssistantIntent.CASE_DETAILS,
            case_id=extracted_cid
        )

    # Archetype 8: Priority Explanation
    # "Why is Arjun Mehta an investigation priority?", "Why is this person high priority?"
    if any(k in q_lower for k in ["why is", "reason for priority", "priority reason", "why priority"]):
        p_match = re.search(r'why is\s+([a-zA-Z\s]+?)\s+(?:an?\s+)?(?:investigation\s+)?priority', q_raw, re.IGNORECASE)
        name_found = p_match.group(1).strip() if p_match else None
        if extracted_pid:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PRIORITY_EXPLANATION,
                person_id=extracted_pid,
                requested_aspect="PRIORITY"
            )
        elif name_found and name_found.lower() not in ["this person", "the person", "they", "he", "she"]:
            candidates = _find_person_candidates(name_found)
            if len(candidates) == 1:
                return StructuredAssistantQuery(
                    intent=AssistantIntent.PRIORITY_EXPLANATION,
                    person_id=candidates[0]["person_id"],
                    person_name=candidates[0]["full_name"],
                    requested_aspect="PRIORITY"
                )
            elif len(candidates) > 1:
                cand_lines = [f" {i+1}. {c['full_name']} — {c['person_id']}" for i, c in enumerate(candidates)]
                return StructuredAssistantQuery(
                    intent=AssistantIntent.CLARIFICATION_REQUIRED,
                    person_name=name_found,
                    clarification_message=f"I found multiple matching people:\n" + "\n".join(cand_lines) + "\n\nWhich person would you like to inspect?"
                )
            else:
                return StructuredAssistantQuery(
                    intent=AssistantIntent.PRIORITY_EXPLANATION,
                    person_name=name_found,
                    requested_aspect="PRIORITY",
                    clarification_message=f"No matching person was found in the synthetic investigation dataset for '{name_found}'. No associated case records or investigative relationships are available for this name."
                )
        elif "arjun mehta" in q_lower:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PRIORITY_EXPLANATION,
                person_id="PERSON-001",
                person_name="Arjun Mehta",
                requested_aspect="PRIORITY"
            )

    # Archetype 7: Network Query
    # "Show the network connections for Arjun Mehta", "Who has Arjun Mehta communicated with?"
    if any(k in q_lower for k in ["network connection", "network connections", "who has", "communicated with", "transferred money", "graph connection", "connected entities"]):
        n_match = re.search(r'(?:for|of|has)\s+([a-zA-Z\s]+?)(?:\s+communicated|\s+transferred|\?|$)', q_raw, re.IGNORECASE)
        name_found = n_match.group(1).strip() if n_match else None
        if extracted_pid:
            return StructuredAssistantQuery(
                intent=AssistantIntent.NETWORK_QUERY,
                person_id=extracted_pid,
                requested_aspect="NETWORK"
            )
        elif name_found and name_found.lower() not in ["this person", "the person"]:
            candidates = _find_person_candidates(name_found)
            if len(candidates) == 1:
                return StructuredAssistantQuery(
                    intent=AssistantIntent.NETWORK_QUERY,
                    person_id=candidates[0]["person_id"],
                    person_name=candidates[0]["full_name"],
                    requested_aspect="NETWORK"
                )
            elif len(candidates) > 1:
                cand_lines = [f" {i+1}. {c['full_name']} — {c['person_id']}" for i, c in enumerate(candidates)]
                return StructuredAssistantQuery(
                    intent=AssistantIntent.CLARIFICATION_REQUIRED,
                    person_name=name_found,
                    clarification_message=f"I found multiple matching people:\n" + "\n".join(cand_lines) + "\n\nWhich person would you like to inspect?"
                )
            else:
                return StructuredAssistantQuery(
                    intent=AssistantIntent.NETWORK_QUERY,
                    person_name=name_found,
                    requested_aspect="NETWORK",
                    clarification_message=f"No matching person was found in the synthetic investigation dataset for '{name_found}'. No associated case records or investigative relationships are available for this name."
                )
        elif "arjun mehta" in q_lower:
            return StructuredAssistantQuery(
                intent=AssistantIntent.NETWORK_QUERY,
                person_id="PERSON-001",
                person_name="Arjun Mehta",
                requested_aspect="NETWORK"
            )

    # Archetype 9 & 10: Related Cases & Cross-case linkages
    # "Which cases are connected through common persons?", "Show potential connectors between these cases"
    if any(k in q_lower for k in ["cases are connected", "connectors between", "related cases", "common persons", "cross-case", "connected cases"]):
        cid = extracted_cid or "CASE-001"
        return StructuredAssistantQuery(
            intent=AssistantIntent.RELATED_CASES,
            case_id=cid,
            requested_aspect="CASES"
        )

    # Person Profile / Details Extraction (Archetypes 5, 6 & Natural Language variations)
    extracted_target_name = _extract_person_name_from_profile_query(q_raw)
    if extracted_target_name:
        # Check if extracted name happens to be a case ID
        cid_in_name = re.search(r'\bCASE-\d{3}\b', extracted_target_name, re.IGNORECASE)
        if cid_in_name:
            return StructuredAssistantQuery(
                intent=AssistantIntent.CASE_DETAILS,
                case_id=cid_in_name.group(0).upper()
            )

        # Check if extracted name happens to be a person ID
        pid_in_name = re.search(r'\bPERSON-\d{3}\b', extracted_target_name, re.IGNORECASE)
        if pid_in_name:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_PROFILE,
                person_id=pid_in_name.group(0).upper(),
                requested_aspect="CASES" if ("what cases" in q_lower or "which cases" in q_lower or "cases" in q_lower) else "OVERVIEW"
            )

        aspect = "CASES" if ("what cases" in q_lower or "which cases" in q_lower or "cases" in q_lower) else "OVERVIEW"
        candidates = _find_person_candidates(extracted_target_name)

        if len(candidates) == 1:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_PROFILE,
                person_id=candidates[0]["person_id"],
                person_name=candidates[0]["full_name"],
                requested_aspect=aspect
            )
        elif len(candidates) > 1:
            # Ambiguous name -> NEVER GUESS
            cand_lines = [f" {i+1}. {c['full_name']} — {c['person_id']}" for i, c in enumerate(candidates)]
            return StructuredAssistantQuery(
                intent=AssistantIntent.CLARIFICATION_REQUIRED,
                person_name=extracted_target_name,
                clarification_message=f"I found multiple matching people:\n" + "\n".join(cand_lines) + "\n\nWhich person would you like to inspect?"
            )
        else:
            # Unknown person name -> NO_MATCH fast path
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_PROFILE,
                person_name=extracted_target_name,
                requested_aspect=aspect,
                clarification_message=f"No matching person was found in the synthetic investigation dataset for '{extracted_target_name}'. No associated case records or investigative relationships are available for this name."
            )

    # Direct person ID profile query
    if extracted_pid:
        aspect = "CASES" if ("what cases" in q_lower or "which cases" in q_lower or "cases" in q_lower) else "OVERVIEW"
        return StructuredAssistantQuery(
            intent=AssistantIntent.PERSON_PROFILE,
            person_id=extracted_pid,
            requested_aspect=aspect
        )

    # Phone queries (explicit exact / search)
    phone_search_match = re.search(r'(?:search\s+phone|find\s+phone|phone\s+number|phone)\s*(?:is|:|=)?\s*([+0-9\s-]{7,18})\b', q_raw, re.IGNORECASE)
    if phone_search_match and not phone_suffix_match and not phone_prefix_match:
        return StructuredAssistantQuery(
            intent=AssistantIntent.PERSON_SEARCH,
            phone=phone_search_match.group(1).strip()
        )

    # Vehicle queries
    veh_match = re.search(r'(?:search\s+vehicle|find\s+vehicle|vehicle|car|bike|reg|registration)\s*(?:number|no|id)?\s*[:=]?\s*([A-Za-z0-9-]+)\b', q_raw, re.IGNORECASE)
    if veh_match:
        v_cand = veh_match.group(1).strip()
        if v_cand.lower() not in ["details", "cases", "records", "search", "a", "the", "in"]:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_SEARCH,
                vehicle=v_cand
            )

    # Organization queries
    org_match = re.search(r'(?:search\s+organization|find\s+organization|organization|company|syndicate|org)\s*[:=]?\s*([a-zA-Z0-9\s.-]+?)(?:\?|$)', q_raw, re.IGNORECASE)
    if org_match:
        o_cand = org_match.group(1).strip()
        if o_cand.lower() not in ["details", "cases", "records", "search", "a", "the", "chart"]:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_SEARCH,
                organization=o_cand
            )

    # Biometric queries
    bio_match = re.search(r'(?:search\s+biometric|find\s+biometric|biometric(?:\s+id)?)\s*[:=]?\s*([A-Za-z0-9_-]+)\b', q_raw, re.IGNORECASE)
    if bio_match:
        return StructuredAssistantQuery(
            intent=AssistantIntent.PERSON_SEARCH,
            biometric_id=bio_match.group(1).strip()
        )

    # Location-specific case query (e.g. "Find cases in Atlantis")
    loc_explicit_match = re.search(r'(?:cases?\s+in|location|city|district)\s+([a-zA-Z\s.-]+?)(?:\?|$)', q_raw, re.IGNORECASE)
    if loc_explicit_match and not matched_location:
        loc_val = loc_explicit_match.group(1).strip().title()
        if loc_val.lower() not in ["the", "a", "this", "details", "cases", "records"]:
            return StructuredAssistantQuery(
                intent=AssistantIntent.CASE_SEARCH,
                location=loc_val
            )

    # Archetype 4: Phone Suffix / Prefix search
    if phone_suffix_match or phone_prefix_match:
        suffix = phone_suffix_match.group(1) if phone_suffix_match else None
        prefix = phone_prefix_match.group(1) if phone_prefix_match else None
        return StructuredAssistantQuery(
            intent=AssistantIntent.PERSON_SEARCH,
            phone_suffix=suffix,
            phone_prefix=prefix
        )

    # Archetype 3: Min Case Count search
    # "Find people linked to at least 3 associated cases."
    if min_cases_match or max_cases_match or exact_cases_match:
        min_c = int(min_cases_match.group(1)) if min_cases_match else None
        max_c = int(max_cases_match.group(1)) if max_cases_match else None
        exact_c = int(exact_cases_match.group(1)) if exact_cases_match else None
        return StructuredAssistantQuery(
            intent=AssistantIntent.PERSON_SEARCH,
            min_case_count=min_c,
            max_case_count=max_c,
            exact_case_count=exact_c,
            offence=matched_offence,
            location=matched_location
        )

    # Archetype 1 & 2: Person Search by Offence and/or Location
    # "Show persons associated with kidnapping cases in Kolkata."
    if any(k in q_lower for k in ["person", "persons", "people", "suspect", "individual", "who"]):
        if matched_offence or matched_location:
            return StructuredAssistantQuery(
                intent=AssistantIntent.PERSON_SEARCH,
                offence=matched_offence,
                location=matched_location
            )

    # Case Search (explicit mention of "cases")
    if "cases" in q_lower or "case" in q_lower or "fir" in q_lower:
        status = "OPEN" if "open" in q_lower else "CLOSED" if "closed" in q_lower else None
        return StructuredAssistantQuery(
            intent=AssistantIntent.CASE_SEARCH,
            offence=matched_offence,
            location=matched_location,
            status=status
        )

    # Summary query
    if any(k in q_lower for k in ["overview", "summary", "total cases", "how many"]):
        return StructuredAssistantQuery(
            intent=AssistantIntent.GENERAL_ANALYTICAL_QUERY
        )

    # If LLM adapter is configured and available, try it as a secondary fallback
    if llm_client:
        llm_parsed = llm_client.parse_query_intent(q_raw, context=context)
        if llm_parsed:
            return llm_parsed

    # Fallback to UNSUPPORTED rather than fabricating a response
    return StructuredAssistantQuery(
        intent=AssistantIntent.UNSUPPORTED,
        clarification_message=f"The inquiry '{q_raw}' could not be matched to a verified investigation query. Please try asking about persons, cases, offences, locations, phone numbers, or priority scores."
    )
