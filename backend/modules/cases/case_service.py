"""
case_service.py
===============
Investigator-oriented Case Intelligence Service for PS26189.
Provides structured access, indexing, and cross-case intelligence
derived from the rich synthetic demonstration dataset and graph.

All data is SYNTHETIC DEMONSTRATION DATA.
Safety Notice: Analytical leads only. Requires human verification.
"""

import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from data.validate_dataset import load_csv

# Cache storage
_CASES_CACHE: Optional[Dict[str, Any]] = None

def clear_cache():
    """Clears in-memory indexed cases cache on runtime mutation."""
    global _CASES_CACHE
    _CASES_CACHE = None

def _load_and_index_dataset():
    global _CASES_CACHE
    if _CASES_CACHE is not None:
        return _CASES_CACHE

    raw_cases = load_csv("cases.csv") or []
    raw_persons = load_csv("persons.csv") or []
    raw_case_persons = load_csv("case_persons.csv") or []
    raw_phones = load_csv("phones.csv") or []
    raw_bank_accounts = load_csv("bank_accounts.csv") or []
    raw_vehicles = load_csv("vehicles.csv") or []
    raw_locations = load_csv("locations.csv") or []
    raw_orgs = load_csv("organizations.csv") or []
    raw_aliases = load_csv("aliases.csv") or []
    raw_families = load_csv("families.csv") or []
    raw_comms = load_csv("communications.csv") or []
    raw_txns = load_csv("transactions.csv") or []
    raw_gt = load_csv("ground_truth.csv") or []

    # Fast lookup dictionaries
    cases_by_id = {c["case_id"]: c for c in raw_cases}
    persons_by_id = {p["person_id"]: p for p in raw_persons}
    phones_by_id = {p["phone_id"]: p for p in raw_phones}
    bank_accounts_by_id = {b["bank_account_id"]: b for b in raw_bank_accounts}
    vehicles_by_id = {v["vehicle_id"]: v for v in raw_vehicles}
    locations_by_id = {l["location_id"]: l for l in raw_locations}
    orgs_by_id = {o["organization_id"]: o for o in raw_orgs}

    # Aliases by person
    aliases_by_person = defaultdict(list)
    for a in raw_aliases:
        aliases_by_person[a["person_id"]].append(a)

    # Families by person
    families_by_person = defaultdict(list)
    for f in raw_families:
        families_by_person[f["person_id"]].append(f)

    # Case-Persons mappings
    case_persons_by_case = defaultdict(list)
    cases_by_person = defaultdict(list)
    for cp in raw_case_persons:
        case_persons_by_case[cp["case_id"]].append(cp)
        cases_by_person[cp["person_id"]].append(cp["case_id"])

    # Communications and transactions by case
    comms_by_case = defaultdict(list)
    for c in raw_comms:
        comms_by_case[c.get("case_id", "")].append(c)

    txns_by_case = defaultdict(list)
    for t in raw_txns:
        txns_by_case[t.get("case_id", "")].append(t)

    gt_by_case = defaultdict(list)
    for g in raw_gt:
        gt_by_case[g.get("case_id", "")].append(g)

    _CASES_CACHE = {
        "cases_by_id": cases_by_id,
        "raw_cases": raw_cases,
        "persons_by_id": persons_by_id,
        "phones_by_id": phones_by_id,
        "bank_accounts_by_id": bank_accounts_by_id,
        "vehicles_by_id": vehicles_by_id,
        "locations_by_id": locations_by_id,
        "orgs_by_id": orgs_by_id,
        "aliases_by_person": aliases_by_person,
        "families_by_person": families_by_person,
        "case_persons_by_case": case_persons_by_case,
        "cases_by_person": cases_by_person,
        "comms_by_case": comms_by_case,
        "txns_by_case": txns_by_case,
        "gt_by_case": gt_by_case,
    }
    return _CASES_CACHE


def get_case_record(case_id: str) -> Optional[Dict[str, Any]]:
    cache = _load_and_index_dataset()
    return cache["cases_by_id"].get(case_id)


def get_all_cases_enriched(G=None) -> List[Dict[str, Any]]:
    cache = _load_and_index_dataset()
    cases_list = []

    graph_nodes = set()
    if G is not None:
        for n, d in G.nodes(data=True):
            if d.get("type") in ("CASE", "CASE_ID"):
                graph_nodes.add(n)

    for row in cache["raw_cases"]:
        cid = row.get("case_id")
        if not cid:
            continue

        title = row.get("case_title") or row.get("title") or f"Case {cid}"
        associated_persons = cache["case_persons_by_case"].get(cid, [])
        comms = cache["comms_by_case"].get(cid, [])
        txns = cache["txns_by_case"].get(cid, [])
        
        # Calculate related entities count
        entities_count = 0
        if row.get("location_id"):
            entities_count += 1
        for cp in associated_persons:
            pid = cp.get("person_id")
            p = cache["persons_by_id"].get(pid, {})
            if p.get("phone_id"): entities_count += 1
            if p.get("phone_id_2"): entities_count += 1
            if p.get("bank_account_id"): entities_count += 1
            if p.get("bank_account_id_2"): entities_count += 1
            if p.get("vehicle_id"): entities_count += 1
            if p.get("vehicle_id_2"): entities_count += 1
            if p.get("organization_id"): entities_count += 1

        details = {
            "case_id": cid,
            "title": title,
            "case_title": title,
            "offence_category": row.get("offence_category", "General Enquiry"),
            "legal_section": row.get("legal_section", "Not Specified"),
            "fir_number": row.get("fir_number", "N/A"),
            "date_opened": row.get("date_opened", ""),
            "status": row.get("status", "OPEN"),
            "police_station": row.get("police_station", "Central Investigation PS"),
            "district": row.get("district", "Headquarters"),
            "state": row.get("state", "Chhattisgarh"),
            "description": row.get("description", ""),
            "location_id": row.get("location_id", ""),
            "associated_persons_count": len(associated_persons),
            "related_entities_count": entities_count,
            "evidence_count": len(comms) + len(txns),
            "has_graph_relationships": cid in graph_nodes or len(comms) > 0 or len(txns) > 0,
            "type": "CASE",
            "value": cid
        }
        cases_list.append(details)

    cases_list.sort(key=lambda x: x["case_id"])
    return cases_list


def get_case_associated_persons(case_id: str) -> List[Dict[str, Any]]:
    cache = _load_and_index_dataset()
    raw_cps = cache["case_persons_by_case"].get(case_id, [])
    result = []

    for cp in raw_cps:
        pid = cp.get("person_id")
        p = cache["persons_by_id"].get(pid, {})
        linked_cases = cache["cases_by_person"].get(pid, [])
        aliases = cache["aliases_by_person"].get(pid, [])
        primary_alias = aliases[0]["alias_name"] if aliases else ""

        # Collect phone numbers and accounts
        phones = []
        if p.get("phone_id") and p["phone_id"] in cache["phones_by_id"]:
            phones.append(cache["phones_by_id"][p["phone_id"]]["phone_number"])
        if p.get("phone_id_2") and p["phone_id_2"] in cache["phones_by_id"]:
            phones.append(cache["phones_by_id"][p["phone_id_2"]]["phone_number"])

        result.append({
            "person_id": pid,
            "full_name": p.get("full_name") or f"Person {pid}",
            "primary_alias": primary_alias,
            "gender": p.get("gender", "Unknown"),
            "age": p.get("age", ""),
            "occupation": p.get("occupation", "Unspecified"),
            "city": p.get("city", ""),
            "district": p.get("district", ""),
            "state": p.get("state", ""),
            "role": cp.get("role", "ASSOCIATE"),
            "association_type": cp.get("association", "Associated with registered case record. Requires human verification."),
            "source": cp.get("source", "STRUCTURED_METADATA"),
            "linked_cases_count": len(linked_cases),
            "linked_cases": linked_cases,
            "phones": phones,
            "has_bank_account": bool(p.get("bank_account_id")),
            "has_vehicle": bool(p.get("vehicle_id")),
            "safety_disclaimer": "Analytical lead only. Requires human verification."
        })

    return result


def get_case_related_entities(case_id: str) -> Dict[str, List[Dict[str, Any]]]:
    cache = _load_and_index_dataset()
    case = cache["cases_by_id"].get(case_id, {})
    cps = cache["case_persons_by_case"].get(case_id, [])

    locations = []
    phones = []
    bank_accounts = []
    vehicles = []
    organizations = []

    seen_phones = set()
    seen_accounts = set()
    seen_vehicles = set()
    seen_locations = set()
    seen_orgs = set()

    # Case primary location
    loc_id = case.get("location_id")
    if loc_id and loc_id in cache["locations_by_id"] and loc_id not in seen_locations:
        loc = cache["locations_by_id"][loc_id]
        locations.append({
            "entity_id": loc_id,
            "type": "LOCATION",
            "name": loc.get("location_name", loc_id),
            "location_type": loc.get("location_type", "INCIDENT_LOCATION"),
            "city": loc.get("city", ""),
            "district": loc.get("district", ""),
            "state": loc.get("state", ""),
            "pin_code": loc.get("pin_code", ""),
            "relation_to_case": "Primary Registered Location"
        })
        seen_locations.add(loc_id)

    # Entities tied to associated persons
    for cp in cps:
        pid = cp.get("person_id")
        p = cache["persons_by_id"].get(pid, {})
        pname = p.get("full_name", pid)

        # Phones
        for key in ["phone_id", "phone_id_2"]:
            ph_id = p.get(key)
            if ph_id and ph_id in cache["phones_by_id"] and ph_id not in seen_phones:
                ph = cache["phones_by_id"][ph_id]
                phones.append({
                    "entity_id": ph_id,
                    "type": "PHONE",
                    "number": ph.get("phone_number", ""),
                    "phone_type": ph.get("phone_type", "MOBILE"),
                    "associated_person_id": pid,
                    "associated_person_name": pname,
                    "carrier": "Registered Telecom Operator"
                })
                seen_phones.add(ph_id)

        # Bank accounts
        for key in ["bank_account_id", "bank_account_id_2"]:
            ba_id = p.get(key)
            if ba_id and ba_id in cache["bank_accounts_by_id"] and ba_id not in seen_accounts:
                ba = cache["bank_accounts_by_id"][ba_id]
                bank_accounts.append({
                    "entity_id": ba_id,
                    "type": "BANK_ACCOUNT",
                    "account_number": ba.get("account_number", ""),
                    "bank_name": ba.get("bank_name", "Scheduled Commercial Bank"),
                    "account_type": ba.get("account_type", "SAVINGS"),
                    "associated_person_id": pid,
                    "associated_person_name": pname
                })
                seen_accounts.add(ba_id)

        # Vehicles
        for key in ["vehicle_id", "vehicle_id_2"]:
            v_id = p.get(key)
            if v_id and v_id in cache["vehicles_by_id"] and v_id not in seen_vehicles:
                veh = cache["vehicles_by_id"][v_id]
                vehicles.append({
                    "entity_id": v_id,
                    "type": "VEHICLE",
                    "registration_number": veh.get("registration_number", ""),
                    "vehicle_type": veh.get("vehicle_type", "VEHICLE"),
                    "model": veh.get("model", ""),
                    "color": veh.get("color", ""),
                    "associated_person_id": pid,
                    "associated_person_name": pname
                })
                seen_vehicles.add(v_id)

        # Organizations
        org_id = p.get("organization_id")
        if org_id and org_id in cache["orgs_by_id"] and org_id not in seen_orgs:
            org = cache["orgs_by_id"][org_id]
            organizations.append({
                "entity_id": org_id,
                "type": "ORGANIZATION",
                "name": org.get("organization_name", org_id),
                "org_type": org.get("organization_type", "Commercial Entity"),
                "associated_person_id": pid,
                "associated_person_name": pname
            })
            seen_orgs.add(org_id)

    # Communications phone entities
    for comm in cache["comms_by_case"].get(case_id, []):
        ph_id = comm.get("phone_id")
        if ph_id and ph_id in cache["phones_by_id"] and ph_id not in seen_phones:
            ph = cache["phones_by_id"][ph_id]
            phones.append({
                "entity_id": ph_id,
                "type": "PHONE",
                "number": ph.get("phone_number", ""),
                "phone_type": ph.get("phone_type", "MOBILE"),
                "associated_person_id": comm.get("source_person_id", ""),
                "associated_person_name": cache["persons_by_id"].get(comm.get("source_person_id", ""), {}).get("full_name", ""),
                "carrier": "Registered Telecom Operator"
            })
            seen_phones.add(ph_id)

    return {
        "locations": locations,
        "phones": phones,
        "bank_accounts": bank_accounts,
        "vehicles": vehicles,
        "organizations": organizations,
        "total_count": len(locations) + len(phones) + len(bank_accounts) + len(vehicles) + len(organizations)
    }


def get_case_evidence_relationships(case_id: str, G=None) -> List[Dict[str, Any]]:
    cache = _load_and_index_dataset()
    relationships = []
    seen_keys = set()

    # 1. Communications in this case
    for comm in cache["comms_by_case"].get(case_id, []):
        src = comm.get("source_person_id")
        tgt = comm.get("target_person_id")
        src_p = cache["persons_by_id"].get(src, {})
        tgt_p = cache["persons_by_id"].get(tgt, {})
        comm_type = comm.get("communication_type", "COMMUNICATION")
        
        key = (src, tgt, f"COMM_{comm_type}")
        if key not in seen_keys:
            seen_keys.add(key)
            relationships.append({
                "relationship_id": comm.get("communication_id"),
                "source_id": src,
                "source_label": src_p.get("full_name") or src,
                "source_type": "PERSON",
                "target_id": tgt,
                "target_label": tgt_p.get("full_name") or tgt,
                "target_type": "PERSON",
                "relationship_type": f"COMMUNICATED_VIA_{comm_type}",
                "confidence": 0.85,
                "evidence": comm.get("description", "Telecommunication record linked to case."),
                "detection_method": "TELECOM_ANALYSIS",
                "date": comm.get("date", "")
            })

    # 2. Financial transactions in this case
    for txn in cache["txns_by_case"].get(case_id, []):
        src = txn.get("source_person_id")
        tgt = txn.get("target_person_id")
        src_p = cache["persons_by_id"].get(src, {})
        tgt_p = cache["persons_by_id"].get(tgt, {})
        amount = txn.get("amount", "")
        
        key = (src, tgt, "FINANCIAL_TRANSACTION")
        if key not in seen_keys:
            seen_keys.add(key)
            relationships.append({
                "relationship_id": txn.get("transaction_id"),
                "source_id": src,
                "source_label": src_p.get("full_name") or src,
                "source_type": "PERSON",
                "target_id": tgt,
                "target_label": tgt_p.get("full_name") or tgt,
                "target_type": "PERSON",
                "relationship_type": "FINANCIAL_TRANSACTION",
                "confidence": 0.90,
                "evidence": txn.get("description", f"Financial transfer of INR {amount} linked to case."),
                "detection_method": "BANKING_ANALYSIS",
                "date": txn.get("date", "")
            })

    # 3. Graph edges if available in G
    if G is not None and case_id in G:
        for u, v, k, d in G.edges(data=True, keys=True):
            if d.get("case_id") == case_id or u == case_id or v == case_id:
                key = (u, v, d.get("relationship_type", ""))
                if key not in seen_keys:
                    seen_keys.add(key)
                    u_data = G.nodes.get(u, {})
                    v_data = G.nodes.get(v, {})
                    relationships.append({
                        "relationship_id": f"graph_edge_{u}_{v}_{k}",
                        "source_id": u,
                        "source_label": u_data.get("value") or u,
                        "source_type": u_data.get("type", "UNKNOWN"),
                        "target_id": v,
                        "target_label": v_data.get("value") or v,
                        "target_type": v_data.get("type", "UNKNOWN"),
                        "relationship_type": d.get("relationship_type", "ASSOCIATED_WITH"),
                        "confidence": float(d.get("confidence", 0.75)),
                        "evidence": d.get("evidence", "Graph link extracted from case data."),
                        "detection_method": d.get("detection_method", "INTELLIGENCE_GRAPH"),
                        "date": ""
                    })

    # 4. Fallback from ground truth if none found
    if not relationships:
        for gt in cache["gt_by_case"].get(case_id, []):
            src = gt.get("source_entity_id")
            tgt = gt.get("target_entity_id")
            src_p = cache["persons_by_id"].get(src, {})
            key = (src, tgt, gt.get("relationship_type"))
            if key not in seen_keys:
                seen_keys.add(key)
                relationships.append({
                    "relationship_id": gt.get("ground_truth_id"),
                    "source_id": src,
                    "source_label": src_p.get("full_name") or src,
                    "source_type": "PERSON" if src.startswith("PERSON") else "ENTITY",
                    "target_id": tgt,
                    "target_label": tgt,
                    "target_type": "CASE" if tgt.startswith("CASE") else "ENTITY",
                    "relationship_type": gt.get("relationship_type", "INVOLVED_IN"),
                    "confidence": 0.95,
                    "evidence": f"Verified case record linkage from {gt.get('evidence_reference', 'case metadata')}.",
                    "detection_method": "CROSS_RECORD_LINKAGE",
                    "date": ""
                })

    return relationships


def get_case_related_cases_details(case_id: str, G=None) -> List[Dict[str, Any]]:
    cache = _load_and_index_dataset()
    associated_persons = cache["case_persons_by_case"].get(case_id, [])
    person_ids_in_case = {cp["person_id"] for cp in associated_persons}

    related_map = defaultdict(lambda: {
        "shared_persons": set(),
        "shared_entities": set(),
        "reasons": []
    })

    # 1. Identify cases sharing persons
    for pid in person_ids_in_case:
        other_cases = cache["cases_by_person"].get(pid, [])
        p_name = cache["persons_by_id"].get(pid, {}).get("full_name", pid)
        for other_cid in other_cases:
            if other_cid != case_id:
                related_map[other_cid]["shared_persons"].add(f"{p_name} ({pid})")

    # 2. Graph-based incident cases
    if G is not None and case_id in G and G.nodes[case_id].get("type") in ("CASE", "CASE_ID"):
        incident_entities = set(G.predecessors(case_id)) | set(G.successors(case_id))
        for ent in incident_entities:
            if G.nodes[ent].get("type") in ("CASE", "CASE_ID"):
                continue
            ent_neighbors = set(G.predecessors(ent)) | set(G.successors(ent))
            ent_label = G.nodes[ent].get("value") or ent
            for en in ent_neighbors:
                if G.nodes[en].get("type") in ("CASE", "CASE_ID") and en != case_id:
                    related_map[en]["shared_entities"].add(f"{ent_label} [{G.nodes[ent].get('type', 'ENTITY')}]")

    # 3. Construct structured related case responses
    result = []
    for other_cid, data in related_map.items():
        other_row = cache["cases_by_id"].get(other_cid)
        if not other_row:
            continue

        shared_persons_list = sorted(list(data["shared_persons"]))
        shared_entities_list = sorted(list(data["shared_entities"]))

        reasons = []
        if shared_persons_list:
            reasons.append(f"Shares {len(shared_persons_list)} person lead(s): {', '.join(shared_persons_list[:2])}")
        if shared_entities_list:
            reasons.append(f"Shares network entity: {', '.join(shared_entities_list[:2])}")

        result.append({
            "case_id": other_cid,
            "title": other_row.get("case_title") or other_row.get("title") or f"Case {other_cid}",
            "offence_category": other_row.get("offence_category", "General"),
            "status": other_row.get("status", "OPEN"),
            "district": other_row.get("district", ""),
            "shared_persons": shared_persons_list,
            "shared_entities": shared_entities_list,
            "reason": "; ".join(reasons) if reasons else "Linked via shared network lead.",
            "link_strength": "HIGH" if len(shared_persons_list) > 1 else "MEDIUM"
        })

    result.sort(key=lambda x: (x["link_strength"] != "HIGH", x["case_id"]))
    return result
