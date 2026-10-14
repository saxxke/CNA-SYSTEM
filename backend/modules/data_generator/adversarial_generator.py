"""
adversarial_generator.py
========================
Generates a 1,200-pair adversarial training corpus with overlapping feature distributions
for Step 25.
Outputs are quarantined strictly under:
backend/data/expanded/experiments/adversarial_training/

Key Invariants:
1. Positives and negatives have deliberately overlapping feature distributions:
   - Hard negatives have case co-occurrences, multiple communications, financial transactions,
     bidirectional contact, high transaction volumes, shared localities, shared surnames, etc.
   - Genuine positives include sparse evidence, single-channel records, lower transaction volumes,
     and one-way communications.
2. Strict disjoint case-level partitioning:
   - Train (70%, 840 pairs)
   - Validation (15%, 180 pairs)
   - Test (15%, 180 pairs)
   Zero case overlap between train, val, and test.
"""

import os
import sys
import json
import random
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple

# Project imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from modules.data_generator.features import extract_features_11, FEATURE_NAMES_11

ADV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/experiments/adversarial_training'))
SMALL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/small'))

def generate_adversarial_corpus(seed: int = 42) -> Dict[str, Any]:
    os.makedirs(ADV_DIR, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)
    
    # 1. Load context from SMALL expanded dataset (read-only)
    persons_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "persons.csv"))
    cases_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "cases.csv"))
    families_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "families.csv"))
    
    persons = persons_df.to_dict('records')
    cases = cases_df.to_dict('records')
    entities_map = {p["person_id"]: p["full_name"] for p in persons}
    
    # Group persons by surname and locality
    surname_groups = {}
    locality_groups = {}
    for p in persons:
        parts = p["full_name"].strip().split()
        surname = parts[-1] if len(parts) > 1 else parts[0]
        surname_groups.setdefault(surname, []).append(p)
        loc = p.get("locality", "Unknown")
        locality_groups.setdefault(loc, []).append(p)
        
    pairs = []
    comms_records = []
    txns_records = []
    cp_records = []
    
    comm_counter = 1
    txn_counter = 1
    cp_counter = 1
    pair_counter = 1
    
    # -------------------------------------------------------------
    # 1. 600 POSITIVE OPERATIONAL EXAMPLES
    # -------------------------------------------------------------
    # Sub-type A: Multi-channel standard operational pairs (350 pairs)
    for _ in range(350):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        
        cp_records.append({
            "cp_id": f"ADV-CP-{cp_counter:04d}",
            "case_id": cid, "person_id": p1["person_id"], "role": "SUSPECT"
        })
        cp_counter += 1
        cp_records.append({
            "cp_id": f"ADV-CP-{cp_counter:04d}",
            "case_id": cid, "person_id": p2["person_id"], "role": "SUSPECT"
        })
        cp_counter += 1
        
        comms_records.append({
            "comm_id": f"ADV-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} regarding operational logistics.",
            "duration": random.randint(50, 300)
        })
        comm_counter += 1
        
        if random.random() < 0.70:
            comms_records.append({
                "comm_id": f"ADV-COMM-{comm_counter:04d}",
                "case_id": cid,
                "description": f"{p2['person_id']} contacted {p1['person_id']} confirming pickup.",
                "duration": random.randint(40, 180)
            })
            comm_counter += 1
            
        amt = round(random.uniform(5000, 65000), 2)
        txns_records.append({
            "txn_id": f"ADV-TXN-{txn_counter:04d}",
            "case_id": cid, "amount": amt,
            "description": f"{p1['person_id']} transferred {amt} INR to {p2['person_id']} for contraband."
        })
        txn_counter += 1
        
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED", "case_id": cid,
            "evidence_reference": f"{p1['person_id']} coordinated with {p2['person_id']} under {cid}.",
            "expected_relationship": 1, "scenario": "POS_STANDARD_MULTI_CHANNEL"
        })
        pair_counter += 1

    # Sub-type B: Sparse one-channel operational pairs (150 pairs: e.g. text evidence only or single call, NO txns, case_cooccurrence = 0 or 1)
    for _ in range(150):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        
        # 50% have case association, 50% are covert across external cases
        if random.random() < 0.50:
            cp_records.append({
                "cp_id": f"ADV-CP-{cp_counter:04d}",
                "case_id": cid, "person_id": p1["person_id"], "role": "SUSPECT"
            })
            cp_counter += 1
            cp_records.append({
                "cp_id": f"ADV-CP-{cp_counter:04d}",
                "case_id": cid, "person_id": p2["person_id"], "role": "SUSPECT"
            })
            cp_counter += 1
            
        comms_records.append({
            "comm_id": f"ADV-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} via encrypted relay.",
            "duration": random.randint(15, 60)
        })
        comm_counter += 1
        
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED", "case_id": cid,
            "evidence_reference": f"Interception notes confirm {p1['person_id']} contacted {p2['person_id']}.",
            "expected_relationship": 1, "scenario": "POS_SPARSE_ONE_CHANNEL"
        })
        pair_counter += 1

    # Sub-type C: Low transaction volume or Hawala settlement (100 pairs)
    for _ in range(100):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        
        amt = round(random.uniform(500, 3000), 2)
        txns_records.append({
            "txn_id": f"ADV-TXN-{txn_counter:04d}",
            "case_id": cid, "amount": amt,
            "description": f"{p1['person_id']} transferred {amt} INR token settlement to {p2['person_id']}."
        })
        txn_counter += 1
        
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "TRANSFERRED_TO", "case_id": cid,
            "evidence_reference": f"Token remittance payment from {p1['person_id']} to {p2['person_id']}.",
            "expected_relationship": 1, "scenario": "POS_LOW_VOLUME_HAWALA"
        })
        pair_counter += 1

    # -------------------------------------------------------------
    # 2. 600 HARD NEGATIVE OPERATIONAL EXAMPLES (With high feature overlap)
    # -------------------------------------------------------------
    
    # Sub-type A: Co-accused/witnesses in shared cases without operational links (150 pairs)
    # Both appear in case_persons -> case_cooccurrence_count >= 1, but expected_relationship = 0!
    for _ in range(150):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        cp_records.append({
            "cp_id": f"ADV-CP-{cp_counter:04d}",
            "case_id": cid, "person_id": p1["person_id"], "role": "WITNESS"
        })
        cp_counter += 1
        cp_records.append({
            "cp_id": f"ADV-CP-{cp_counter:04d}",
            "case_id": cid, "person_id": p2["person_id"], "role": "SUSPECT"
        })
        cp_counter += 1
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED", "case_id": cid,
            "evidence_reference": f"Co-named in investigation {cid}; witness and accused, no operational nexus.",
            "expected_relationship": 0, "scenario": "NEG_CO_ACCUSED_NO_NEXUS"
        })
        pair_counter += 1

    # Sub-type B: High-volume commercial supplier payments (75 pairs)
    # high transaction volume + transactions exist, but expected_relationship = 0!
    for _ in range(75):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        amt = round(random.uniform(40000, 200000), 2)
        txns_records.append({
            "txn_id": f"ADV-TXN-{txn_counter:04d}",
            "case_id": cid, "amount": amt,
            "description": f"{p1['person_id']} transferred {amt} INR to {p2['person_id']} for verified supplier invoice."
        })
        txn_counter += 1
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "TRANSFERRED_TO", "case_id": cid,
            "evidence_reference": f"Commercial hardware vendor invoice payment of {amt} INR under {cid}.",
            "expected_relationship": 0, "scenario": "NEG_HIGH_VOLUME_COMMERCIAL"
        })
        pair_counter += 1

    # Sub-type C: Multi-case civilian complainants / officials (75 pairs)
    # Associated with 2 cases together -> case_cooccurrence_count >= 2, but expected_relationship = 0!
    for _ in range(75):
        p1, p2 = random.sample(persons, 2)
        c1, c2 = random.sample(cases, 2)
        for cid in [c1["case_id"], c2["case_id"]]:
            cp_records.append({
                "cp_id": f"ADV-CP-{cp_counter:04d}",
                "case_id": cid, "person_id": p1["person_id"], "role": "CIVIL_COMPLAINANT"
            })
            cp_counter += 1
            cp_records.append({
                "cp_id": f"ADV-CP-{cp_counter:04d}",
                "case_id": cid, "person_id": p2["person_id"], "role": "SUSPECT"
            })
            cp_counter += 1
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED", "case_id": c1["case_id"],
            "evidence_reference": f"Civilian complainant and accused present across multiple FIRs ({c1['case_id']}, {c2['case_id']}).",
            "expected_relationship": 0, "scenario": "NEG_MULTI_CASE_CIVILIAN"
        })
        pair_counter += 1

    # Sub-type D: Bidirectional ordinary/adversary communications (75 pairs)
    # Bidirectional communication exists, but expected_relationship = 0!
    for _ in range(75):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ADV-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} demanding return of personal property.",
            "duration": 45
        })
        comm_counter += 1
        comms_records.append({
            "comm_id": f"ADV-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p2['person_id']} contacted {p1['person_id']} rejecting demand in heated dispute.",
            "duration": 50
        })
        comm_counter += 1
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED", "case_id": cid,
            "evidence_reference": "Heated civil dispute confrontation; adversary relationship, zero operational syndicate alliance.",
            "expected_relationship": 0, "scenario": "NEG_BIDIRECTIONAL_DISPUTE"
        })
        pair_counter += 1

    # Sub-type E: Shared locality & surname pairs (75 pairs)
    # High entity similarity or same locality records, but expected_relationship = 0!
    count_sn = 0
    for surname, group in surname_groups.items():
        if len(group) >= 2 and count_sn < 75:
            p1, p2 = group[0], group[1]
            c = random.choice(cases)
            pairs.append({
                "pair_id": f"ADV-PAIR-{pair_counter:04d}",
                "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
                "relationship_type": "CONTACTED", "case_id": c["case_id"],
                "evidence_reference": f"Residents sharing surname {surname} in municipal rolls; unrelated.",
                "expected_relationship": 0, "scenario": "NEG_SHARED_SURNAME_LOCALITY"
            })
            pair_counter += 1
            count_sn += 1

    # Sub-type F: Civilian family kinship pairs (50 pairs)
    # Explicit kinship in families.csv -> MUST receive expected_relationship = 0 for operational graph!
    fam_rows = families_df.to_dict('records')
    for fam in fam_rows[:50]:
        c = random.choice(cases)
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": fam["person_id"], "target_entity_id": fam["related_person_id"],
            "relationship_type": "RELATED_TO", "case_id": c["case_id"],
            "evidence_reference": f"Civilian family member ({fam.get('relationship_subtype', 'KIN')}); strictly non-operational.",
            "expected_relationship": 0, "scenario": "NEG_CIVILIAN_KINSHIP"
        })
        pair_counter += 1

    # Sub-type G: Taxi / retail payments & misdials (fill remaining to reach exactly 600 negatives)
    while len(pairs) < 1200:
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        txns_records.append({
            "txn_id": f"ADV-TXN-{txn_counter:04d}",
            "case_id": cid, "amount": 350.0,
            "description": f"{p1['person_id']} transferred 350.0 INR to {p2['person_id']} for taxi booking."
        })
        txn_counter += 1
        pairs.append({
            "pair_id": f"ADV-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"], "target_entity_id": p2["person_id"],
            "relationship_type": "TRANSFERRED_TO", "case_id": cid,
            "evidence_reference": "Cab fare digital transaction; non-operational commercial ride.",
            "expected_relationship": 0, "scenario": "NEG_COMMERCIAL_TAXI_RETAIL"
        })
        pair_counter += 1

    # -------------------------------------------------------------
    # 3. DISJOINT CASE-LEVEL TRAIN / VAL / TEST PARTITION (70/15/15)
    # -------------------------------------------------------------
    all_cases = list(set(p["case_id"] for p in pairs))
    random.shuffle(all_cases)
    
    n_cases = len(all_cases)
    n_tr_cases = int(n_cases * 0.70)
    n_val_cases = int(n_cases * 0.15)
    
    train_case_set = set(all_cases[:n_tr_cases])
    val_case_set = set(all_cases[n_tr_cases:n_tr_cases + n_val_cases])
    test_case_set = set(all_cases[n_tr_cases + n_val_cases:])
    
    # Assert zero case leakage
    assert len(train_case_set.intersection(val_case_set)) == 0
    assert len(train_case_set.intersection(test_case_set)) == 0
    assert len(val_case_set.intersection(test_case_set)) == 0
    
    train_pairs, val_pairs, test_pairs = [], [], []
    for p in pairs:
        cid = p["case_id"]
        if cid in train_case_set:
            p["split"] = "TRAIN"
            train_pairs.append(p)
        elif cid in val_case_set:
            p["split"] = "VAL"
            val_pairs.append(p)
        else:
            p["split"] = "TEST"
            test_pairs.append(p)
            
    # Save CSV files into backend/data/expanded/experiments/adversarial_training/
    gt_path = os.path.join(ADV_DIR, "adversarial_ground_truth.csv")
    pd.DataFrame(pairs).to_csv(gt_path, index=False)
    
    comms_path = os.path.join(ADV_DIR, "adversarial_comms.csv")
    pd.DataFrame(comms_records).to_csv(comms_path, index=False)
    
    txns_path = os.path.join(ADV_DIR, "adversarial_txns.csv")
    pd.DataFrame(txns_records).to_csv(txns_path, index=False)
    
    cp_path = os.path.join(ADV_DIR, "adversarial_case_persons.csv")
    pd.DataFrame(cp_records).to_csv(cp_path, index=False)
    
    # Compute feature overlap statistics
    # Combine with SMALL base tables for full feature extraction
    base_comms = pd.read_csv(os.path.join(SMALL_DATA_DIR, "communications.csv"))
    base_txns = pd.read_csv(os.path.join(SMALL_DATA_DIR, "transactions.csv"))
    base_cp = pd.read_csv(os.path.join(SMALL_DATA_DIR, "case_persons.csv"))
    
    combined_comms = pd.concat([base_comms, pd.DataFrame(comms_records)], ignore_index=True)
    combined_txns = pd.concat([base_txns, pd.DataFrame(txns_records)], ignore_index=True)
    combined_cp = pd.concat([base_cp, pd.DataFrame(cp_records)], ignore_index=True)
    
    X_all = []
    y_all = []
    for p in pairs:
        rel = {
            "source": p["source_entity_id"], "target": p["target_entity_id"],
            "relationship_type": p["relationship_type"], "case_id": p["case_id"],
            "evidence": p["evidence_reference"]
        }
        X_all.append(extract_features_11(rel, combined_comms, combined_txns, combined_cp, entities_map))
        y_all.append(p["expected_relationship"])
    X_all = np.array(X_all)
    y_all = np.array(y_all)
    
    pos_mask = (y_all == 1)
    neg_mask = (y_all == 0)
    
    feature_overlap_stats = {}
    for idx, fname in enumerate(FEATURE_NAMES_11):
        pos_vals = X_all[pos_mask, idx]
        neg_vals = X_all[neg_mask, idx]
        
        # Calculate overlap (percentage of negatives whose values fall inside positive range)
        pos_min, pos_max = float(np.min(pos_vals)), float(np.max(pos_vals))
        neg_min, neg_max = float(np.min(neg_vals)), float(np.max(neg_vals))
        
        overlap_count = int(np.sum((neg_vals >= pos_min) & (neg_vals <= pos_max)))
        overlap_pct = round((overlap_count / len(neg_vals)) * 100.0, 2)
        
        feature_overlap_stats[fname] = {
            "pos_mean": round(float(np.mean(pos_vals)), 4),
            "pos_std": round(float(np.std(pos_vals)), 4),
            "pos_range": [round(pos_min, 4), round(pos_max, 4)],
            "neg_mean": round(float(np.mean(neg_vals)), 4),
            "neg_std": round(float(np.std(neg_vals)), 4),
            "neg_range": [round(neg_min, 4), round(neg_max, 4)],
            "negative_overlap_pct": overlap_pct
        }
        
    split_manifest = {
        "dataset_name": "STEP_25_ADVERSARIAL_TRAINING_CORPUS",
        "total_pairs": len(pairs),
        "total_positives": int(np.sum(y_all == 1)),
        "total_negatives": int(np.sum(y_all == 0)),
        "splits": {
            "train": {
                "pairs": len(train_pairs),
                "positives": sum(1 for p in train_pairs if p["expected_relationship"] == 1),
                "negatives": sum(1 for p in train_pairs if p["expected_relationship"] == 0),
                "cases": len(train_case_set)
            },
            "val": {
                "pairs": len(val_pairs),
                "positives": sum(1 for p in val_pairs if p["expected_relationship"] == 1),
                "negatives": sum(1 for p in val_pairs if p["expected_relationship"] == 0),
                "cases": len(val_case_set)
            },
            "test": {
                "pairs": len(test_pairs),
                "positives": sum(1 for p in test_pairs if p["expected_relationship"] == 1),
                "negatives": sum(1 for p in test_pairs if p["expected_relationship"] == 0),
                "cases": len(test_case_set)
            }
        },
        "zero_case_leakage_verified": True,
        "feature_overlap_statistics": feature_overlap_stats
    }
    
    manifest_path = os.path.join(ADV_DIR, "adversarial_split_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2)
        
    return split_manifest

if __name__ == "__main__":
    res = generate_adversarial_corpus(seed=42)
    print("Adversarial corpus generated successfully.")
    print(json.dumps(res, indent=2))
