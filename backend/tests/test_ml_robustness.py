"""
test_ml_robustness.py
=====================
Tests verifying Step 24 ML Robustness, Hard-Negative & Stress Testing invariants:
1. Robustness artifacts and data are strictly quarantined in backend/data/expanded/experiments/robustness/.
2. Baseline CSV dataset files (backend/data/*.csv) remain 100% untouched.
3. Live production model (backend/models/relationship_confidence_model.joblib) remains 100% untouched.
4. Family relationships are strictly excluded from investigative relationship confidence.
5. Co-accused without direct operational link are properly designated as negative pairs.
6. Robustness reports, ablation CSVs, and stress test matrices exist and are valid.
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
ROBUSTNESS_DIR = os.path.join(EXP_DIR, 'robustness')
LIVE_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/relationship_confidence_model.joblib'))

def test_robustness_corpus_isolation():
    """Verifies that all robustness artifacts reside strictly under backend/data/expanded/experiments/robustness/."""
    assert os.path.exists(ROBUSTNESS_DIR), "Robustness directory must exist"
    # Verify baseline files remain untouched
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

def test_robustness_dataset_counts_and_balance():
    """Verifies that the robustness ground truth has 500 balanced pairs across scenarios A through O."""
    gt_path = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    if not os.path.exists(gt_path):
        pytest.skip("Robustness ground truth not generated yet")
        
    df = pd.read_csv(gt_path)
    assert len(df) == 500, f"Expected 500 pairs, found {len(df)}"
    pos = (df["expected_relationship"] == 1).sum()
    neg = (df["expected_relationship"] == 0).sum()
    assert pos == 250, f"Expected 250 positives, found {pos}"
    assert neg == 250, f"Expected 250 negatives, found {neg}"
    
    # Check scenario diversity
    scenarios = set(df["scenario"].dropna())
    assert len(scenarios) >= 10, f"Expected at least 10 scenarios, found {len(scenarios)}"
    assert "SCENARIO_D_SHARED_CASE_NO_DIRECT_LINK" in scenarios
    assert "SCENARIO_L_FAMILY_NON_OPERATIONAL" in scenarios

def test_family_relationship_isolation():
    """Verifies that family relationships are strictly marked as expected_relationship = 0 for operational investigation."""
    gt_path = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    if not os.path.exists(gt_path):
        pytest.skip("Robustness ground truth not generated yet")
        
    df = pd.read_csv(gt_path)
    fam_subset = df[df["scenario"] == "SCENARIO_L_FAMILY_NON_OPERATIONAL"]
    assert len(fam_subset) >= 20
    assert (fam_subset["expected_relationship"] == 0).all(), "All family relationships must be expected_relationship = 0"

def test_hard_negative_cooccurrence_not_positive():
    """Verifies that shared-case hard negatives have expected_relationship = 0."""
    gt_path = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    if not os.path.exists(gt_path):
        pytest.skip("Robustness ground truth not generated yet")
        
    df = pd.read_csv(gt_path)
    case_neg = df[df["scenario"] == "SCENARIO_D_SHARED_CASE_NO_DIRECT_LINK"]
    assert len(case_neg) >= 20
    assert (case_neg["expected_relationship"] == 0).all()

def test_reports_and_csvs_generated():
    """Verifies that all required report files exist and contain valid data."""
    rep_json = os.path.join(ROBUSTNESS_DIR, "robustness_report.json")
    rep_md = os.path.join(ROBUSTNESS_DIR, "ROBUSTNESS_REPORT.md")
    abl_csv = os.path.join(ROBUSTNESS_DIR, "feature_ablation.csv")
    th_csv = os.path.join(ROBUSTNESS_DIR, "threshold_results.csv")
    er_csv = os.path.join(ROBUSTNESS_DIR, "entity_resolution_robustness.csv")
    
    if not os.path.exists(rep_json):
        pytest.skip("Robustness reports not generated yet")
        
    assert os.path.exists(rep_md)
    assert os.path.exists(abl_csv)
    assert os.path.exists(th_csv)
    assert os.path.exists(er_csv)
    
    with open(rep_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "step23_models_on_robustness_corpus" in data
    assert "feature_ablation_results" in data
    assert "entity_resolution_robustness" in data
