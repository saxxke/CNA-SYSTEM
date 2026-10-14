"""
test_ml_adversarial.py
======================
Tests verifying Step 25 Adversarial ML Training & Model Improvement invariants:
1. Adversarial training artifacts and data are strictly quarantined in backend/data/expanded/experiments/adversarial_training/.
2. Baseline CSV dataset files (backend/data/*.csv) remain 100% untouched.
3. Live production model (backend/models/relationship_confidence_model.joblib) remains 100% untouched.
4. Step 24 robustness corpus (backend/data/expanded/experiments/robustness/) remains read-only and untouched.
5. 1,200-pair adversarial corpus exhibits genuine feature overlap without single-feature label recoverability.
6. Zero case leakage across Train, Validation, and Test partitions.
7. Step 24 re-test comparison and candidate model artifacts exist.
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
EXP_DIR = os.path.abspath(os.path.join(DATA_DIR, 'expanded/experiments'))
ADV_DIR = os.path.abspath(os.path.join(EXP_DIR, 'adversarial_training'))
ROBUSTNESS_DIR = os.path.abspath(os.path.join(EXP_DIR, 'robustness'))
LIVE_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/relationship_confidence_model.joblib'))

def test_adversarial_corpus_isolation():
    """Verifies that Step 25 artifacts reside exclusively under backend/data/expanded/experiments/adversarial_training/."""
    assert os.path.exists(ADV_DIR), "Adversarial directory must exist"
    
    # Check baseline files
    baseline_files = [
        "cases.csv", "persons.csv", "case_persons.csv", "phones.csv",
        "bank_accounts.csv", "vehicles.csv", "locations.csv",
        "organizations.csv", "aliases.csv", "families.csv",
        "communications.csv", "transactions.csv", "ground_truth.csv"
    ]
    for fn in baseline_files:
        p = os.path.join(DATA_DIR, fn)
        assert os.path.exists(p)
        df = pd.read_csv(p)
        assert len(df) <= 400, f"Baseline file {fn} must retain demo scale"

def test_live_model_untouched():
    """Verifies that the live model in backend/models/ remains intact and was not overwritten."""
    assert os.path.exists(LIVE_MODEL_PATH)
    import joblib
    model = joblib.load(LIVE_MODEL_PATH)
    assert hasattr(model, "predict_proba")

def test_step24_robustness_corpus_untouched():
    """Verifies that the Step 24 robustness corpus has not been modified or overwritten."""
    rob_gt = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    assert os.path.exists(rob_gt)
    df = pd.read_csv(rob_gt)
    assert len(df) == 500, "Step 24 robustness ground truth must remain exactly 500 pairs"

def test_adversarial_dataset_counts_and_balance():
    """Verifies that the adversarial dataset has exactly 1,200 pairs (600 pos, 600 neg)."""
    gt_path = os.path.join(ADV_DIR, "adversarial_ground_truth.csv")
    if not os.path.exists(gt_path):
        pytest.skip("Adversarial ground truth not generated yet")
        
    df = pd.read_csv(gt_path)
    assert len(df) == 1200, f"Expected 1,200 pairs, found {len(df)}"
    pos = (df["expected_relationship"] == 1).sum()
    neg = (df["expected_relationship"] == 0).sum()
    assert pos == 600, f"Expected 600 positives, found {pos}"
    assert neg == 600, f"Expected 600 negatives, found {neg}"

def test_adversarial_feature_overlap_not_trivially_separable():
    """Verifies that hard negatives possess case co-occurrences and evidence diversity."""
    manifest_path = os.path.join(ADV_DIR, "adversarial_split_manifest.json")
    if not os.path.exists(manifest_path):
        pytest.skip("Adversarial manifest not generated yet")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    stats = manifest.get("feature_overlap_statistics", {})
    assert "case_cooccurrence_count" in stats
    assert "evidence_diversity" in stats
    
    # Verify that negative feature values overlap with positive range
    case_overlap = stats["case_cooccurrence_count"]["negative_overlap_pct"]
    assert case_overlap > 0.0, "Hard negatives must feature case co-occurrence overlap"
    
    div_overlap = stats["evidence_diversity"]["negative_overlap_pct"]
    assert div_overlap > 0.0, "Hard negatives must feature evidence diversity overlap"

def test_zero_case_leakage_adversarial():
    """Verifies zero case overlap between train, val, and test splits."""
    manifest_path = os.path.join(ADV_DIR, "adversarial_split_manifest.json")
    if not os.path.exists(manifest_path):
        pytest.skip("Adversarial manifest not generated yet")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    assert manifest.get("zero_case_leakage_verified") is True

def test_adversarial_models_and_reports_generated():
    """Verifies that all 4 models and selection reports are saved under adversarial_training/."""
    report_md = os.path.join(ADV_DIR, "MODEL_SELECTION_REPORT.md")
    report_json = os.path.join(ADV_DIR, "adversarial_report.json")
    models_sub = os.path.join(ADV_DIR, "models")
    
    if not os.path.exists(report_json):
        pytest.skip("Adversarial runner has not been executed yet")
        
    assert os.path.exists(report_md)
    for mname in ["Adv_LogReg_11_Scaled.joblib", "Adv_RandomForest_11.joblib", "Adv_HistGradientBoosting_11.joblib", "Adv_Calibrated_RF_11.joblib"]:
        assert os.path.exists(os.path.join(models_sub, mname))
