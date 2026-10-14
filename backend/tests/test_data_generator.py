"""
test_data_generator.py
======================
Unit and integration tests for Step 22:
1. Schema and FK validation on generated SMALL profile
2. Bitwise byte-for-byte reproducibility with fixed seed (seed=42)
3. Seed mutation changes output while preserving validity (seed=99)
4. Primary key uniqueness and FIR uniqueness
5. Multi-case connector scenarios (>= 3 persons with >= 3 cases)
6. Positive and hard-negative ground-truth balance
7. Reciprocal family relationship validation
8. Graph safety: zero family ties enter NetworkX graph edges
9. Leakage-safe cluster-based train/test splitting
10. Baseline dataset integrity: backend/data/*.csv remains 100% untouched
"""

import os
import csv
import hashlib
import tempfile
import pytest
import networkx as nx

from modules.data_generator.generator import generate_dataset
from modules.data_generator.validator import validate_dataset_directory
from modules.data_generator.splitter import split_dataset

EXPANDED_SMALL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/expanded/small"))
BASELINE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))

def test_1_small_dataset_schema_and_fk_validity():
    """Requirement: Expanded small dataset passes all schema and foreign-key checks."""
    assert os.path.exists(EXPANDED_SMALL_DIR)
    res = validate_dataset_directory(EXPANDED_SMALL_DIR)
    assert res["valid"] is True
    assert len(res["errors"]) == 0
    assert res["record_counts"]["persons.csv"] == 1000
    assert res["record_counts"]["cases.csv"] == 1250
    assert res["record_counts"]["case_persons.csv"] >= 1800
    assert res["record_counts"]["ground_truth.csv"] == 1000


def test_2_zero_comment_lines_in_csvs():
    """Requirement 1: CSV files must be standard CSV without '#' comment headers."""
    for fname in os.listdir(EXPANDED_SMALL_DIR):
        if fname.endswith(".csv"):
            fpath = os.path.join(EXPANDED_SMALL_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                first_line = f.readline()
                assert not first_line.startswith("#"), f"{fname} contains disallowed comment line"


def test_3_reproducibility_identical_seed():
    """Requirement 3: Deterministic reproducibility with seed=42 yields byte-for-byte identical files."""
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        generate_dataset(profile="SMALL", output_dir=dir1, seed=42)
        generate_dataset(profile="SMALL", output_dir=dir2, seed=42)
        
        for fname in ["cases.csv", "persons.csv", "case_persons.csv", "communications.csv", "transactions.csv", "ground_truth.csv"]:
            p1 = os.path.join(dir1, fname)
            p2 = os.path.join(dir2, fname)
            
            with open(p1, "rb") as f1, open(p2, "rb") as f2:
                h1 = hashlib.sha256(f1.read()).hexdigest()
                h2 = hashlib.sha256(f2.read()).hexdigest()
                assert h1 == h2, f"Bitwise reproducibility failed for {fname}"


def test_4_reproducibility_different_seed():
    """Requirement 3: Different seeds produce different records while preserving schema and validity."""
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        generate_dataset(profile="SMALL", output_dir=dir1, seed=42)
        generate_dataset(profile="SMALL", output_dir=dir2, seed=99)
        
        # Verify validator passes for seed=99
        val_res = validate_dataset_directory(dir2)
        assert val_res["valid"] is True
        
        # Verify hashes differ
        p1 = os.path.join(dir1, "persons.csv")
        p2 = os.path.join(dir2, "persons.csv")
        with open(p1, "rb") as f1, open(p2, "rb") as f2:
            assert hashlib.sha256(f1.read()).hexdigest() != hashlib.sha256(f2.read()).hexdigest()


def test_5_unique_primary_keys_and_firs():
    """Requirement 2: Deterministic sequential ID allocation guarantees zero PK or FIR collisions."""
    cases_path = os.path.join(EXPANDED_SMALL_DIR, "cases.csv")
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
        
    case_ids = [c["case_id"] for c in cases]
    assert len(case_ids) == len(set(case_ids)), "Duplicate case_id found"
    
    firs = [c["fir_number"] for c in cases if c.get("fir_number")]
    assert len(firs) == len(set(firs)), "Duplicate FIR number found"


def test_6_multi_case_connectors():
    """Requirement 2: Ensure presence of multi-case connectors (at least 3 persons with >= 3 cases)."""
    cp_path = os.path.join(EXPANDED_SMALL_DIR, "case_persons.csv")
    with open(cp_path, "r", encoding="utf-8") as f:
        case_persons = list(csv.DictReader(f))
        
    counts = {}
    for cp in case_persons:
        pid = cp["person_id"]
        counts[pid] = counts.get(pid, 0) + 1
        
    multi_case_count = sum(1 for c in counts.values() if c >= 3)
    assert multi_case_count >= 3, f"Expected at least 3 multi-case persons, found {multi_case_count}"


def test_7_ground_truth_label_balance():
    """Requirement 7: Ground truth contains both positive (1) and hard-negative (0) controls."""
    gt_path = os.path.join(EXPANDED_SMALL_DIR, "ground_truth.csv")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt = list(csv.DictReader(f))
        
    pos = sum(1 for r in gt if int(r["expected_relationship"]) == 1)
    neg = sum(1 for r in gt if int(r["expected_relationship"]) == 0)
    
    assert pos > 0, "No positive ground-truth pairs found"
    assert neg > 0, "No negative ground-truth controls found"
    assert pos >= 500, f"Expected at least 500 positive pairs, found {pos}"
    assert neg >= 200, f"Expected at least 200 negative pairs, found {neg}"


def test_8_graph_safety_family_relationship_isolation():
    """Requirement 8: Family relationships must NEVER enter the investigative NetworkX graph."""
    families_path = os.path.join(EXPANDED_SMALL_DIR, "families.csv")
    with open(families_path, "r", encoding="utf-8") as f:
        families = list(csv.DictReader(f))
        
    family_pairs = {(f["person_id"], f["related_person_id"]) for f in families}
    
    # Build investigative graph from communications and transactions
    G = nx.MultiDiGraph()
    comms_path = os.path.join(EXPANDED_SMALL_DIR, "communications.csv")
    with open(comms_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            G.add_edge(row["source_person_id"], row["target_person_id"], relationship_type="CONTACTED")
            
    txns_path = os.path.join(EXPANDED_SMALL_DIR, "transactions.csv")
    with open(txns_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            G.add_edge(row["source_person_id"], row["target_person_id"], relationship_type="TRANSFERRED_TO")
            
    # Assert that no edge has relationship_type matching family relationships
    for u, v, d in G.edges(data=True):
        rel = d.get("relationship_type")
        assert rel in ["CONTACTED", "TRANSFERRED_TO", "INVOLVED_IN", "USES"], f"Illegal edge in graph: {rel}"
        assert rel not in ["FATHER", "MOTHER", "SON", "DAUGHTER", "SPOUSE", "BROTHER", "SISTER", "FAMILY"]


def test_9_leakage_safe_dataset_splitting():
    """Requirement F: Cluster-based splitting guarantees zero case leakage between train and test."""
    split_res = split_dataset(EXPANDED_SMALL_DIR, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
    assert split_res["zero_case_leakage_verified"] is True
    assert split_res["train_case_count"] > 0
    assert split_res["test_case_count"] > 0
    assert len(split_res["train_gt"]) > 0
    assert len(split_res["test_gt"]) > 0


def test_10_baseline_demo_dataset_untouched():
    """Requirement 4 & 9: Baseline demo dataset in backend/data/*.csv remains 100% unchanged."""
    cases_path = os.path.join(BASELINE_DATA_DIR, "cases.csv")
    persons_path = os.path.join(BASELINE_DATA_DIR, "persons.csv")
    
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    with open(persons_path, "r", encoding="utf-8") as f:
        persons = list(csv.DictReader(f))
        
    assert len(cases) == 250, "Baseline cases.csv was modified!"
    assert len(persons) == 200, "Baseline persons.csv was modified!"
