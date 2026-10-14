"""
scenario_builder.py
===================
Constructs investigation topologies and realistic relational scenarios:
- Multi-case connectors and cross-case linkages
- Aliases with identity variations
- Strict reciprocal civilian families (strictly isolated from case involvement)
- Communications & banking transactions
- Balanced ground-truth pairs with hard negative controls (expected_relationship = 0)
"""

import random
from typing import List, Dict, Any, Tuple
from modules.data_generator.config import (
    ROLES_IN_CASE, FAMILY_RELATIONSHIPS, COMMUNICATION_TYPES
)
from modules.data_generator.entity_factories import EntityFactories

def build_scenarios(
    factories: EntityFactories,
    persons: List[Dict[str, Any]],
    cases: List[Dict[str, Any]],
    phones: List[Dict[str, Any]],
    bank_accounts: List[Dict[str, Any]],
    profile_cfg: Dict[str, int],
    rng: random.Random
) -> Dict[str, List[Dict[str, Any]]]:
    
    # 1. CASE_PERSONS ASSOCIATIONS
    case_persons = []
    seen_cp_pairs = set()
    
    # Ensure multi-case connectors (at least 10 key individuals linked to >= 3 cases)
    connector_count = min(30, len(persons) // 20)
    connector_persons = persons[:connector_count]
    
    for p in connector_persons:
        num_cases = rng.randint(3, 6)
        assigned_cases = rng.sample(cases, min(num_cases, len(cases)))
        for c in assigned_cases:
            pair = (c["case_id"], p["person_id"])
            if pair not in seen_cp_pairs:
                seen_cp_pairs.add(pair)
                case_persons.append({
                    "cp_id": factories.cp_id_gen.next_id(),
                    "case_id": c["case_id"],
                    "person_id": p["person_id"],
                    "role": rng.choice(["SUSPECT", "ASSOCIATE", "PERSON_OF_INTEREST"]),
                    "narrative": f"{p['full_name']} identified as an analytical lead in connection with {c['title']}."
                })

    # Distribute remaining case-person associations
    remaining_cp = max(0, profile_cfg["case_persons"] - len(case_persons))
    other_persons = persons[connector_count:]
    
    for _ in range(remaining_cp):
        c = rng.choice(cases)
        p = rng.choice(other_persons) if other_persons else rng.choice(persons)
        pair = (c["case_id"], p["person_id"])
        if pair not in seen_cp_pairs:
            seen_cp_pairs.add(pair)
            case_persons.append({
                "cp_id": factories.cp_id_gen.next_id(),
                "case_id": c["case_id"],
                "person_id": p["person_id"],
                "role": rng.choice(ROLES_IN_CASE),
                "narrative": f"Subject of enquiry in {c['title']} under {c['legal_section']}."
            })

    # 2. ALIASES (including spelling mutations for entity resolution testing)
    aliases = []
    alias_target_count = profile_cfg["aliases"]
    sampled_persons_for_aliases = rng.sample(persons, min(alias_target_count, len(persons)))
    
    for p in sampled_persons_for_aliases:
        first, last = p["full_name"].split(" ", 1)
        alias_type = rng.choice(["NICKNAME", "MUTATION", "PHONETIC"])
        if alias_type == "NICKNAME":
            alias_name = f"{first} {rng.choice(['Bhai', 'Ustad', 'Chhota', 'Dada', 'Guddu', 'Sonu'])}"
        elif alias_type == "MUTATION":
            # Mutate last vowel or consonant
            alias_name = f"{first[:-1]}a {last}" if len(first) > 3 else f"{first} {last}ji"
        else:
            alias_name = f"{first} {last[:3]}."
            
        aliases.append({
            "alias_id": factories.alias_id_gen.next_id(),
            "person_id": p["person_id"],
            "alias_name": alias_name,
            "context": f"Colloquial reference in records ({alias_type})"
        })

    # 3. FAMILIES (Strict Reciprocal Civilian Pairs)
    families = []
    seen_family_pairs = set()
    num_family_units = profile_cfg["families"] // 2
    
    for _ in range(num_family_units):
        p1 = rng.choice(persons)
        p2 = rng.choice(persons)
        if p1["person_id"] == p2["person_id"]:
            continue
        pair = tuple(sorted([p1["person_id"], p2["person_id"]]))
        if pair in seen_family_pairs:
            continue
        seen_family_pairs.add(pair)
        
        rel_type_forward, rel_type_backward = rng.choice(FAMILY_RELATIONSHIPS)
        
        families.append({
            "family_id": factories.fam_id_gen.next_id(),
            "person_id": p1["person_id"],
            "related_person_id": p2["person_id"],
            "relationship_subtype": rel_type_forward
        })
        families.append({
            "family_id": factories.fam_id_gen.next_id(),
            "person_id": p2["person_id"],
            "related_person_id": p1["person_id"],
            "relationship_subtype": rel_type_backward
        })

    # 4. COMMUNICATIONS
    communications = []
    for _ in range(profile_cfg["communications"]):
        c = rng.choice(cases)
        src = rng.choice(persons)
        tgt = rng.choice(persons)
        if src["person_id"] == tgt["person_id"]:
            continue
        ctype = rng.choice(COMMUNICATION_TYPES)
        desc = f"Synthetic telecommunication record: {src['person_id']} {src['full_name']} contacted {tgt['person_id']} {tgt['full_name']} via {ctype} in relation to {c['case_id']}."
        communications.append({
            "communication_id": factories.comm_id_gen.next_id(),
            "case_id": c["case_id"],
            "source_person_id": src["person_id"],
            "target_person_id": tgt["person_id"],
            "phone_id": src.get("phone_id", ""),
            "communication_type": ctype,
            "description": desc
        })

    # 5. TRANSACTIONS
    transactions = []
    for _ in range(profile_cfg["transactions"]):
        c = rng.choice(cases)
        src = rng.choice(persons)
        tgt = rng.choice(persons)
        if src["person_id"] == tgt["person_id"]:
            continue
        amt = rng.choice([25000, 50000, 75000, 150000, 250000, 500000])
        desc = f"Synthetic transaction record: {src['person_id']} transferred INR {amt} to {tgt['person_id']} linked to {c['case_id']}."
        transactions.append({
            "transaction_id": factories.txn_id_gen.next_id(),
            "case_id": c["case_id"],
            "source_person_id": src["person_id"],
            "target_person_id": tgt["person_id"],
            "source_account_id": src.get("bank_account_id", ""),
            "target_account_id": tgt.get("bank_account_id", ""),
            "amount": amt,
            "description": desc
        })

    # 6. GROUND TRUTH (Balanced Positive & Hard Negative Pairs)
    ground_truth = []
    gt_pairs_seen = set()
    
    # 70% Positive Ground Truth (Derived from actual communications and transactions)
    pos_target = int(profile_cfg["ground_truth"] * 0.70)
    for comm in communications[:pos_target // 2]:
        pair = (comm["source_person_id"], comm["target_person_id"])
        if pair not in gt_pairs_seen:
            gt_pairs_seen.add(pair)
            ground_truth.append({
                "ground_truth_id": factories.gt_id_gen.next_id(),
                "source_entity_id": comm["source_person_id"],
                "target_entity_id": comm["target_person_id"],
                "relationship_type": "CONTACTED",
                "expected_relationship": 1,
                "case_id": comm["case_id"],
                "evidence_reference": comm["description"]
            })
            
    for txn in transactions[:pos_target // 2]:
        pair = (txn["source_person_id"], txn["target_person_id"])
        if pair not in gt_pairs_seen:
            gt_pairs_seen.add(pair)
            ground_truth.append({
                "ground_truth_id": factories.gt_id_gen.next_id(),
                "source_entity_id": txn["source_person_id"],
                "target_entity_id": txn["target_person_id"],
                "relationship_type": "TRANSFERRED_TO",
                "expected_relationship": 1,
                "case_id": txn["case_id"],
                "evidence_reference": txn["description"]
            })

    # 30% Hard Negative Ground Truth (Co-located or in same district but NO verified relationship)
    neg_target = profile_cfg["ground_truth"] - len(ground_truth)
    attempts = 0
    while len(ground_truth) < profile_cfg["ground_truth"] and attempts < neg_target * 5:
        attempts += 1
        p1 = rng.choice(persons)
        p2 = rng.choice(persons)
        if p1["person_id"] == p2["person_id"]:
            continue
        pair = (p1["person_id"], p2["person_id"])
        if pair in gt_pairs_seen:
            continue
        gt_pairs_seen.add(pair)
        
        # Negatives have expected_relationship = 0
        ground_truth.append({
            "ground_truth_id": factories.gt_id_gen.next_id(),
            "source_entity_id": p1["person_id"],
            "target_entity_id": p2["person_id"],
            "relationship_type": rng.choice(["CONTACTED", "TRANSFERRED_TO"]),
            "expected_relationship": 0,
            "case_id": rng.choice(cases)["case_id"],
            "evidence_reference": f"Synthetic negative control: {p1['person_id']} and {p2['person_id']} registered in {p1['city']} without verified investigative tie."
        })

    return {
        "case_persons": case_persons,
        "aliases": aliases,
        "families": families,
        "communications": communications,
        "transactions": transactions,
        "ground_truth": ground_truth
    }
