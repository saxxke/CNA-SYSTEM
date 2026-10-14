"""
person_service.py
=================
Investigator-oriented Person Profile Intelligence Service for PS26189.
Extracts identity, demographics, aliases, contact details, associated cases,
assets, family relationships, evidence relationships, network metrics, and
investigation priority from the rich synthetic dataset.

All data is SYNTHETIC DEMONSTRATION DATA.
Safety Notice: Analytical leads only. Requires human verification.
Family relationships strictly do not imply case involvement or criminality.
"""

import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from data.validate_dataset import load_csv

# In-memory cache
_PERSONS_CACHE: Optional[Dict[str, Any]] = None

def clear_cache():
    """Clears in-memory indexed person cache on runtime mutation."""
    global _PERSONS_CACHE
    _PERSONS_CACHE = None

def _load_and_index():
    global _PERSONS_CACHE
    if _PERSONS_CACHE is not None:
        return _PERSONS_CACHE

    raw_persons = load_csv("persons.csv") or []
    raw_aliases = load_csv("aliases.csv") or []
    raw_families = load_csv("families.csv") or []
    raw_phones = load_csv("phones.csv") or []
    raw_bank_accounts = load_csv("bank_accounts.csv") or []
    raw_vehicles = load_csv("vehicles.csv") or []
    raw_locations = load_csv("locations.csv") or []
    raw_orgs = load_csv("organizations.csv") or []
    raw_case_persons = load_csv("case_persons.csv") or []
    raw_cases = load_csv("cases.csv") or []
    raw_comms = load_csv("communications.csv") or []
    raw_txns = load_csv("transactions.csv") or []
    raw_gt = load_csv("ground_truth.csv") or []

    # Dictionaries by ID
    persons_by_id = {p["person_id"]: p for p in raw_persons}
    cases_by_id = {c["case_id"]: c for c in raw_cases}
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
    case_persons_by_person = defaultdict(list)
    for cp in raw_case_persons:
        case_persons_by_person[cp["person_id"]].append(cp)

    # Communications and transactions involving person
    comms_by_person = defaultdict(list)
    for c in raw_comms:
        src = c.get("source_person_id")
        tgt = c.get("target_person_id")
        if src: comms_by_person[src].append(c)
        if tgt and tgt != src: comms_by_person[tgt].append(c)

    txns_by_person = defaultdict(list)
    for t in raw_txns:
        src = t.get("source_person_id")
        tgt = t.get("target_person_id")
        if src: txns_by_person[src].append(t)
        if tgt and tgt != src: txns_by_person[tgt].append(t)

    gt_by_person = defaultdict(list)
    for g in raw_gt:
        src = g.get("source_entity_id")
        tgt = g.get("target_entity_id")
        if src: gt_by_person[src].append(g)
        if tgt and tgt != src: gt_by_person[tgt].append(g)

    _PERSONS_CACHE = {
        "raw_persons": raw_persons,
        "persons_by_id": persons_by_id,
        "cases_by_id": cases_by_id,
        "phones_by_id": phones_by_id,
        "bank_accounts_by_id": bank_accounts_by_id,
        "vehicles_by_id": vehicles_by_id,
        "locations_by_id": locations_by_id,
        "orgs_by_id": orgs_by_id,
        "aliases_by_person": aliases_by_person,
        "families_by_person": families_by_person,
        "case_persons_by_person": case_persons_by_person,
        "comms_by_person": comms_by_person,
        "txns_by_person": txns_by_person,
        "gt_by_person": gt_by_person,
    }
    return _PERSONS_CACHE


def list_persons_summary(search: Optional[str] = None, district: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    cache = _load_and_index()
    results = []

    q = (search or "").lower().strip()
    d_filter = (district or "").lower().strip()

    for p in cache["raw_persons"]:
        pid = p["person_id"]
        name = p.get("full_name", "")
        dist = p.get("district", "")
        city = p.get("city", "")
        occ = p.get("occupation", "")
        
        aliases = cache["aliases_by_person"].get(pid, [])
        primary_alias = aliases[0]["alias_name"] if aliases else ""

        # Check district filter
        if d_filter and d_filter not in dist.lower():
            continue

        # Check search query
        if q:
            match = (
                q in pid.lower() or
                q in name.lower() or
                q in primary_alias.lower() or
                q in dist.lower() or
                q in city.lower() or
                q in occ.lower()
            )
            if not match:
                continue

        linked_cases = cache["case_persons_by_person"].get(pid, [])
        phone_obj = cache["phones_by_id"].get(p.get("phone_id"), {})

        results.append({
            "person_id": pid,
            "full_name": name,
            "primary_alias": primary_alias,
            "gender": p.get("gender", "Unknown"),
            "age": p.get("age", ""),
            "occupation": occ,
            "district": dist,
            "city": city,
            "phone_number": phone_obj.get("phone_number", ""),
            "linked_cases_count": len(linked_cases),
            "threat_level": p.get("threat_level", "STANDARD"),
            "type": "PERSON"
        })

        if limit and len(results) >= limit:
            break

    results.sort(key=lambda x: (-x["linked_cases_count"], x["person_id"]))
    return results


def get_person_profile(
    person_id: str,
    G=None,
    analytics: Optional[Dict[str, Any]] = None,
    priority: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    cache = _load_and_index()
    p = cache["persons_by_id"].get(person_id)
    if not p:
        return None

    # 1. Demographics
    demographics = {
        "person_id": person_id,
        "full_name": p.get("full_name", f"Person {person_id}"),
        "first_name": p.get("first_name", ""),
        "last_name": p.get("last_name", ""),
        "gender": p.get("gender", "Unknown"),
        "date_of_birth": p.get("date_of_birth", ""),
        "age": p.get("age", ""),
        "occupation": p.get("occupation", "Unspecified"),
        "education": p.get("education", "Not Recorded"),
        "address": p.get("address", "Registered Address on File"),
        "locality": p.get("locality", ""),
        "city": p.get("city", ""),
        "district": p.get("district", ""),
        "state": p.get("state", "Chhattisgarh"),
        "pin_code": p.get("pin_code", ""),
        "email": p.get("email", "")
    }

    # 2. Aliases
    raw_aliases = cache["aliases_by_person"].get(person_id, [])
    aliases = [
        {
            "alias_id": a.get("alias_id", ""),
            "alias_name": a.get("alias_name", ""),
            "alias_type": a.get("alias_type", "Alternative Reference")
        }
        for a in raw_aliases
    ]
    primary_alias = aliases[0]["alias_name"] if aliases else ""

    # 3. Contact information
    phones = []
    for ph_key in ["phone_id", "phone_id_2"]:
        ph_id = p.get(ph_key)
        if ph_id and ph_id in cache["phones_by_id"]:
            ph = cache["phones_by_id"][ph_id]
            phones.append({
                "phone_id": ph_id,
                "phone_number": ph.get("phone_number", ""),
                "phone_type": ph.get("phone_type", "MOBILE"),
                "carrier": "Registered Telecom Operator",
                "is_primary": ph_key == "phone_id"
            })

    contact = {
        "phones": phones,
        "email": p.get("email", ""),
        "residential_address": f"{p.get('address', '')}{', ' + p.get('locality', '') if p.get('locality') else ''}{', ' + p.get('city', '') if p.get('city') else ''}{' — PIN: ' + p.get('pin_code', '') if p.get('pin_code') else ''}".strip(', ')
    }

    # 4. Associated Case Records
    raw_cps = cache["case_persons_by_person"].get(person_id, [])
    associated_cases = []
    case_ids = []

    for cp in raw_cps:
        cid = cp.get("case_id")
        case_ids.append(cid)
        case_row = cache["cases_by_id"].get(cid, {})
        associated_cases.append({
            "case_id": cid,
            "title": case_row.get("case_title") or case_row.get("title") or f"Case {cid}",
            "fir_number": case_row.get("fir_number", "N/A"),
            "offence_category": case_row.get("offence_category", "General Enquiry"),
            "legal_section": case_row.get("legal_section", "Not Specified"),
            "date_opened": case_row.get("date_opened", ""),
            "district": case_row.get("district", ""),
            "police_station": case_row.get("police_station", "Central Station"),
            "status": case_row.get("status", "OPEN"),
            "role": cp.get("role", "ASSOCIATE"),
            "association_narrative": cp.get("association", "Associated with registered case record. Requires human verification."),
            "source": cp.get("source", "STRUCTURED_METADATA")
        })

    # Sort cases by date_opened descending
    associated_cases.sort(key=lambda x: x.get("date_opened", ""), reverse=True)

    # 5. Assets & Identifiers
    bank_accounts = []
    for ba_key in ["bank_account_id", "bank_account_id_2"]:
        ba_id = p.get(ba_key)
        if ba_id and ba_id in cache["bank_accounts_by_id"]:
            ba = cache["bank_accounts_by_id"][ba_id]
            bank_accounts.append({
                "bank_account_id": ba_id,
                "account_number": ba.get("account_number", ""),
                "bank_name": ba.get("bank_name", "Scheduled Commercial Bank"),
                "account_type": ba.get("account_type", "SAVINGS")
            })

    vehicles = []
    for v_key in ["vehicle_id", "vehicle_id_2"]:
        v_id = p.get(v_key)
        if v_id and v_id in cache["vehicles_by_id"]:
            veh = cache["vehicles_by_id"][v_id]
            vehicles.append({
                "vehicle_id": v_id,
                "registration_number": veh.get("registration_number", ""),
                "vehicle_type": veh.get("vehicle_type", "VEHICLE"),
                "model": veh.get("model", ""),
                "color": veh.get("color", "")
            })

    org = None
    if p.get("organization_id") and p["organization_id"] in cache["orgs_by_id"]:
        o = cache["orgs_by_id"][p["organization_id"]]
        org = {
            "organization_id": p["organization_id"],
            "organization_name": o.get("organization_name", p["organization_id"]),
            "organization_type": o.get("organization_type", "Commercial Entity")
        }

    location = None
    if p.get("location_id") and p["location_id"] in cache["locations_by_id"]:
        loc = cache["locations_by_id"][p["location_id"]]
        location = {
            "location_id": p["location_id"],
            "location_name": loc.get("location_name", p["location_id"]),
            "location_type": loc.get("location_type", "RESIDENTIAL"),
            "city": loc.get("city", ""),
            "district": loc.get("district", ""),
            "state": loc.get("state", ""),
            "pin_code": loc.get("pin_code", "")
        }

    assets = {
        "phones": phones,
        "bank_accounts": bank_accounts,
        "vehicles": vehicles,
        "organization": org,
        "location": location,
        "total_assets_count": len(phones) + len(bank_accounts) + len(vehicles) + (1 if org else 0) + (1 if location else 0)
    }

    # 6. Family Relationships (Strict Safety Rule: Does not imply case involvement)
    raw_families = cache["families_by_person"].get(person_id, [])
    family_relationships = []
    for f in raw_families:
        rel_pid = f.get("related_person_id")
        rel_person = cache["persons_by_id"].get(rel_pid, {})
        rel_sub = f.get("relationship_subtype", "RELATIVE")
        rel_name = rel_person.get("full_name") or f"Person {rel_pid}"
        subj_name = demographics.get("full_name") or f"Person {person_id}"
        family_relationships.append({
            "family_id": f.get("family_id", ""),
            "related_person_id": rel_pid,
            "related_person_name": rel_name,
            "relationship_subtype": rel_sub,
            "relation_to_subject": f"{rel_name} is the {rel_sub} of {subj_name}",
            "notes": f.get("notes", "Synthetic family record."),
            "safety_disclaimer": "Family relationship does not imply case involvement or criminality."
        })

    # 7. Evidence-Backed Relationships
    evidence_relationships = []
    seen_evidence_keys = set()

    # Communications
    for comm in cache["comms_by_person"].get(person_id, []):
        src = comm.get("source_person_id")
        tgt = comm.get("target_person_id")
        is_source = (src == person_id)
        other_id = tgt if is_source else src
        other_p = cache["persons_by_id"].get(other_id, {})
        comm_type = comm.get("communication_type", "COMMUNICATION")

        key = (src, tgt, f"COMM_{comm_type}")
        if key not in seen_evidence_keys:
            seen_evidence_keys.add(key)
            evidence_relationships.append({
                "relationship_id": comm.get("communication_id"),
                "source_id": src,
                "source_label": cache["persons_by_id"].get(src, {}).get("full_name", src),
                "target_id": tgt,
                "target_label": other_p.get("full_name", tgt),
                "connected_entity_id": other_id,
                "connected_entity_name": other_p.get("full_name", other_id),
                "relationship_type": f"COMMUNICATED_VIA_{comm_type}",
                "direction": "OUTGOING" if is_source else "INCOMING",
                "confidence": 0.85,
                "evidence": comm.get("description", "Telecommunication record linked to case."),
                "case_id": comm.get("case_id", ""),
                "detection_method": "TELECOM_ANALYSIS",
                "date": comm.get("date", "")
            })

    # Transactions
    for txn in cache["txns_by_person"].get(person_id, []):
        src = txn.get("source_person_id")
        tgt = txn.get("target_person_id")
        is_source = (src == person_id)
        other_id = tgt if is_source else src
        other_p = cache["persons_by_id"].get(other_id, {})
        amount = txn.get("amount", "")

        key = (src, tgt, "FINANCIAL_TRANSACTION")
        if key not in seen_evidence_keys:
            seen_evidence_keys.add(key)
            evidence_relationships.append({
                "relationship_id": txn.get("transaction_id"),
                "source_id": src,
                "source_label": cache["persons_by_id"].get(src, {}).get("full_name", src),
                "target_id": tgt,
                "target_label": other_p.get("full_name", tgt),
                "connected_entity_id": other_id,
                "connected_entity_name": other_p.get("full_name", other_id),
                "relationship_type": "FINANCIAL_TRANSACTION",
                "direction": "OUTGOING" if is_source else "INCOMING",
                "confidence": 0.90,
                "evidence": txn.get("description", f"Financial transfer of INR {amount} linked to case."),
                "case_id": txn.get("case_id", ""),
                "detection_method": "BANKING_ANALYSIS",
                "date": txn.get("date", "")
            })

    # Graph edges
    connected_nodes_set = set()
    if G is not None and person_id in G:
        for neighbor in set(G.predecessors(person_id)) | set(G.successors(person_id)):
            connected_nodes_set.add(neighbor)

        for u, v, k, d in list(G.in_edges(person_id, data=True, keys=True)) + list(G.out_edges(person_id, data=True, keys=True)):
            key = (u, v, d.get("relationship_type", ""))
            if key not in seen_evidence_keys:
                seen_evidence_keys.add(key)
                u_data = G.nodes.get(u, {})
                v_data = G.nodes.get(v, {})
                other_id = v if u == person_id else u
                other_label = (v_data if u == person_id else u_data).get("value") or other_id
                evidence_relationships.append({
                    "relationship_id": f"graph_{u}_{v}_{k}",
                    "source_id": u,
                    "source_label": u_data.get("value") or u,
                    "target_id": v,
                    "target_label": v_data.get("value") or v,
                    "connected_entity_id": other_id,
                    "connected_entity_name": other_label,
                    "relationship_type": d.get("relationship_type", "ASSOCIATED_WITH"),
                    "direction": "OUTGOING" if u == person_id else "INCOMING",
                    "confidence": float(d.get("confidence", 0.75)),
                    "evidence": d.get("evidence", "Graph link extracted from case data."),
                    "case_id": d.get("case_id", ""),
                    "detection_method": d.get("detection_method", "INTELLIGENCE_GRAPH"),
                    "date": ""
                })

    # Fallback to ground truth if empty
    if not evidence_relationships:
        for gt in cache["gt_by_person"].get(person_id, []):
            src = gt.get("source_entity_id")
            tgt = gt.get("target_entity_id")
            key = (src, tgt, gt.get("relationship_type"))
            if key not in seen_evidence_keys:
                seen_evidence_keys.add(key)
                evidence_relationships.append({
                    "relationship_id": gt.get("ground_truth_id"),
                    "source_id": src,
                    "source_label": cache["persons_by_id"].get(src, {}).get("full_name", src),
                    "target_id": tgt,
                    "target_label": tgt,
                    "connected_entity_id": tgt if src == person_id else src,
                    "connected_entity_name": tgt if src == person_id else src,
                    "relationship_type": gt.get("relationship_type", "INVOLVED_IN"),
                    "direction": "OUTGOING" if src == person_id else "INCOMING",
                    "confidence": 0.95,
                    "evidence": f"Verified record linkage from {gt.get('evidence_reference', 'case metadata')}.",
                    "case_id": gt.get("case_id", ""),
                    "detection_method": "CROSS_RECORD_LINKAGE",
                    "date": ""
                })

    # 8. Network Summary
    distinct_types = {r["relationship_type"] for r in evidence_relationships}
    related_person_ids = {r["connected_entity_id"] for r in evidence_relationships if r["connected_entity_id"].startswith("PERSON-")}
    primary_case = case_ids[0] if case_ids else "CASE-001"

    network_summary = {
        "connected_entities_count": len(connected_nodes_set) if connected_nodes_set else len(evidence_relationships),
        "related_persons_count": len(related_person_ids),
        "associated_cases_count": len(associated_cases),
        "relationship_types": sorted(list(distinct_types)),
        "has_graph": bool(G is not None and person_id in G),
        "primary_case_id": primary_case
    }

    # 9. Graph Metrics & Analytics
    graph_metrics = {}
    if analytics:
        for r in analytics.get("degree_centrality", []):
            if r["entity_id"] == person_id:
                graph_metrics["degree_centrality"] = r["centrality_score"]
        for r in analytics.get("betweenness_centrality", []):
            if r["entity_id"] == person_id:
                graph_metrics["betweenness_centrality"] = r["betweenness_score"]

    # 10. Investigation Priority
    priority_info = None
    if priority:
        for pr in priority:
            if pr.get("entity_id") == person_id:
                priority_info = {
                    "entity_id": person_id,
                    "priority_score": pr.get("priority_score", 0.0),
                    "priority_level": pr.get("priority_level", "LOW"),
                    "reasons": pr.get("reasons", []),
                    "supporting_evidence": pr.get("supporting_evidence", []),
                    "safety_disclaimer": "Investigation Priority score is an analytical lead for prioritization. Requires human verification."
                }
                break

    # Build connected_entities for backward compatibility with existing tests
    connected_entities_compat = []
    if G is not None and person_id in G:
        for n in set(G.predecessors(person_id)) | set(G.successors(person_id)):
            connected_entities_compat.append({"id": n, "type": G.nodes[n].get("type", "UNKNOWN")})
    elif evidence_relationships:
        for r in evidence_relationships:
            connected_entities_compat.append({"id": r["connected_entity_id"], "type": "PERSON" if r["connected_entity_id"].startswith("PERSON") else "ENTITY"})

    return {
        "entity_id": person_id,
        "entity_type": "PERSON",
        "value": demographics["full_name"],
        "primary_alias": primary_alias,
        "demographics": demographics,
        "aliases": aliases,
        "contact": contact,
        "associated_cases": associated_cases,
        "assets": assets,
        "family_relationships": family_relationships,
        "network_summary": network_summary,
        "evidence_relationships": evidence_relationships,
        "graph_metrics": graph_metrics,
        "priority_information": priority_info,
        "connected_entities": connected_entities_compat,
        "details": demographics,
        "safety_notice": "SYNTHETIC DEMONSTRATION DATA. Analytical lead only. Requires human verification."
    }


def get_person_family_profile(person_id: str) -> Optional[Dict[str, Any]]:
    """
    Step 19: Dedicated Investigator Family Profile Service.
    
    SAFETY PRINCIPLE:
    FAMILY RELATIONSHIP != CASE INVOLVEMENT != CRIMINALITY
    Family relationships are strictly civilian records from families.csv and persons.csv.
    They must never be merged into investigative networks, evidence relationships, or priority scoring.
    """
    cache = _load_and_index()
    p = cache["persons_by_id"].get(person_id)
    if not p:
        return None

    subject_name = p.get("full_name") or f"Person {person_id}"
    raw_families = cache["families_by_person"].get(person_id, [])

    # Map expected reciprocal types
    RECIPROCAL_MAP = {
        "FATHER": ["CHILD", "SON", "DAUGHTER"],
        "MOTHER": ["CHILD", "SON", "DAUGHTER"],
        "CHILD": ["FATHER", "MOTHER", "PARENT"],
        "SON": ["FATHER", "MOTHER", "PARENT"],
        "DAUGHTER": ["FATHER", "MOTHER", "PARENT"],
        "SPOUSE": ["SPOUSE", "HUSBAND", "WIFE"],
        "BROTHER": ["BROTHER", "SISTER", "SIBLING"],
        "SISTER": ["BROTHER", "SISTER", "SIBLING"],
    }

    family_members = []
    groupings = {
        "FATHER": [],
        "MOTHER": [],
        "SPOUSE": [],
        "BROTHER": [],
        "SISTER": [],
        "CHILD": [],
        "OTHER": []
    }

    separate_investigative_records = []

    for f in raw_families:
        rel_pid = f.get("related_person_id")
        rel_person = cache["persons_by_id"].get(rel_pid, {})
        rel_sub = f.get("relationship_subtype", "OTHER").upper()
        rel_name = rel_person.get("full_name") or f"Person {rel_pid}"

        # Check for reciprocal record in families.csv (do NOT fabricate if missing)
        reverse_records = cache["families_by_person"].get(rel_pid, [])
        reciprocal_found = None
        for r_rec in reverse_records:
            if r_rec.get("related_person_id") == person_id:
                reciprocal_found = r_rec
                break

        is_reciprocal_verified = False
        reciprocal_subtype = None
        if reciprocal_found:
            reciprocal_subtype = reciprocal_found.get("relationship_subtype", "").upper()
            expected = RECIPROCAL_MAP.get(rel_sub, [])
            if reciprocal_subtype in expected or reciprocal_subtype == rel_sub:
                is_reciprocal_verified = True

        # Check if this family member has independent case involvement
        # (strictly reported as separate investigative context)
        rel_cases_raw = cache["case_persons_by_person"].get(rel_pid, [])
        independent_cases = []
        for cp in rel_cases_raw:
            cid = cp.get("case_id")
            case_row = cache["cases_by_id"].get(cid, {})
            independent_cases.append({
                "case_id": cid,
                "title": case_row.get("case_title") or case_row.get("title") or f"Case {cid}",
                "status": case_row.get("status", "OPEN"),
                "role_in_case": cp.get("role") or cp.get("role_in_case") or "ASSOCIATE"
            })

        if independent_cases:
            separate_investigative_records.append({
                "person_id": rel_pid,
                "person_name": rel_name,
                "family_relationship_to_subject": f"{rel_name} is the {rel_sub} of {subject_name}",
                "case_count": len(independent_cases),
                "cases": independent_cases,
                "safety_disclaimer": "Case involvement is shown separately and must be independently verified. Family relationship does NOT imply involvement."
            })

        member_entry = {
            "family_id": f.get("family_id", ""),
            "related_person_id": rel_pid,
            "related_person_name": rel_name,
            "relationship_subtype": rel_sub,
            "relation_to_subject": f"{rel_name} is the {rel_sub} of {subject_name}",
            "age": rel_person.get("age", ""),
            "gender": rel_person.get("gender", "Unknown"),
            "occupation": rel_person.get("occupation", ""),
            "locality": rel_person.get("locality", ""),
            "city": rel_person.get("city", ""),
            "district": rel_person.get("district", ""),
            "state": rel_person.get("state", "Chhattisgarh"),
            "phone_id": rel_person.get("phone_id", ""),
            "notes": f.get("notes", "Synthetic family record."),
            "reciprocal_status": {
                "is_verified": is_reciprocal_verified,
                "reciprocal_subtype": reciprocal_subtype,
                "description": "Reciprocal link verified in database" if is_reciprocal_verified else "Source-recorded record (one-way in database; not fabricated)"
            },
            "has_independent_cases": len(independent_cases) > 0,
            "independent_cases_count": len(independent_cases),
            "safety_notice": "Civilian family record. Does NOT imply case involvement or criminality."
        }

        family_members.append(member_entry)

        # Categorize into groupings
        if rel_sub in groupings:
            groupings[rel_sub].append(member_entry)
        elif rel_sub in ("SON", "DAUGHTER"):
            groupings["CHILD"].append(member_entry)
        else:
            groupings["OTHER"].append(member_entry)

    # Sort members deterministically
    family_members.sort(key=lambda x: (x["relationship_subtype"], x["related_person_id"]))

    return {
        "person_id": person_id,
        "person_name": subject_name,
        "demographics": {
            "age": p.get("age", ""),
            "gender": p.get("gender", "Unknown"),
            "occupation": p.get("occupation", ""),
            "city": p.get("city", ""),
            "district": p.get("district", "")
        },
        "family_relationships_count": len(family_members),
        "family_relationships": family_members,
        "grouped_family": groupings,
        "counts_by_type": {
            "father": len(groupings["FATHER"]),
            "mother": len(groupings["MOTHER"]),
            "spouse": len(groupings["SPOUSE"]),
            "brother": len(groupings["BROTHER"]),
            "sister": len(groupings["SISTER"]),
            "child": len(groupings["CHILD"]),
            "other": len(groupings["OTHER"])
        },
        "separate_investigative_context": {
            "members_with_cases_count": len(separate_investigative_records),
            "records": separate_investigative_records,
            "mandatory_safety_notice": (
                "Family relationship data is shown only as recorded relationship information. "
                "Family relationship does NOT imply case involvement, criminality, guilt, or investigative association."
            )
        },
        "mandatory_safety_notice": (
            "Family relationship data is shown only as recorded relationship information. "
            "Family relationship does NOT imply case involvement, criminality, guilt, or investigative association."
        )
    }

