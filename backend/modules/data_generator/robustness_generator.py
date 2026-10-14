"""
robustness_generator.py
=======================
Generates a dedicated 500-pair hard-negative and adversarial stress corpus
for Step 24 robustness evaluation.
All outputs are strictly quarantined under:
backend/data/expanded/experiments/robustness/

Scenarios Covered (A through O):
A. Same surname, unrelated people
B. Same locality, unrelated people
C. Similar names, unrelated people
D. Shared case but no direct evidence (co-accused without operational link)
E. One communication only (e.g. wrong number / single contact)
F. One transaction only (e.g. isolated commercial sale)
G. High transaction volume but weak relationship evidence (e.g. retail invoice)
H. One-way communication vs bidirectional communication
I. Multi-case association without direct relationship evidence
J. One-channel evidence vs multi-channel evidence
K. Similar feature values for positive and negative pairs
L. Family relationship pairs (strictly non-operational kinship)
M. Cross-case hard negatives
N. Sparse-evidence cases
O. Conflicting evidence patterns
"""

import os
import sys
import csv
import json
import random
import pandas as pd
import numpy as np

# Ensure path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

ROBUSTNESS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/experiments/robustness'))
SMALL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/small'))

def generate_robustness_corpus(seed: int = 42) -> dict:
    os.makedirs(ROBUSTNESS_DIR, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)
    
    # 1. Load context from SMALL expanded dataset (read-only)
    persons_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "persons.csv"))
    cases_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "cases.csv"))
    case_persons_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "case_persons.csv"))
    families_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "families.csv"))
    
    persons = persons_df.to_dict('records')
    cases = cases_df.to_dict('records')
    person_ids = [p["person_id"] for p in persons]
    entities_map = {p["person_id"]: p["full_name"] for p in persons}
    
    # Pre-group persons by surname and locality
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
    # 250 POSITIVE OPERATIONAL EXAMPLES (Diverse topologies)
    # -------------------------------------------------------------
    # Positive pairs represent genuine operational collaboration with varying evidence depth
    used_pos_pairs = set()
    while len(used_pos_pairs) < 250:
        p1, p2 = random.sample(persons, 2)
        if (p1["person_id"], p2["person_id"]) in used_pos_pairs:
            continue
        used_pos_pairs.add((p1["person_id"], p2["person_id"]))
        
        c = random.choice(cases)
        cid = c["case_id"]
        
        # Associate both in the case
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": cid,
            "person_id": p1["person_id"],
            "role": "SUSPECT"
        })
        cp_counter += 1
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": cid,
            "person_id": p2["person_id"],
            "role": "SUSPECT"
        })
        cp_counter += 1
        
        # Add communications
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} regarding coordination.",
            "duration": random.randint(60, 300)
        })
        comm_counter += 1
        
        # Bidirectional for 60% of positives
        if random.random() < 0.60:
            comms_records.append({
                "comm_id": f"ROB-COMM-{comm_counter:04d}",
                "case_id": cid,
                "description": f"{p2['person_id']} contacted {p1['person_id']} to confirm receipt.",
                "duration": random.randint(45, 200)
            })
            comm_counter += 1
            
        # Financial transactions for 50% of positives
        if random.random() < 0.50:
            amt = round(random.uniform(5000, 75000), 2)
            txns_records.append({
                "txn_id": f"ROB-TXN-{txn_counter:04d}",
                "case_id": cid,
                "amount": amt,
                "description": f"{p1['person_id']} transferred {amt} INR to {p2['person_id']} for logistics."
            })
            txn_counter += 1
            
        pairs.append({
            "pair_id": f"ROB-PAIR-{pair_counter:04d}",
            "source_entity_id": p1["person_id"],
            "target_entity_id": p2["person_id"],
            "relationship_type": "CONTACTED" if random.random() < 0.7 else "TRANSFERRED_TO",
            "case_id": cid,
            "evidence_reference": f"{p1['person_id']} contacted {p2['person_id']} repeatedly under {cid}.",
            "expected_relationship": 1,
            "scenario": "OPERATIONAL_POSITIVE"
        })
        pair_counter += 1

    # -------------------------------------------------------------
    # 250 HARD NEGATIVE EXAMPLES (Scenarios A through O)
    # -------------------------------------------------------------
    hard_negatives = []
    
    # Scenario A: Same surname, unrelated individuals (20 pairs)
    for surname, group in surname_groups.items():
        if len(group) >= 2 and len([p for p in hard_negatives if p["scenario"] == "SCENARIO_A_SAME_SURNAME"]) < 20:
            p1, p2 = group[0], group[1]
            c = random.choice(cases)
            hard_negatives.append({
                "source": p1["person_id"], "target": p2["person_id"],
                "case_id": c["case_id"], "evidence": "Both individuals share surname in area records.",
                "scenario": "SCENARIO_A_SAME_SURNAME"
            })
            
    # Scenario B: Same locality, unrelated individuals (20 pairs)
    for loc, group in locality_groups.items():
        if len(group) >= 2 and len([p for p in hard_negatives if p["scenario"] == "SCENARIO_B_SAME_LOCALITY"]) < 20:
            p1, p2 = group[0], group[1]
            c = random.choice(cases)
            hard_negatives.append({
                "source": p1["person_id"], "target": p2["person_id"],
                "case_id": c["case_id"], "evidence": f"Both individuals registered residing in {loc}.",
                "scenario": "SCENARIO_B_SAME_LOCALITY"
            })

    # Scenario C: Similar names, unrelated individuals (15 pairs)
    for i in range(len(persons) - 1):
        if len([p for p in hard_negatives if p["scenario"] == "SCENARIO_C_SIMILAR_NAME"]) >= 15:
            break
        p1 = persons[i]
        p2 = persons[i + 1]
        sim = len(set(p1["full_name"]).intersection(set(p2["full_name"]))) / max(len(p1["full_name"]), 1)
        if sim > 0.7:
            c = random.choice(cases)
            hard_negatives.append({
                "source": p1["person_id"], "target": p2["person_id"],
                "case_id": c["case_id"], "evidence": "Phonetic and character resemblance in civil registry.",
                "scenario": "SCENARIO_C_SIMILAR_NAME"
            })

    # Scenario D: Co-accused in shared case with NO direct operational link (30 pairs)
    # Both appear in case_persons, giving case_cooccurrence_count >= 1, but expected_relationship = 0!
    for _ in range(30):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        # Associate both in the same case
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": cid,
            "person_id": p1["person_id"],
            "role": "WITNESS"
        })
        cp_counter += 1
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": cid,
            "person_id": p2["person_id"],
            "role": "SUSPECT"
        })
        cp_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": f"Named independently in investigation {cid}; witness and accused.",
            "scenario": "SCENARIO_D_SHARED_CASE_NO_DIRECT_LINK"
        })

    # Scenario E: One isolated communication only (wrong number / misdial) (20 pairs)
    for _ in range(20):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} once (misdial / wrong number).",
            "duration": 4
        })
        comm_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Single 4-second misdial registered; no operational relationship.",
            "scenario": "SCENARIO_E_ONE_COMM_MISDIAL"
        })

    # Scenario F: One isolated financial transaction (retail purchase) (20 pairs)
    for _ in range(20):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        txns_records.append({
            "txn_id": f"ROB-TXN-{txn_counter:04d}",
            "case_id": cid,
            "amount": 250.0,
            "description": f"{p1['person_id']} transferred 250.0 INR to {p2['person_id']} for retail item."
        })
        txn_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Single retail merchant payment; no syndicate linkage.",
            "scenario": "SCENARIO_F_ONE_TXN_RETAIL"
        })

    # Scenario G: High transaction volume but commercial/vendor invoice (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        txns_records.append({
            "txn_id": f"ROB-TXN-{txn_counter:04d}",
            "case_id": cid,
            "amount": 150000.0,
            "description": f"{p1['person_id']} transferred 150000.0 INR to {p2['person_id']} for building hardware supplier invoice."
        })
        txn_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Commercial invoice payment to registered building vendor; no conspiracy.",
            "scenario": "SCENARIO_G_HIGH_VOLUME_COMMERCIAL"
        })

    # Scenario H: One-way communication without reply (cold spam/outreach) (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} unprompted; unanswered incoming call.",
            "duration": 0
        })
        comm_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Unsolicited one-way unanswered call; no mutual conspiracy.",
            "scenario": "SCENARIO_H_ONE_WAY_UNANSWERED"
        })

    # Scenario I: Multi-case appearances without direct link (informant/official) (20 pairs)
    for _ in range(20):
        p1, p2 = random.sample(persons, 2)
        # Associate p1 with 3 cases, p2 with 3 cases, overlapping in 2
        for k in range(2):
            cid = cases[k]["case_id"]
            cp_records.append({
                "cp_id": f"ROB-CP-{cp_counter:04d}",
                "case_id": cid,
                "person_id": p1["person_id"],
                "role": "CIVIL_COMPLAINANT"
            })
            cp_counter += 1
            cp_records.append({
                "cp_id": f"ROB-CP-{cp_counter:04d}",
                "case_id": cid,
                "person_id": p2["person_id"],
                "role": "SUSPECT"
            })
            cp_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cases[0]["case_id"],
            "evidence": "Civilian complainant appearing across multiple case registries; zero operational ties.",
            "scenario": "SCENARIO_I_MULTI_CASE_NO_DIRECT_LINK"
        })

    # Scenario J: One-channel evidence vs multi-channel (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} inquiring about apartment rent.",
            "duration": 18
        })
        comm_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Real estate enquiry call; non-conspiracy.",
            "scenario": "SCENARIO_J_SINGLE_CHANNEL_INQUIRY"
        })

    # Scenario K: Similar feature values for positive and negative pairs (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} regarding taxi service.",
            "duration": 45
        })
        comm_counter += 1
        txns_records.append({
            "txn_id": f"ROB-TXN-{txn_counter:04d}",
            "case_id": cid,
            "amount": 450.0,
            "description": f"{p1['person_id']} transferred 450.0 INR to {p2['person_id']} for cab fare."
        })
        txn_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid, "evidence": "Transportation booking and fare payment; commercial ride-hailing.",
            "scenario": "SCENARIO_K_TAXI_COMMERCIAL_FARE"
        })

    # Scenario L: Family relationship pairs (strictly civilian non-operational) (25 pairs)
    fam_rows = families_df.to_dict('records')
    for fam in fam_rows[:25]:
        p1_id = fam["person_id"]
        p2_id = fam["related_person_id"]
        c = random.choice(cases)
        hard_negatives.append({
            "source": p1_id, "target": p2_id,
            "case_id": c["case_id"],
            "evidence": f"Civilian family relationship ({fam.get('relationship_subtype', 'KIN')}); zero case involvement.",
            "scenario": "SCENARIO_L_FAMILY_NON_OPERATIONAL"
        })

    # Scenario M: Cross-case hard negatives (active in separate cases in same station) (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c1, c2 = random.sample(cases, 2)
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": c1["case_id"],
            "person_id": p1["person_id"],
            "role": "SUSPECT"
        })
        cp_counter += 1
        cp_records.append({
            "cp_id": f"ROB-CP-{cp_counter:04d}",
            "case_id": c2["case_id"],
            "person_id": p2["person_id"],
            "role": "SUSPECT"
        })
        cp_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": c1["case_id"],
            "evidence": f"Suspects arrested in separate distinct cases ({c1['case_id']}, {c2['case_id']}) under same division.",
            "scenario": "SCENARIO_M_CROSS_CASE_SEPARATE"
        })

    # Scenario N: Sparse-evidence cases (text-only mention without telecom/bank records) (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": c["case_id"],
            "evidence": "Mentioned as bystander in crowd at incident location.",
            "scenario": "SCENARIO_N_SPARSE_BYSTANDER"
        })

    # Scenario O: Conflicting evidence patterns (telecom log exists, but explicit clearance) (15 pairs)
    for _ in range(15):
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        cid = c["case_id"]
        comms_records.append({
            "comm_id": f"ROB-COMM-{comm_counter:04d}",
            "case_id": cid,
            "description": f"{p1['person_id']} contacted {p2['person_id']} regarding dispute.",
            "duration": 30
        })
        comm_counter += 1
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": cid,
            "evidence": "Investigator noted call was adversary dispute/hostile confrontation, not operational alliance.",
            "scenario": "SCENARIO_O_CONFLICTING_ADVERSARY"
        })

    # Fill any remaining until exactly 250 hard negatives
    while len(hard_negatives) < 250:
        p1, p2 = random.sample(persons, 2)
        c = random.choice(cases)
        hard_negatives.append({
            "source": p1["person_id"], "target": p2["person_id"],
            "case_id": c["case_id"],
            "evidence": "General district inquiry; no verified relationship.",
            "scenario": "SCENARIO_MISC_NEGATIVE"
        })
        
    for neg in hard_negatives[:250]:
        pairs.append({
            "pair_id": f"ROB-PAIR-{pair_counter:04d}",
            "source_entity_id": neg["source"],
            "target_entity_id": neg["target"],
            "relationship_type": "RELATED_TO" if "FAMILY" in neg["scenario"] else "CONTACTED",
            "case_id": neg["case_id"],
            "evidence_reference": neg["evidence"],
            "expected_relationship": 0,
            "scenario": neg["scenario"]
        })
        pair_counter += 1
        
    # Write CSV files into backend/data/expanded/experiments/robustness/
    gt_path = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    pd.DataFrame(pairs).to_csv(gt_path, index=False)
    
    comms_path = os.path.join(ROBUSTNESS_DIR, "robustness_comms.csv")
    pd.DataFrame(comms_records).to_csv(comms_path, index=False)
    
    txns_path = os.path.join(ROBUSTNESS_DIR, "robustness_txns.csv")
    pd.DataFrame(txns_records).to_csv(txns_path, index=False)
    
    cp_path = os.path.join(ROBUSTNESS_DIR, "robustness_case_persons.csv")
    pd.DataFrame(cp_records).to_csv(cp_path, index=False)
    
    # Save metadata
    meta = {
        "dataset_name": "STEP_24_ROBUSTNESS_CORPUS",
        "seed": seed,
        "total_pairs": len(pairs),
        "positive_pairs": sum(1 for p in pairs if p["expected_relationship"] == 1),
        "negative_pairs": sum(1 for p in pairs if p["expected_relationship"] == 0),
        "hard_negative_scenarios": {
            s: sum(1 for p in pairs if p["scenario"] == s)
            for s in set(p["scenario"] for p in pairs)
        }
    }
    meta_path = os.path.join(ROBUSTNESS_DIR, "robustness_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    return meta

if __name__ == "__main__":
    meta = generate_robustness_corpus(seed=42)
    print("Robustness corpus generated successfully:")
    print(json.dumps(meta, indent=2))
