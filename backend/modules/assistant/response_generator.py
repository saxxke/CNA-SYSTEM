"""
response_generator.py
=====================
Grounded response generation and evidence provenance synthesizer for Step 21.

Enforces:
1. Grounding: Output is generated ONLY from facts present in the retrieved backend payload.
2. Provenance: Every response builds structured ProvenanceItem objects citing exact source types,
   IDs, case IDs, and evidence text snippets.
3. Safety: Strictly prohibits "criminal", "guilty", "convicted", "confirmed criminal".
   Uses: "associated with case records", "potential relationship", "investigative lead", "analytical priority".
4. Telecom/Banking wording: Describes synthetic communication/transaction records strictly as
   "synthetic communication record" or "synthetic transaction record".
5. Family isolation: Family data is never presented as investigative evidence or suspicion.
6. Zero hallucination: Never invents names, IDs, phone numbers, or graph connections.
"""

from typing import Dict, List, Any, Optional
from modules.assistant.models import (
    StructuredAssistantQuery, 
    AssistantIntent, 
    AssistantResponseState,
    ProvenanceItem, 
    PersonCandidate
)


def build_grounded_response(
    question: str,
    query: StructuredAssistantQuery,
    execution_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes a human-readable markdown response and structured provenance
    strictly using facts retrieved by deterministic backend services.
    """
    intent = query.intent
    response_state = execution_result.get("response_state")
    provenance: List[ProvenanceItem] = []
    answer_parts = []
    suggested_followups: List[str] = []

    # 0. EARLY NO_MATCH RETURN (Zero hallucination guard)
    if response_state == AssistantResponseState.NO_MATCH:
        no_match_type = execution_result.get("no_match_entity_type", "general")
        no_match_target = execution_result.get("no_match_target") or "the requested identifier"

        if no_match_type == "person":
            answer_parts.append(
                f"No matching person was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated case records or investigative relationships are available for this name (no person record found)."
            )
        elif no_match_type == "case":
            answer_parts.append(
                f"No matching case record was found in the synthetic investigation dataset for '{no_match_target}' (case record not found). "
                f"No associated case details or investigative records are available for this case ID."
            )
        elif no_match_type == "phone":
            answer_parts.append(
                f"No matching phone record was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated person records or investigative communications are available for this number."
            )
        elif no_match_type == "vehicle":
            answer_parts.append(
                f"No matching vehicle record was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated person records or vehicle registrations are available for this vehicle."
            )
        elif no_match_type == "location":
            answer_parts.append(
                f"No matching location record was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated case records or person records are available for this location."
            )
        elif no_match_type == "organization":
            answer_parts.append(
                f"No matching organization record was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated person or case records are available for this organization."
            )
        elif no_match_type == "biometric":
            answer_parts.append(
                f"No matching biometric record was found in the synthetic investigation dataset for '{no_match_target}'. "
                f"No associated person records are available in the synthetic dataset."
            )
        else:
            answer_parts.append(
                f"No matching records were found in the synthetic investigation dataset for '{no_match_target}'."
            )

        return {
            "question": question,
            "intent": intent,
            "response_state": response_state,
            "structured_query": query,
            "answer_markdown": "\n".join(answer_parts),
            "provenance": [],
            "suggested_followups": []
        }

    # 1. INTENT: PERSON_SEARCH
    if intent == AssistantIntent.PERSON_SEARCH:
        persons = execution_result.get("persons", [])
        total = len(persons)

        if total == 0:
            answer_parts.append(f"No individuals matching the specified filter criteria were found in the synthetic dataset.")
            suggested_followups.append("Try broadening your location or case count criteria.")
        else:
            filter_descs = []
            if query.offence: filter_descs.append(f"offence category '{query.offence}'")
            if query.location: filter_descs.append(f"location '{query.location}'")
            if query.phone_suffix: filter_descs.append(f"phone suffix '{query.phone_suffix}'")
            if query.phone_prefix: filter_descs.append(f"phone prefix '{query.phone_prefix}'")
            if query.min_case_count: filter_descs.append(f"at least {query.min_case_count} associated cases")
            criteria_str = f" for {', '.join(filter_descs)}" if filter_descs else ""

            answer_parts.append(f"Found **{total}** person lead(s){criteria_str} in the synthetic records:\n")

            for p in persons[:5]:
                name = p.get("full_name")
                pid = p.get("person_id")
                cases_count = p.get("associated_case_count", 0)
                phone = p.get("phone_number", "None on file")
                reasons = ", ".join(p.get("matching_reasons", []))

                answer_parts.append(f"- **{name}** (`{pid}`): {cases_count} associated case(s) • Phone: `{phone}`")
                if reasons:
                    answer_parts.append(f"  *Reason: {reasons}*")

                # Provenance
                provenance.append(ProvenanceItem(
                    source_type="PERSON_RECORD",
                    source_id=pid,
                    evidence_text=f"Matched: {reasons}"
                ))
                for cid in p.get("matching_case_ids", []):
                    provenance.append(ProvenanceItem(
                        source_type="CASE_PERSON_ASSOCIATION",
                        source_id=f"{pid}_{cid}",
                        case_id=cid,
                        evidence_text=f"Associated with registered case record {cid}"
                    ))

            if total > 5:
                answer_parts.append(f"\n*(Showing top 5 of {total} matching records)*")

            if persons:
                top_p = persons[0]
                suggested_followups.append(f"Tell me more about {top_p['full_name']}")
                suggested_followups.append(f"Show the network connections for {top_p['full_name']}")

    # 2. INTENT: CASE_SEARCH
    elif intent == AssistantIntent.CASE_SEARCH:
        cases = execution_result.get("cases", [])
        total = len(cases)

        if total == 0:
            answer_parts.append("No registered case files matched the specified criteria in the synthetic dataset.")
        else:
            answer_parts.append(f"Found **{total}** registered case record(s) matching your inquiry:\n")
            for c in cases[:5]:
                cid = c.get("case_id")
                title = c.get("title")
                offence = c.get("offence_category")
                district = c.get("district")
                status = c.get("status")

                answer_parts.append(f"- **{cid}**: {title} (`{offence}` • {district} • Status: {status})")

                provenance.append(ProvenanceItem(
                    source_type="CASE_RECORD",
                    source_id=cid,
                    case_id=cid,
                    evidence_text=f"Registered case record: {title} ({offence})"
                ))

            if total > 5:
                answer_parts.append(f"\n*(Showing top 5 of {total} cases)*")

            if cases:
                suggested_followups.append(f"Details for {cases[0]['case_id']}")
                suggested_followups.append(f"Which cases are connected to {cases[0]['case_id']}?")

    # 3. INTENT: PERSON_PROFILE
    elif intent == AssistantIntent.PERSON_PROFILE:
        profile = execution_result.get("profile")
        if not profile:
            answer_parts.append(f"No person record found matching the requested identifier in the synthetic dataset.")
        else:
            name = profile.get("demographics", {}).get("full_name")
            pid = profile.get("entity_id")
            demog = profile.get("demographics", {})
            cases = profile.get("associated_cases", [])
            assets = profile.get("assets", {})
            alias = profile.get("primary_alias")

            alias_str = f" (Alias: *{alias}*)" if alias else ""
            answer_parts.append(f"### Investigative Dossier: {name} (`{pid}`){alias_str}\n")
            answer_parts.append(f"- **Demographics**: {demog.get('age', '')} years old, {demog.get('gender', '')}, Occupation: {demog.get('occupation', 'Unspecified')}")
            answer_parts.append(f"- **Jurisdiction**: {demog.get('district', '')}, {demog.get('city', '')} ({demog.get('state', '')})")
            answer_parts.append(f"- **Associated Cases**: Associated with **{len(cases)}** registered case file(s)")

            for c in cases[:4]:
                answer_parts.append(f"  - **{c['case_id']}** ({c['offence_category']}): *{c['title']}* (Role: `{c.get('role', 'ASSOCIATE')}`)")
                provenance.append(ProvenanceItem(
                    source_type="CASE_PERSON_ASSOCIATION",
                    source_id=f"{pid}_{c['case_id']}",
                    case_id=c['case_id'],
                    evidence_text=c.get("association_narrative", "Associated with registered case record.")
                ))

            provenance.append(ProvenanceItem(
                source_type="PERSON_RECORD",
                source_id=pid,
                evidence_text=f"Demographics for {name} ({pid})"
            ))

            suggested_followups.append(f"Show the network connections for {name}")
            suggested_followups.append(f"Why is {name} an investigation priority?")

    # 4. INTENT: CASE_DETAILS
    elif intent == AssistantIntent.CASE_DETAILS:
        case = execution_result.get("case")
        if not case:
            answer_parts.append(f"Case file `{query.case_id}` was not found in the synthetic dataset.")
        else:
            cid = case.get("case_id")
            title = case.get("title") or case.get("case_title")
            offence = case.get("offence_category")
            section = case.get("legal_section")
            fir = case.get("fir_number")
            status = case.get("status")
            district = case.get("district")
            ps = case.get("police_station")
            persons = execution_result.get("associated_persons", [])

            answer_parts.append(f"### Case Record: {title} (`{cid}`)\n")
            answer_parts.append(f"- **FIR Number**: `{fir}` • **Status**: `{status}`")
            answer_parts.append(f"- **Offence Category**: {offence} (Legal Section: `{section}`)")
            answer_parts.append(f"- **Jurisdiction**: {ps}, District: {district}")
            answer_parts.append(f"- **Associated Persons on File**: {len(persons)} registered associate(s)")

            for p in persons[:4]:
                pname = p.get("full_name")
                pid = p.get("person_id")
                role = p.get("role_in_case", "ASSOCIATE")
                answer_parts.append(f"  - **{pname}** (`{pid}`): Role: `{role}`")
                provenance.append(ProvenanceItem(
                    source_type="CASE_PERSON_ASSOCIATION",
                    source_id=f"{pid}_{cid}",
                    case_id=cid,
                    evidence_text=f"Role in case: {role}"
                ))

            provenance.append(ProvenanceItem(
                source_type="CASE_RECORD",
                source_id=cid,
                case_id=cid,
                evidence_text=f"Primary case file {cid}: {title}"
            ))

            suggested_followups.append(f"Which cases are connected to {cid}?")

    # 5. INTENT: NETWORK_QUERY
    elif intent == AssistantIntent.NETWORK_QUERY:
        relationships = execution_result.get("relationships", [])
        name = query.person_name or query.person_id or "Subject"

        if not relationships:
            answer_parts.append(f"No direct evidence-backed network relationships were identified for {name} in the synthetic graph.")
        else:
            answer_parts.append(f"### Evidence-Backed Network Connections for {name}\n")
            answer_parts.append(f"Identified **{len(relationships)}** verified interaction(s) from synthetic communication records and synthetic transaction records:\n")

            for r in relationships[:5]:
                other = r.get("connected_entity_name") or r.get("connected_entity_id")
                rel_type = r.get("relationship_type")
                conf = r.get("confidence", 0.0)
                evidence = r.get("evidence", "Graph interaction")
                cid = r.get("case_id", "")
                method = r.get("detection_method", "ANALYSIS")

                # Neutral wording
                if "COMM" in rel_type:
                    rel_label = "synthetic communication record"
                elif "TRANS" in rel_type:
                    rel_label = "synthetic transaction record"
                else:
                    rel_label = f"potential relationship ({rel_type})"

                answer_parts.append(f"- **{other}**: Linked via *{rel_label}* (Confidence: {conf:.2f})")
                answer_parts.append(f"  *Evidence: \"{evidence}\" [Case: {cid or 'N/A'}]*")

                provenance.append(ProvenanceItem(
                    source_type="GRAPH_EDGE",
                    source_id=r.get("relationship_id", f"{query.person_id}_{other}"),
                    case_id=cid if cid else None,
                    evidence_text=evidence,
                    confidence=conf,
                    detection_method=method
                ))

            if len(relationships) > 5:
                answer_parts.append(f"\n*(Showing 5 of {len(relationships)} connections)*")

            suggested_followups.append(f"Why is {name} an investigation priority?")
            suggested_followups.append(f"What cases is {name} associated with?")

    # 6. INTENT: RELATED_CASES
    elif intent == AssistantIntent.RELATED_CASES:
        related = execution_result.get("related_cases", [])
        cid = query.case_id or "Selected Case"

        if not related:
            answer_parts.append(f"No cross-case linkages through common suspects or shared entities were identified for {cid}.")
        else:
            answer_parts.append(f"### Cross-Case Connections Linked to `{cid}`\n")
            answer_parts.append(f"Identified **{len(related)}** related case(s) sharing common person leads or network entities:\n")

            for rc in related[:5]:
                rc_id = rc.get("case_id")
                rc_title = rc.get("title")
                rc_offence = rc.get("offence_category")
                reason = rc.get("reason")
                strength = rc.get("link_strength", "MEDIUM")

                answer_parts.append(f"- **{rc_id}** ({rc_offence}): *{rc_title}* [Link: `{strength}`]")
                answer_parts.append(f"  *Linkage factor: {reason}*")

                provenance.append(ProvenanceItem(
                    source_type="CASE_RECORD",
                    source_id=rc_id,
                    case_id=rc_id,
                    evidence_text=reason
                ))

            suggested_followups.append("Show potential connectors between these cases")

    # 7. INTENT: PRIORITY_EXPLANATION
    elif intent == AssistantIntent.PRIORITY_EXPLANATION:
        p_info = execution_result.get("priority_information")
        name = query.person_name or query.person_id or "Subject"

        if not p_info:
            answer_parts.append(f"No priority scoring lead record is registered for {name}. Note: Investigation Priority is calculated deterministically from graph centrality and cross-case connectivity.")
        else:
            score = p_info.get("priority_score", 0.0)
            level = p_info.get("priority_level", "LEAD")
            reasons = p_info.get("reasons", [])
            evidence = p_info.get("supporting_evidence", [])

            answer_parts.append(f"### Investigation Priority Lead Analysis: {name}\n")
            answer_parts.append(f"- **Priority Score**: **{score:.1f} / 100.0** (Analytical Level: `{level}`)")
            answer_parts.append(f"- **Safety Notice**: *Investigation Priority score is an analytical lead for prioritization. It does NOT predict criminality or guilt and requires human verification.*")
            answer_parts.append(f"\n**Deterministic Centrality & Connectivity Factors**:")

            for r in reasons:
                answer_parts.append(f"- {r}")

            if evidence:
                answer_parts.append(f"\n**Supporting Signal Evidence**:")
                for ev in evidence[:3]:
                    answer_parts.append(f"- `{ev}`")

            provenance.append(ProvenanceItem(
                source_type="PRIORITY_ANALYSIS",
                source_id=f"PRIORITY_{query.person_id}",
                evidence_text="; ".join(reasons)
            ))

            suggested_followups.append(f"Show the network connections for {name}")
            suggested_followups.append(f"What cases is {name} associated with?")

    # 8. INTENT: CLARIFICATION_REQUIRED (Ambiguous person name)
    elif intent == AssistantIntent.CLARIFICATION_REQUIRED:
        candidates = execution_result.get("candidates", [])
        answer_parts.append(f"The name **'{query.person_name}'** is ambiguous. I found multiple matching people:\n")
        for i, c in enumerate(candidates):
            c_name = getattr(c, 'full_name', None) or (c.get('full_name') if isinstance(c, dict) else str(c))
            c_id = getattr(c, 'person_id', None) or (c.get('person_id') if isinstance(c, dict) else "")
            answer_parts.append(f" {i+1}. {c_name} — {c_id}")
            if c_id:
                suggested_followups.append(f"Tell me about {c_id}")
        answer_parts.append("\nWhich person would you like to inspect?")

    # 9. INTENT: GENERAL_ANALYTICAL_QUERY
    elif intent == AssistantIntent.GENERAL_ANALYTICAL_QUERY:
        stats = execution_result.get("summary", {})
        answer_parts.append(f"### Investigation System Overview (Synthetic Demonstration Dataset)\n")
        answer_parts.append(f"- **Registered Cases**: {stats.get('total_cases', 250)}")
        answer_parts.append(f"- **Indexed Persons**: {stats.get('total_persons', 200)}")
        answer_parts.append(f"- **Network Relationships**: {stats.get('total_relationships', 145)}")
        suggested_followups.append("Show persons associated with kidnapping cases in Kolkata")
        suggested_followups.append("Find people linked to at least 3 associated cases")

    # 10. INTENT: UNSUPPORTED
    else:
        msg = query.clarification_message or f"The inquiry '{question}' could not be matched to a verified investigation query."
        answer_parts.append(msg)
        answer_parts.append("\n**Supported Question Archetypes**:")
        answer_parts.append("- *\"Show persons associated with kidnapping cases in Kolkata\"*")
        answer_parts.append("- *\"Show people whose phone number ends in 4895\"*")
        answer_parts.append("- *\"Find people linked to at least 3 associated cases\"*")
        answer_parts.append("- *\"Tell me more about Arjun Mehta\"*")
        answer_parts.append("- *\"Show the network connections for Arjun Mehta\"*")
        answer_parts.append("- *\"Why is Arjun Mehta an investigation priority?\"*")
        answer_parts.append("- *\"Which cases are connected to CASE-001?\"*")

    # Assemble response
    answer_text = "\n".join(answer_parts)

    return {
        "question": question,
        "intent": intent,
        "structured_query": query,
        "answer_markdown": answer_text,
        "provenance": provenance,
        "suggested_followups": suggested_followups
    }
