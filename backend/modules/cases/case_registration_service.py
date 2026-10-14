"""
case_registration_service.py
============================
Service coordinating the Register New Case + Create / Link Person workflow.
- Strict input validation
- Dynamic ID allocation
- Advisory entity-resolution duplicate protection
- Isolated runtime persistence
- Real-time NetworkX graph update with INVOLVED_IN edges
- Graph analytics and priority recomputation
- In-memory search & profile cache invalidation
- Strict family isolation and non-accusatory terminology
"""

import datetime
from typing import Dict, List, Any, Optional
import networkx as nx

from modules.persistence.runtime_store import (
    append_runtime_record,
    get_all_records,
    check_fir_exists,
    get_next_case_id,
    get_next_person_id,
    get_next_cp_id,
    get_next_phone_id,
    get_next_vehicle_id,
    get_next_bank_account_id,
)
from modules.entity_resolution.normalization import normalize_entity
from modules.entity_resolution.resolver import calculate_string_similarity
from modules.graph.graph_builder import add_entity, add_relationship
from modules.analytics.graph_analytics import analyze_graph
from modules.priority.priority_scorer import calculate_priority_scores
from modules.graph.dataset_integration import get_case_inventory

from modules.cases.case_service import clear_cache as clear_cases_cache
from modules.entities.person_service import clear_cache as clear_persons_cache
from modules.search.search_service import clear_cache as clear_search_cache


ALLOWED_OFFENCE_CATEGORIES = {
    "Kidnapping", "Extortion", "Cybercrime", "Financial Fraud", "Theft",
    "Robbery", "Burglary", "Assault", "Criminal Intimidation", "Property Offence",
    "Murder", "Attempted Murder", "Molestation", "Forgery", "Fraud",
    "Narcotics", "Smuggling", "Other"
}

ALLOWED_STATUSES = {"OPEN", "UNDER INVESTIGATION", "CHARGESHEETED", "CLOSED"}

ALLOWED_ROLES = {
    "SUBJECT", "PERSON_OF_INTEREST", "WITNESS", "VICTIM",
    "COMPLAINANT", "INFORMANT", "OTHER"
}


class ValidationError(Exception):
    """Raised when validation fails for case or person registration."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.message = message
        self.errors = errors or [message]
        super().__init__(f"{message}: {'; '.join(self.errors)}")


def validate_case_payload(case_data: Dict[str, Any]) -> None:
    """Validates case fields, required types, and formats."""
    errors = []
    
    title = (case_data.get("title") or case_data.get("case_title") or "").strip()
    if not title:
        errors.append("Case title is required.")
    elif len(title) < 3:
        errors.append("Case title must be at least 3 characters.")
        
    offence = (case_data.get("offence_category") or "").strip()
    if not offence:
        errors.append("Offence category is required.")
    elif offence not in ALLOWED_OFFENCE_CATEGORIES:
        # Allow case-insensitive match
        match = next((c for c in ALLOWED_OFFENCE_CATEGORIES if c.lower() == offence.lower()), None)
        if match:
            case_data["offence_category"] = match
        else:
            errors.append(f"Invalid offence category '{offence}'. Allowed: {', '.join(sorted(ALLOWED_OFFENCE_CATEGORIES))}")

    status = (case_data.get("status") or "OPEN").strip().upper()
    if status not in ALLOWED_STATUSES:
        errors.append(f"Invalid status '{status}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")
    case_data["status"] = status

    date_val = (case_data.get("incident_date") or case_data.get("date_opened") or "").strip()
    if not date_val:
        errors.append("Incident date (or date opened) is required.")
    else:
        try:
            datetime.date.fromisoformat(date_val[:10])
        except ValueError:
            errors.append("Incident date must be in YYYY-MM-DD format.")

    location = (case_data.get("location") or case_data.get("locality") or "").strip()
    if not location:
        errors.append("Incident location is required.")

    district = (case_data.get("district") or "").strip()
    if not district:
        errors.append("District is required.")

    police_station = (case_data.get("police_station") or "").strip()
    if not police_station:
        errors.append("Police station is required.")

    description = (case_data.get("description") or "").strip()
    if not description:
        errors.append("Case narrative description is required.")

    fir = (case_data.get("fir_number") or "").strip()
    if fir:
        if check_fir_exists(fir):
            errors.append(f"FIR number '{fir}' already exists in registered cases.")

    if errors:
        raise ValidationError("Case validation failed", errors)


def validate_new_person_payload(person_data: Dict[str, Any]) -> None:
    """Validates person fields for new person creation."""
    errors = []
    name = (person_data.get("full_name") or "").strip()
    if not name:
        errors.append("Person full name is required.")
    elif len(name) < 2:
        errors.append("Person full name must be at least 2 characters.")

    dob = (person_data.get("date_of_birth") or "").strip()
    if dob:
        try:
            datetime.date.fromisoformat(dob[:10])
        except ValueError:
            errors.append("Date of birth must be in YYYY-MM-DD format.")

    phone = (person_data.get("phone") or person_data.get("phone_number") or "").strip()
    if phone:
        norm_phone = normalize_entity("PHONE", phone)["canonical_value"]
        if len(norm_phone) < 7 or len(norm_phone) > 15:
            errors.append("Phone number format is invalid.")

    email = (person_data.get("email") or "").strip()
    if email and "@" not in email:
        errors.append("Email format is invalid.")

    if errors:
        raise ValidationError("Person validation failed", errors)


def check_person_duplicate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advisory Entity Resolution duplicate & possible-match checker.
    Never automatically merges people.
    Returns potential matches for human investigator review.
    """
    raw_name = (candidate.get("full_name") or "").strip()
    raw_phone = (candidate.get("phone") or candidate.get("phone_number") or "").strip()
    raw_district = (candidate.get("district") or "").strip().lower()

    if not raw_name:
        return {"has_matches": False, "matches": []}

    norm_name = normalize_entity("PERSON", raw_name)["canonical_value"].lower()
    norm_phone = normalize_entity("PHONE", raw_phone)["canonical_value"] if raw_phone else ""

    existing_persons = get_all_records("persons.csv")
    existing_phones = {p["phone_id"]: p.get("phone_number", "") for p in get_all_records("phones.csv")}

    matches = []

    for p in existing_persons:
        pid = p.get("person_id", "")
        p_name = p.get("full_name", "")
        p_norm = normalize_entity("PERSON", p_name)["canonical_value"].lower()
        p_dist = (p.get("district") or "").strip().lower()

        # Check phone
        p_phone_id = p.get("phone_id", "")
        p_phone_raw = existing_phones.get(p_phone_id, "")
        p_norm_phone = normalize_entity("PHONE", p_phone_raw)["canonical_value"] if p_phone_raw else ""

        # 1. Exact Phone Match
        if norm_phone and p_norm_phone and norm_phone == p_norm_phone:
            matches.append({
                "person_id": pid,
                "full_name": p_name,
                "district": p.get("district", ""),
                "occupation": p.get("occupation", ""),
                "phone_number": p_phone_raw,
                "score": 1.0,
                "match_level": "DUPLICATE",
                "match_type": "EXACT_PHONE",
                "reason": f"Exact phone number match ({p_phone_raw}) with registered record {pid}"
            })
            continue

        # 2. Exact Name + Same District Match
        if norm_name == p_norm:
            if raw_district and p_dist and raw_district == p_dist:
                matches.append({
                    "person_id": pid,
                    "full_name": p_name,
                    "district": p.get("district", ""),
                    "occupation": p.get("occupation", ""),
                    "phone_number": p_phone_raw,
                    "score": 0.95,
                    "match_level": "DUPLICATE",
                    "match_type": "EXACT_NAME_DISTRICT",
                    "reason": f"Exact name and district ({p.get('district')}) match with registered record {pid}"
                })
                continue
            else:
                matches.append({
                    "person_id": pid,
                    "full_name": p_name,
                    "district": p.get("district", ""),
                    "occupation": p.get("occupation", ""),
                    "phone_number": p_phone_raw,
                    "score": 0.88,
                    "match_level": "POSSIBLE_MATCH",
                    "match_type": "EXACT_NAME",
                    "reason": f"Identical name match with registered record {pid}"
                })
                continue

        # 3. High String / Initial Similarity (e.g. A. Mehta vs Arjun Mehta)
        sim = calculate_string_similarity(norm_name, p_norm)
        parts_cand = norm_name.split()
        parts_p = p_norm.split()

        initial_match = False
        if len(parts_cand) >= 2 and len(parts_p) >= 2:
            # Same surname and matching first initial
            if parts_cand[-1] == parts_p[-1]:
                if parts_cand[0][0] == parts_p[0][0]:
                    initial_match = True

        if sim >= 0.82 or initial_match:
            score = max(sim, 0.78 if initial_match else 0.70)
            matches.append({
                "person_id": pid,
                "full_name": p_name,
                "district": p.get("district", ""),
                "occupation": p.get("occupation", ""),
                "phone_number": p_phone_raw,
                "score": round(score, 2),
                "match_level": "POSSIBLE_MATCH",
                "match_type": "NAME_SIMILARITY",
                "reason": f"High name similarity ({round(score*100)}%) with registered record {pid}"
            })

    # Sort matches by score descending
    matches.sort(key=lambda m: m["score"], reverse=True)
    return {
        "has_matches": len(matches) > 0,
        "matches": matches[:5]
    }


def search_persons_for_linking(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches registered persons by name, ID, phone, or alias for linking to a new case.
    """
    if not query or not query.strip():
        return []

    q = query.strip().lower()
    q_norm = normalize_entity("PERSON", q)["canonical_value"].lower()

    persons = get_all_records("persons.csv")
    case_persons = get_all_records("case_persons.csv")
    phones = {p["phone_id"]: p.get("phone_number", "") for p in get_all_records("phones.csv")}
    aliases = get_all_records("aliases.csv")

    # Count cases per person
    case_counts: Dict[str, int] = {}
    for cp in case_persons:
        pid = cp.get("person_id")
        if pid:
            case_counts[pid] = case_counts.get(pid, 0) + 1

    # Aliases by person
    aliases_by_person: Dict[str, List[str]] = {}
    for a in aliases:
        pid = a.get("person_id")
        name = a.get("alias_name")
        if pid and name:
            aliases_by_person.setdefault(pid, []).append(name)

    results = []
    for p in persons:
        pid = p.get("person_id", "")
        name = p.get("full_name", "")
        name_norm = normalize_entity("PERSON", name)["canonical_value"].lower()
        p_phone = phones.get(p.get("phone_id", ""), "")
        p_aliases = aliases_by_person.get(pid, [])

        matched = False
        match_reason = ""

        if q in pid.lower():
            matched = True
            match_reason = "Person ID"
        elif q in name_norm or q_norm in name_norm:
            matched = True
            match_reason = "Name Match"
        elif q in p_phone.lower():
            matched = True
            match_reason = "Phone Match"
        else:
            for al in p_aliases:
                if q in al.lower():
                    matched = True
                    match_reason = f"Alias ({al})"
                    break

        if matched:
            results.append({
                "person_id": pid,
                "full_name": name,
                "district": p.get("district", ""),
                "occupation": p.get("occupation", ""),
                "phone_number": p_phone,
                "associated_case_count": case_counts.get(pid, 0),
                "aliases": p_aliases,
                "match_reason": match_reason
            })
            if len(results) >= limit:
                break

    return results


def register_case_transaction(
    payload: Dict[str, Any],
    app_state: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Transactional coordinator for registering a new case record and its associations.
    - Validates all records first
    - Writes to isolated runtime files
    - Updates live NetworkX graph with INVOLVED_IN edges
    - Re-evaluates graph analytics and priority
    - Clears in-memory caches
    """
    case_input = payload.get("case") or {}
    associated_persons = payload.get("associated_persons") or []
    optional_entities = payload.get("optional_entities") or []

    # 1. Validate case data
    validate_case_payload(case_input)

    # 2. Validate associated people
    if not associated_persons:
        raise ValidationError("At least one associated person is required to register a case.")

    validated_persons = []
    seen_person_ids = set()

    for idx, item in enumerate(associated_persons):
        p_type = (item.get("person_type") or "EXISTING").upper()
        role = (item.get("role") or "SUBJECT").strip().upper()
        if role not in ALLOWED_ROLES:
            raise ValidationError(f"Invalid role '{role}' for person #{idx+1}. Allowed: {', '.join(sorted(ALLOWED_ROLES))}")

        if p_type == "EXISTING":
            pid = (item.get("person_id") or "").strip()
            if not pid:
                raise ValidationError(f"Person ID is required for existing person #{idx+1}.")
            # Check existence
            existing = next((p for p in get_all_records("persons.csv") if p.get("person_id") == pid), None)
            if not existing:
                raise ValidationError(f"Existing person with ID '{pid}' was not found.")
            if pid in seen_person_ids:
                raise ValidationError(f"Duplicate association: person '{pid}' is included multiple times.")
            seen_person_ids.add(pid)
            validated_persons.append({
                "person_type": "EXISTING",
                "person_id": pid,
                "role": role,
                "full_name": existing.get("full_name", pid),
                "details": existing
            })

        elif p_type == "NEW":
            new_data = item.get("new_person_data") or {}
            validate_new_person_payload(new_data)
            validated_persons.append({
                "person_type": "NEW",
                "person_id": None, # Will be allocated dynamically
                "role": role,
                "full_name": new_data.get("full_name", "").strip(),
                "details": new_data
            })
        else:
            raise ValidationError(f"Unknown person_type '{p_type}'. Must be EXISTING or NEW.")

    # 3. Dynamic ID Allocations
    case_id = get_next_case_id()
    now_iso = datetime.datetime.now().isoformat()
    created_by = "prototype-user"

    title = (case_input.get("title") or case_input.get("case_title") or "").strip()
    fir_num = (case_input.get("fir_number") or "").strip()
    offence_category = case_input.get("offence_category")
    legal_section = (case_input.get("legal_section") or "Not Specified").strip()
    date_opened = case_input.get("incident_date") or case_input.get("date_opened")
    status = case_input.get("status") or "OPEN"
    police_station = case_input.get("police_station")
    district = case_input.get("district")
    state = case_input.get("state") or "Chhattisgarh"
    location_str = case_input.get("location") or district
    description = case_input.get("description")

    # 4. Persistence: Case Record
    case_record = {
        "case_id": case_id,
        "case_title": title,
        "offence_category": offence_category,
        "legal_section": legal_section,
        "fir_number": fir_num,
        "date_opened": date_opened,
        "description": description,
        "status": status,
        "police_station": police_station,
        "district": district,
        "state": state,
        "location_id": "",
        "created_at": now_iso,
        "created_by": created_by
    }
    append_runtime_record("cases.csv", case_record)

    # 5. Persistence: People & Case-Person Links
    created_associations = []

    for vp in validated_persons:
        if vp["person_type"] == "NEW":
            pid = get_next_person_id()
            vp["person_id"] = pid
            new_p = vp["details"]

            # Handle optional phone
            raw_phone = (new_p.get("phone") or new_p.get("phone_number") or "").strip()
            phone_id = ""
            if raw_phone:
                phone_id = get_next_phone_id()
                phone_record = {
                    "phone_id": phone_id,
                    "phone_number": raw_phone,
                    "phone_type": "Mobile",
                    "created_at": now_iso,
                    "created_by": created_by
                }
                append_runtime_record("phones.csv", phone_record)

            parts = new_p.get("full_name", "").strip().split(maxsplit=1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""

            person_record = {
                "person_id": pid,
                "full_name": new_p.get("full_name", "").strip(),
                "first_name": first_name,
                "last_name": last_name,
                "gender": new_p.get("gender") or "Unknown",
                "date_of_birth": new_p.get("date_of_birth") or "",
                "age": str(new_p.get("age") or ""),
                "occupation": new_p.get("occupation") or "Not Specified",
                "education": new_p.get("education") or "Not Specified",
                "address": new_p.get("address") or "",
                "locality": new_p.get("locality") or "",
                "city": new_p.get("city") or location_str,
                "district": new_p.get("district") or district,
                "state": new_p.get("state") or state,
                "pin_code": str(new_p.get("pin_code") or ""),
                "phone_id": phone_id,
                "phone_id_2": "",
                "bank_account_id": "",
                "bank_account_id_2": "",
                "vehicle_id": "",
                "vehicle_id_2": "",
                "location_id": "",
                "organization_id": "",
                "email": new_p.get("email") or "",
                "created_at": now_iso,
                "created_by": created_by
            }
            append_runtime_record("persons.csv", person_record)
        else:
            pid = vp["person_id"]

        # Link Person to Case
        cp_id = get_next_cp_id()
        cp_record = {
            "cp_id": cp_id,
            "case_id": case_id,
            "person_id": pid,
            "association": f"Associated with registered case as {vp['role']}. Requires human verification.",
            "role": vp["role"],
            "source": "STRUCTURED_METADATA",
            "created_at": now_iso,
            "created_by": created_by
        }
        append_runtime_record("case_persons.csv", cp_record)

        created_associations.append({
            "cp_id": cp_id,
            "case_id": case_id,
            "person_id": pid,
            "person_name": vp["full_name"],
            "role": vp["role"],
            "is_new": vp["person_type"] == "NEW"
        })

    # 6. Persistence: Optional Entities (Phones, Vehicles, Bank Accounts)
    for opt in optional_entities:
        ent_type = (opt.get("entity_type") or "").upper()
        val = (opt.get("value") or "").strip()
        if not ent_type or not val:
            continue

        if ent_type == "PHONE":
            ph_id = get_next_phone_id()
            append_runtime_record("phones.csv", {
                "phone_id": ph_id,
                "phone_number": val,
                "phone_type": "Mobile",
                "created_at": now_iso,
                "created_by": created_by
            })
        elif ent_type == "VEHICLE":
            v_id = get_next_vehicle_id()
            append_runtime_record("vehicles.csv", {
                "vehicle_id": v_id,
                "registration_number": val,
                "vehicle_type": opt.get("vehicle_type", "Four Wheeler"),
                "created_at": now_iso,
                "created_by": created_by
            })
        elif ent_type == "BANK_ACCOUNT":
            b_id = get_next_bank_account_id()
            append_runtime_record("bank_accounts.csv", {
                "bank_account_id": b_id,
                "account_number": val,
                "bank_name": opt.get("bank_name", "State Bank"),
                "created_at": now_iso,
                "created_by": created_by
            })

    # 7. Real-Time Graph & State Update
    nodes_added = 0
    edges_added = 0

    if app_state and hasattr(app_state, "graph"):
        G = app_state.graph
        
        # Add Case node
        add_entity(G, {
            "type": "CASE_ID",
            "value": case_id,
            "evidence": title,
            "source": "STRUCTURED_METADATA",
            "confidence": 1.0
        })
        nodes_added += 1

        # Add associated Persons and directed INVOLVED_IN edges
        for assoc in created_associations:
            pid = assoc["person_id"]
            pname = assoc["person_name"]
            role = assoc["role"]

            add_entity(G, {
                "type": "PERSON",
                "value": pid,
                "evidence": pname,
                "source": "STRUCTURED_METADATA",
                "confidence": 1.0
            })
            nodes_added += 1

            # Strict graph semantics: Case-Person association only
            # No person-person edge! No family edge!
            add_relationship(G, {
                "source": case_id,
                "target": pid,
                "relationship_type": "INVOLVED_IN",
                "evidence": f"Case association as {role}",
                "case_id": case_id,
                "detection_method": "STRUCTURED_METADATA",
                "confidence": 1.0
            })
            edges_added += 1

        # Recalculate graph analytics and priority scores
        try:
            app_state.analytics = analyze_graph(G)
            app_state.priority = calculate_priority_scores(G, app_state.analytics)
        except Exception:
            pass

        # Refresh case inventory
        try:
            app_state.cases = get_case_inventory()
        except Exception:
            pass

    # 8. Clear in-memory caches across all services
    clear_cases_cache()
    clear_persons_cache()
    clear_search_cache()

    return {
        "success": True,
        "message": "Investigation record created successfully.",
        "case_id": case_id,
        "case_title": title,
        "created_case": case_record,
        "associated_persons": created_associations,
        "graph_summary": {
            "nodes_added": nodes_added,
            "edges_added": edges_added
        }
    }
