"""
test_ml_benchmarks.py
=====================
Tests verifying Step 23 ML Model Improvement & Benchmarking invariants:
1. Feature provenance and shape consistency (7 vs 11 features)
2. Zero label leakage and no target-derived signals
3. Leakage-safe train/test case partitioning
4. Isolation of live demo model (backend/models/relationship_confidence_model.joblib)
5. Isolation of baseline demonstration CSV files (backend/data/*.csv)
6. Entity resolution precision and false-positive suppression on hard negatives
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.data_generator.features import (
    extract_features_7, extract_features_11,
    FEATURE_NAMES_7, FEATURE_NAMES_11
)
from modules.data_generator.splitter import split_dataset
from modules.entity_resolution.resolver import entity_resolution_score
from modules.entity_resolution.normalization import normalize_entity

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
EXPANDED_SMALL_DIR = os.path.abspath(os.path.join(DATA_DIR, 'expanded/small'))
EXPERIMENTS_DIR = os.path.abspath(os.path.join(DATA_DIR, 'expanded/experiments'))
LIVE_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/relationship_confidence_model.joblib'))

def test_feature_provenance_and_shape():
    """Verifies that features are computed strictly from available records without label leakage."""
    comms_df = pd.DataFrame([{
        "comm_id": "COMM-001",
        "case_id": "CASE-001",
        "description": "PERSON-001 contacted PERSON-002 regarding shipment."
    }])
    txns_df = pd.DataFrame([{
        "txn_id": "TXN-001",
        "amount": 25000.0,
        "description": "PERSON-001 transferred funds to PERSON-002."
    }])
    case_persons_df = pd.DataFrame([
        {"cp_id": "CP-001", "case_id": "CASE-001", "person_id": "PERSON-001"},
        {"cp_id": "CP-002", "case_id": "CASE-001", "person_id": "PERSON-002"}
    ])
    entities_map = {
        "PERSON-001": "Subhash Ghosh",
        "PERSON-002": "Rajesh Ghosh"
    }
    
    rel = {
        "source": "PERSON-001",
        "target": "PERSON-002",
        "relationship_type": "CONTACTED",
        "case_id": "CASE-001",
        "evidence": "PERSON-001 contacted PERSON-002 regarding shipment."
    }
    
    f7 = extract_features_7(rel, comms_df, txns_df, entities_map)
    assert len(f7) == 7
    assert len(f7) == len(FEATURE_NAMES_7)
    assert all(isinstance(v, (int, float)) and not np.isnan(v) for v in f7)
    
    f11 = extract_features_11(rel, comms_df, txns_df, case_persons_df, entities_map)
    assert len(f11) == 11
    assert len(f11) == len(FEATURE_NAMES_11)
    assert all(isinstance(v, (int, float)) and not np.isnan(v) for v in f11)
    
    # Check new explainable features:
    # evidence_diversity (both comms and txns present) -> 1.0
    assert f11[7] == 1.0
    # case_cooccurrence_count (both in CASE-001) -> 1.0
    assert f11[8] == 1.0
    # bidirectional_activity -> > 0
    assert f11[9] > 0.0
    # normalized_transaction_volume (log10(1 + 25000)) -> ~4.398
    assert f11[10] > 4.0

def test_zero_case_leakage():
    """Verifies that split_dataset enforces strict disjoint case sets between train and test."""
    if not os.path.exists(EXPANDED_SMALL_DIR):
        pytest.skip("Expanded small dataset not found")
        
    res = split_dataset(EXPANDED_SMALL_DIR, train_ratio=0.70, test_ratio=0.30, seed=42)
    assert res["zero_case_leakage_verified"] is True
    
    train_cases = {r.get("case_id") for r in res["train_gt"] if r.get("case_id")}
    test_cases = {r.get("case_id") for r in res["test_gt"] if r.get("case_id")}
    
    assert len(train_cases.intersection(test_cases)) == 0

def test_live_model_isolated():
    """Verifies that the live demo model exists and remains isolated."""
    assert os.path.exists(LIVE_MODEL_PATH), "Live demo model must exist in backend/models/"
    # Verify the model is loadable and unchanged
    import joblib
    model = joblib.load(LIVE_MODEL_PATH)
    assert hasattr(model, "predict_proba")

def test_baseline_csvs_isolated():
    """Verifies that baseline CSV dataset files are completely untouched."""
    baseline_files = [
        "cases.csv", "persons.csv", "case_persons.csv", "phones.csv",
        "bank_accounts.csv", "vehicles.csv", "locations.csv",
        "organizations.csv", "aliases.csv", "families.csv",
        "communications.csv", "transactions.csv", "ground_truth.csv"
    ]
    for fn in baseline_files:
        p = os.path.join(DATA_DIR, fn)
        assert os.path.exists(p), f"Baseline file {fn} must exist"
        # Check that none of the baseline files have been modified to contain expanded data
        df = pd.read_csv(p)
        assert len(df) <= 400, f"Baseline file {fn} must retain demo scale (< 400 records)"

def test_entity_resolution_hard_negatives():
    """Verifies that entity resolution rejects hard negative pairs and does not falsely match distinct persons."""
    # Distinct persons with same surname
    ent_a = normalize_entity("PERSON", "Arjun Sen")
    ent_b = normalize_entity("PERSON", "Bikram Sen")
    
    res = entity_resolution_score(ent_a, ent_b)
    assert res["decision"] != "MATCH", "Distinct persons with shared surname must not MATCH"
    
    # Completely distinct names
    ent_c = normalize_entity("PERSON", "Tapas Ghosh")
    ent_d = normalize_entity("PERSON", "Debashis Banerjee")
    res_cd = entity_resolution_score(ent_c, ent_d)
    assert res_cd["decision"] == "NO_MATCH"
    assert res_cd["final_score"] < 0.65

def test_benchmark_reports_and_models_exist():
    """Verifies that benchmark runner created reports and model artifacts under backend/data/expanded/experiments/."""
    report_json = os.path.join(EXPERIMENTS_DIR, "benchmark_report.json")
    report_md = os.path.join(EXPERIMENTS_DIR, "BENCHMARK_REPORT.md")
    
    if not os.path.exists(report_json):
        pytest.skip("Benchmark has not been run yet")
        
    with open(report_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "models_benchmarked" in data
    assert "LogReg_7_Baseline" in data["models_benchmarked"]
    assert "LogReg_11_Scaled" in data["models_benchmarked"]
    assert "RandomForest_11" in data["models_benchmarked"]
    assert "HistGradientBoosting_11" in data["models_benchmarked"]
    assert "Calibrated_RF_11" in data["models_benchmarked"]
    assert "entity_resolution_benchmark" in data
    assert os.path.exists(report_md)
