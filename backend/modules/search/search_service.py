"""
search_service.py
=================
In-memory indexed deterministic search service for the current synthetic MVP dataset.

Provides composable, multi-criteria filtering across:
- Persons: Name (full/partial), aliases, person ID, phone (exact/prefix/suffix), vehicle,
  organization, location, district, occupation, associated case offence, and case counts.
- Cases: Case ID, FIR, title, offence category, legal section, police station, district,
  status, year, date range, location.

Strict Safety Separation:
- Family relationships are strictly civilian and completely excluded from investigative filtering.
- ground_truth.csv is strictly excluded from user-facing search results.
- No LLM or generative hallucination: all results and reasons are 100% deterministic from source CSV records.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from data.validate_dataset import load_csv
from modules.entity_resolution.normalization import normalize_entity

# Cache for the in-memory indexed dataset
_SEARCH_INDEX: Optional[Dict[str, Any]] = None

def clear_cache():
    """Clears in-memory search index cache on runtime mutation."""
    global _SEARCH_INDEX
    _SEARCH_INDEX = None

def _get_search_index() -> Dict[str, Any]:
    global _SEARCH_INDEX
    if _SEARCH_INDEX is not None:
        return _SEARCH_INDEX

    raw_persons = load_csv("persons.csv") or []
    raw_cases = load_csv("cases.csv") or []
    raw_case_persons = load_csv("case_persons.csv") or []
    raw_aliases = load_csv("aliases.csv") or []
    raw_phones = load_csv("phones.csv") or []
    raw_vehicles = load_csv("vehicles.csv") or []
    raw_orgs = load_csv("organizations.csv") or []
    raw_locations = load_csv("locations.csv") or []

    # Fast dictionaries
    cases_by_id = {c["case_id"]: c for c in raw_cases}
    persons_by_id = {p["person_id"]: p for p in raw_persons}
    phones_by_id = {p["phone_id"]: p for p in raw_phones}
    vehicles_by_id = {v["vehicle_id"]: v for v in raw_vehicles}
    orgs_by_id = {o["organization_id"]: o for o in raw_orgs}
    locations_by_id = {l["location_id"]: l for l in raw_locations}

    # Aliases by person
    aliases_by_person = defaultdict(list)
    for a in raw_aliases:
        aliases_by_person[a["person_id"]].append(a.get("alias_name", ""))

    # Case-Person associations
    case_ids_by_person = defaultdict(list)
    persons_by_case = defaultdict(list)
    for cp in raw_case_persons:
        pid = cp.get("person_id")
        cid = cp.get("case_id")
        if pid and cid:
            case_ids_by_person[pid].append(cid)
            persons_by_case[cid].append(pid)

    # Pre-index persons with normalized phone and linked case metadata
    indexed_persons = []
    for p in raw_persons:
        pid = p["person_id"]
        ph_obj = phones_by_id.get(p.get("phone_id"), {})
        raw_phone = ph_obj.get("phone_number", "")
        norm_phone = normalize_entity("PHONE", raw_phone)["canonical_value"] if raw_phone else ""
        
        # Also check second phone if present
        ph_obj_2 = phones_by_id.get(p.get("phone_id_2"), {})
        raw_phone_2 = ph_obj_2.get("phone_number", "")
        norm_phone_2 = normalize_entity("PHONE", raw_phone_2)["canonical_value"] if raw_phone_2 else ""

        # Linked cases
        cids = case_ids_by_person.get(pid, [])
        linked_case_objects = [cases_by_id[cid] for cid in cids if cid in cases_by_id]
        offence_categories = {c.get("offence_category", "") for c in linked_case_objects}
        case_districts = {c.get("district", "") for c in linked_case_objects}

        veh_obj = vehicles_by_id.get(p.get("vehicle_id"), {})
        veh_reg = veh_obj.get("registration_number", "")
        veh_model = veh_obj.get("model", "")

        org_obj = orgs_by_id.get(p.get("organization_id"), {})
        org_name = org_obj.get("organization_name", "")

        loc_obj = locations_by_id.get(p.get("location_id"), {})
        loc_name = loc_obj.get("location_name", "")

        indexed_persons.append({
            "person_id": pid,
            "full_name": p.get("full_name", ""),
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "aliases": aliases_by_person.get(pid, []),
            "gender": p.get("gender", "Unknown"),
            "age": p.get("age", ""),
            "occupation": p.get("occupation", ""),
            "phone_number": raw_phone,
            "normalized_phone": norm_phone,
            "phone_number_2": raw_phone_2,
            "normalized_phone_2": norm_phone_2,
            "vehicle_reg": veh_reg,
            "vehicle_model": veh_model,
            "organization_name": org_name,
            "organization_id": p.get("organization_id", ""),
            "location_name": loc_name,
            "location_id": p.get("location_id", ""),
            "address": p.get("address", ""),
            "locality": p.get("locality", ""),
            "city": p.get("city", ""),
            "district": p.get("district", ""),
            "state": p.get("state", "Chhattisgarh"),
            "threat_level": p.get("threat_level", "STANDARD"),
            "associated_case_ids": cids,
            "associated_case_count": len(cids),
            "linked_case_objects": linked_case_objects,
            "offence_categories": offence_categories,
            "case_districts": case_districts
        })

    # Pre-index cases
    indexed_cases = []
    for c in raw_cases:
        cid = c["case_id"]
        date_opened = c.get("date_opened", "")
        year = date_opened[:4] if len(date_opened) >= 4 else ""
        loc_obj = locations_by_id.get(c.get("location_id"), {})
        loc_name = loc_obj.get("location_name", "")
        loc_city = loc_obj.get("city", "")
        loc_locality = loc_obj.get("locality", "")
        
        indexed_cases.append({
            "case_id": cid,
            "title": c.get("case_title") or c.get("title") or f"Case {cid}",
            "fir_number": c.get("fir_number", ""),
            "offence_category": c.get("offence_category", ""),
            "legal_section": c.get("legal_section", ""),
            "date_opened": date_opened,
            "year": year,
            "status": c.get("status", "OPEN"),
            "police_station": c.get("police_station", ""),
            "district": c.get("district", ""),
            "state": c.get("state", ""),
            "description": c.get("description", ""),
            "location_name": loc_name,
            "city": loc_city,
            "locality": loc_locality,
            "associated_person_ids": persons_by_case.get(cid, []),
            "associated_persons_count": len(persons_by_case.get(cid, []))
        })

    # Collect metadata options for frontend dropdowns
    metadata = {
        "offence_categories": sorted(list({c["offence_category"] for c in indexed_cases if c["offence_category"]})),
        "districts": sorted(list({c["district"] for c in indexed_cases if c["district"]})),
        "statuses": sorted(list({c["status"] for c in indexed_cases if c["status"]})),
        "years": sorted(list({c["year"] for c in indexed_cases if c["year"]}), reverse=True)
    }

    _SEARCH_INDEX = {
        "persons": indexed_persons,
        "cases": indexed_cases,
        "cases_by_id": cases_by_id,
        "metadata": metadata
    }
    return _SEARCH_INDEX


def get_search_metadata() -> Dict[str, Any]:
    """Returns available filter options for dropdowns."""
    idx = _get_search_index()
    return idx["metadata"]


def _match_phone(p: Dict[str, Any], phone_query: str, match_type: str = "contains") -> bool:
    """
    Normalizes query and compares against canonical phone numbers.
    match_type in ("contains", "prefix", "suffix", "exact")
    """
    if not phone_query:
        return False
    norm_q = normalize_entity("PHONE", phone_query)["canonical_value"]
    if not norm_q:
        # Fallback to pure digit extraction if normalize_entity returned empty
        norm_q = "".join(ch for ch in phone_query if ch.isdigit())
    if not norm_q:
        return False

    target_numbers = [p["normalized_phone"], p["normalized_phone_2"]]
    for num in target_numbers:
        if not num:
            continue
        if match_type == "exact" and num == norm_q:
            return True
        elif match_type == "prefix" and num.startswith(norm_q):
            return True
        elif match_type == "suffix" and num.endswith(norm_q):
            return True
        elif match_type == "contains" and norm_q in num:
            return True
    return False


def advanced_search(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes in-memory indexed deterministic search across persons and cases.
    Evaluates independent filters deterministically and produces traceable reasons.
    """
    index = _get_search_index()
    mode = (request.get("mode") or "ALL").upper().strip()
    general_query = (request.get("query") or "").lower().strip()

    limit = request.get("limit") or 100
    try:
        limit = max(1, min(int(limit), 250))
    except (ValueError, TypeError):
        limit = 100

    # Specific person filters
    name_q = (request.get("name") or "").lower().strip()
    alias_q = (request.get("alias") or "").lower().strip()
    person_id_q = (request.get("person_id") or "").lower().strip()
    phone_q = (request.get("phone") or "").strip()
    phone_prefix_q = (request.get("phone_prefix") or "").strip()
    phone_suffix_q = (request.get("phone_suffix") or "").strip()
    vehicle_q = (request.get("vehicle") or "").lower().strip()
    org_q = (request.get("organization") or "").lower().strip()
    occ_q = (request.get("occupation") or "").lower().strip()
    
    min_case_count = request.get("min_case_count")
    max_case_count = request.get("max_case_count")
    exact_case_count = request.get("exact_case_count")

    # Specific case filters
    case_id_q = (request.get("case_id") or "").lower().strip()
    fir_q = (request.get("fir_number") or "").lower().strip()
    offence_q = (request.get("offence") or "").lower().strip()
    legal_section_q = (request.get("legal_section") or "").lower().strip()
    police_station_q = (request.get("police_station") or "").lower().strip()
    status_q = (request.get("status") or "").lower().strip()
    year_q = (request.get("year") or "").strip()

    # Shared filters (applicable to both person and case)
    location_q = (request.get("location") or "").lower().strip()
    district_q = (request.get("district") or "").lower().strip()

    matched_persons = []
    matched_cases = []

    # 1. EVALUATE PERSON SEARCH (if mode in ("ALL", "PERSON"))
    if mode in ("ALL", "PERSON"):
        for p in index["persons"]:
            reasons = []
            matching_case_ids = []

            # 1. General query
            if general_query:
                g_match = False
                if general_query in p["person_id"].lower():
                    reasons.append(f"Person ID matched '{general_query}'")
                    g_match = True
                elif general_query in p["full_name"].lower():
                    reasons.append(f"Name matched query '{general_query}'")
                    g_match = True
                elif any(general_query in a.lower() for a in p["aliases"]):
                    matched_alias = next(a for a in p["aliases"] if general_query in a.lower())
                    reasons.append(f"Alias matched '{matched_alias}'")
                    g_match = True
                elif general_query in p["district"].lower() or general_query in p["city"].lower():
                    reasons.append(f"Location matched '{general_query}'")
                    g_match = True
                elif general_query in p["occupation"].lower():
                    reasons.append(f"Occupation matched '{general_query}'")
                    g_match = True
                elif _match_phone(p, general_query, "contains"):
                    reasons.append(f"Phone matched '{general_query}'")
                    g_match = True
                
                if not g_match:
                    continue

            # 2. Specific name filter
            if name_q:
                if name_q in p["full_name"].lower() or name_q in p["first_name"].lower() or name_q in p["last_name"].lower():
                    reasons.append(f"Matched name filter: {p['full_name']}")
                else:
                    continue

            # 3. Specific alias filter
            if alias_q:
                if any(alias_q in a.lower() for a in p["aliases"]):
                    matched_alias = next(a for a in p["aliases"] if alias_q in a.lower())
                    reasons.append(f"Matched alias filter: '{matched_alias}'")
                else:
                    continue

            # 4. Specific person ID filter
            if person_id_q:
                if person_id_q in p["person_id"].lower():
                    reasons.append(f"Matched Person ID: {p['person_id']}")
                else:
                    continue

            # 5. Phone filters (Prefix / Suffix / Contains)
            if phone_prefix_q:
                if _match_phone(p, phone_prefix_q, "prefix"):
                    reasons.append(f"Matched phone prefix: {phone_prefix_q}")
                else:
                    continue

            if phone_suffix_q:
                if _match_phone(p, phone_suffix_q, "suffix"):
                    reasons.append(f"Matched phone suffix: {phone_suffix_q}")
                else:
                    continue

            if phone_q:
                if _match_phone(p, phone_q, "contains"):
                    reasons.append(f"Matched phone: {phone_q}")
                else:
                    continue

            # 6. Vehicle filter
            if vehicle_q:
                if vehicle_q in p["vehicle_reg"].lower() or vehicle_q in p["vehicle_model"].lower():
                    reasons.append(f"Matched vehicle registration/model: {p['vehicle_reg']}")
                else:
                    continue

            # 7. Organization filter
            if org_q:
                if org_q in p["organization_name"].lower() or org_q in p["organization_id"].lower():
                    reasons.append(f"Matched organization: {p['organization_name']}")
                else:
                    continue

            # 8. Occupation filter
            if occ_q:
                if occ_q in p["occupation"].lower():
                    reasons.append(f"Matched occupation: {p['occupation']}")
                else:
                    continue

            # 9. Location & District filters (Person residence or linked case location)
            if location_q:
                loc_match = (
                    location_q in p["city"].lower() or
                    location_q in p["district"].lower() or
                    location_q in p["locality"].lower() or
                    location_q in p["location_name"].lower() or
                    location_q in p["address"].lower()
                )
                if loc_match:
                    reasons.append(f"Matched person location: {p['city'] or p['district']}")
                else:
                    # Also check if any associated case is in this location
                    case_loc_matches = [
                        c["case_id"] for c in p["linked_case_objects"]
                        if location_q in c.get("district", "").lower() or location_q in c.get("location_name", "").lower()
                    ]
                    if case_loc_matches:
                        matching_case_ids.extend(case_loc_matches)
                        reasons.append(f"Associated with case(s) in location '{location_q}': {', '.join(case_loc_matches)}")
                    else:
                        continue

            if district_q:
                if district_q in p["district"].lower():
                    reasons.append(f"Matched district: {p['district']}")
                elif any(district_q in cd.lower() for cd in p["case_districts"]):
                    matching_cids = [c["case_id"] for c in p["linked_case_objects"] if district_q in c.get("district", "").lower()]
                    matching_case_ids.extend(matching_cids)
                    reasons.append(f"Associated with case(s) in district '{district_q}': {', '.join(matching_cids)}")
                else:
                    continue

            # 10. Associated Offence filter (cross-record lookup from cases)
            if offence_q:
                offence_matches = [
                    c["case_id"] for c in p["linked_case_objects"]
                    if offence_q in c.get("offence_category", "").lower()
                ]
                if offence_matches:
                    matching_case_ids.extend(offence_matches)
                    reasons.append(f"Associated with cases categorized as '{offence_q.title()}': {', '.join(offence_matches)}")
                else:
                    continue

            # 11. Case Count filters (actual case_persons.csv associations)
            case_count = p["associated_case_count"]
            if min_case_count is not None:
                try:
                    min_val = int(min_case_count)
                    if case_count < min_val:
                        continue
                    reasons.append(f"Matched minimum case count requirement (>= {min_val}, count: {case_count})")
                except (ValueError, TypeError):
                    pass

            if max_case_count is not None:
                try:
                    max_val = int(max_case_count)
                    if case_count > max_val:
                        continue
                    reasons.append(f"Matched maximum case count requirement (<= {max_val}, count: {case_count})")
                except (ValueError, TypeError):
                    pass

            if exact_case_count is not None:
                try:
                    exact_val = int(exact_case_count)
                    if case_count != exact_val:
                        continue
                    reasons.append(f"Matched exact case count requirement (== {exact_val})")
                except (ValueError, TypeError):
                    pass

            # If no specific filters were passed and no general query, include with default reason
            if not reasons:
                reasons.append("Included in person directory index")

            # Deduplicate matching case IDs
            unique_matching_cases = sorted(list(set(matching_case_ids)))

            matched_persons.append({
                "person_id": p["person_id"],
                "full_name": p["full_name"],
                "aliases": p["aliases"],
                "gender": p["gender"],
                "age": p["age"],
                "occupation": p["occupation"] or "Unspecified",
                "phone_number": p["phone_number"] or "None on file",
                "district": p["district"],
                "city": p["city"],
                "associated_case_count": p["associated_case_count"],
                "matching_case_ids": unique_matching_cases,
                "matching_reasons": reasons,
                "threat_level": p["threat_level"]
            })

            if len(matched_persons) >= limit:
                break

    # 2. EVALUATE CASE SEARCH (if mode in ("ALL", "CASE"))
    # In ALL mode, we skip Case evaluation if purely person-specific filters were requested
    # (e.g. min_case_count, max_case_count, exact_case_count, phone_prefix, phone_suffix)
    has_person_only_filter = (
        min_case_count is not None or
        max_case_count is not None or
        exact_case_count is not None or
        bool(phone_prefix_q) or
        bool(phone_suffix_q) or
        bool(name_q) or
        bool(alias_q) or
        bool(person_id_q) or
        bool(vehicle_q) or
        bool(occ_q)
    )

    should_evaluate_cases = (mode == "CASE") or (mode == "ALL" and not has_person_only_filter)

    if should_evaluate_cases:
        for c in index["cases"]:
            reasons = []

            # 1. General query
            if general_query:
                g_match = False
                if general_query in c["case_id"].lower():
                    reasons.append(f"Case ID matched '{general_query}'")
                    g_match = True
                elif general_query in c["title"].lower():
                    reasons.append(f"Title matched query '{general_query}'")
                    g_match = True
                elif general_query in c["fir_number"].lower():
                    reasons.append(f"FIR matched '{general_query}'")
                    g_match = True
                elif general_query in c["offence_category"].lower():
                    reasons.append(f"Offence category matched '{c['offence_category']}'")
                    g_match = True
                elif general_query in c["district"].lower() or general_query in c["location_name"].lower():
                    reasons.append(f"Location matched '{general_query}'")
                    g_match = True
                elif general_query in c["police_station"].lower():
                    reasons.append(f"Police station matched '{c['police_station']}'")
                    g_match = True
                elif general_query in c["status"].lower():
                    reasons.append(f"Status matched '{c['status']}'")
                    g_match = True
                
                if not g_match:
                    continue

            # 2. Specific case ID filter
            if case_id_q:
                if case_id_q in c["case_id"].lower():
                    reasons.append(f"Matched Case ID: {c['case_id']}")
                else:
                    continue

            # 3. FIR filter
            if fir_q:
                if fir_q in c["fir_number"].lower():
                    reasons.append(f"Matched FIR: {c['fir_number']}")
                else:
                    continue

            # 4. Offence category filter
            if offence_q:
                if offence_q in c["offence_category"].lower():
                    reasons.append(f"Matched offence category: {c['offence_category']}")
                else:
                    continue

            # 5. Legal section filter
            if legal_section_q:
                if legal_section_q in c["legal_section"].lower():
                    reasons.append(f"Matched legal section: {c['legal_section']}")
                else:
                    continue

            # 6. Status filter
            if status_q:
                if status_q in c["status"].lower():
                    reasons.append(f"Matched status: {c['status']}")
                else:
                    continue

            # 7. Police station filter
            if police_station_q:
                if police_station_q in c["police_station"].lower():
                    reasons.append(f"Matched police station: {c['police_station']}")
                else:
                    continue

            # 8. District filter
            if district_q:
                if district_q in c["district"].lower():
                    reasons.append(f"Matched district: {c['district']}")
                else:
                    continue

            # 9. Location filter
            if location_q:
                matched_loc_val = None
                if location_q in c["district"].lower():
                    matched_loc_val = c["district"]
                elif location_q in c["city"].lower():
                    matched_loc_val = c["city"]
                elif location_q in c["locality"].lower():
                    matched_loc_val = c["locality"]
                elif location_q in c["location_name"].lower():
                    matched_loc_val = c["location_name"]

                if matched_loc_val:
                    reasons.append(f"Matched location: {matched_loc_val}")
                else:
                    continue

            # 10. Year filter
            if year_q:
                if c["year"] == year_q or year_q in c["date_opened"]:
                    reasons.append(f"Matched year: {year_q}")
                else:
                    continue

            if not reasons:
                reasons.append("Included in case registry index")

            matched_cases.append({
                "case_id": c["case_id"],
                "title": c["title"],
                "fir_number": c["fir_number"],
                "offence_category": c["offence_category"],
                "legal_section": c["legal_section"],
                "date_opened": c["date_opened"],
                "year": c["year"],
                "district": c["district"],
                "police_station": c["police_station"],
                "status": c["status"],
                "associated_persons_count": c["associated_persons_count"],
                "matching_reasons": reasons
            })

            if len(matched_cases) >= limit:
                break

    # Sort results deterministically
    matched_persons.sort(key=lambda x: (-x["associated_case_count"], x["person_id"]))
    matched_cases.sort(key=lambda x: (x["date_opened"], x["case_id"]), reverse=True)

    return {
        "mode": mode,
        "total_persons": len(matched_persons),
        "total_cases": len(matched_cases),
        "total_results": len(matched_persons) + len(matched_cases),
        "persons": matched_persons,
        "cases": matched_cases,
        "safety_notice": "SYNTHETIC DEMONSTRATION DATA. Deterministic search results. Analytical leads only. Requires human verification."
    }
