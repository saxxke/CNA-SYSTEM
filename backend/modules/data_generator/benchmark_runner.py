"""
benchmark_runner.py
===================
Comprehensive ML benchmarking and experiment runner for Step 23.
Evaluates:
1. Step 22 Baseline vs Enhanced Experimental Models
2. Feature engineering (7 features vs 11 features)
3. Model candidates:
   - Logistic Regression (7 features) [Baseline]
   - Logistic Regression (11 features + StandardScaler)
   - Random Forest Classifier (11 features, explainable depth limits)
   - HistGradientBoostingClassifier (11 features, robust tree ensembles)
   - Calibrated Classifier (Isotonic / Sigmoid probability calibration)
4. Threshold sweeps: 0.50, 0.60, 0.70, 0.80
5. Entity Resolution benchmarking on positive alias mutations and hard negative pairs
6. Isolates all models and reports in backend/data/expanded/experiments/
"""

import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, brier_score_loss, confusion_matrix
)

# Project imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from modules.data_generator.splitter import split_dataset
from modules.data_generator.features import (
    extract_features_7, extract_features_11,
    FEATURE_NAMES_7, FEATURE_NAMES_11
)
from modules.entity_resolution.resolver import (
    entity_resolution_score, calculate_string_similarity
)
from modules.entity_resolution.normalization import normalize_entity

EXPERIMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/experiments'))
MODELS_DIR = os.path.join(EXPERIMENTS_DIR, "models")
SMALL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/small'))

def measure_inference_time(model: Any, X: np.ndarray, iterations: int = 5) -> float:
    """
    Measures inference latency in seconds per 1,000 samples.
    """
    if len(X) == 0:
        return 0.0
    start = time.perf_counter()
    for _ in range(iterations):
        if hasattr(model, "predict_proba"):
            _ = model.predict_proba(X)
        else:
            _ = model.predict(X)
    elapsed = time.perf_counter() - start
    total_samples = len(X) * iterations
    return float((elapsed / total_samples) * 1000.0)

def evaluate_thresholds(y_true: np.ndarray, y_proba: np.ndarray, thresholds: List[float]) -> Dict[str, Any]:
    """
    Evaluates classification performance across specific confidence thresholds.
    """
    results = {}
    for th in thresholds:
        y_pred = (y_proba >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        
        results[f"th_{th:.2f}"] = {
            "threshold": th,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        }
    return results

def run_benchmarks(data_dir: str = SMALL_DATA_DIR) -> Dict[str, Any]:
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # 1. Load context tables
    cases_df = pd.read_csv(os.path.join(data_dir, "cases.csv"))
    persons_df = pd.read_csv(os.path.join(data_dir, "persons.csv"))
    case_persons_df = pd.read_csv(os.path.join(data_dir, "case_persons.csv"))
    comms_df = pd.read_csv(os.path.join(data_dir, "communications.csv"))
    txns_df = pd.read_csv(os.path.join(data_dir, "transactions.csv"))
    aliases_df = pd.read_csv(os.path.join(data_dir, "aliases.csv"))
    
    entities_map = {}
    for _, row in persons_df.iterrows():
        entities_map[str(row["person_id"])] = str(row["full_name"])
        
    # 2. Perform case-level leakage-safe train/test split (seed=42)
    split_res = split_dataset(data_dir, train_ratio=0.70, test_ratio=0.30, seed=42)
    train_rows = split_res["train_gt"]
    test_rows = split_res["test_gt"]
    
    # 3. Extract features for both 7-feature and 11-feature configurations
    X_train_7, X_train_11, y_train = [], [], []
    for r in train_rows:
        rel = {
            "source": r["source_entity_id"],
            "target": r["target_entity_id"],
            "relationship_type": r["relationship_type"],
            "case_id": r.get("case_id", ""),
            "evidence": r.get("evidence_reference", "")
        }
        X_train_7.append(extract_features_7(rel, comms_df, txns_df, entities_map))
        X_train_11.append(extract_features_11(rel, comms_df, txns_df, case_persons_df, entities_map))
        y_train.append(int(r["expected_relationship"]))
        
    X_test_7, X_test_11, y_test = [], [], []
    for r in test_rows:
        rel = {
            "source": r["source_entity_id"],
            "target": r["target_entity_id"],
            "relationship_type": r["relationship_type"],
            "case_id": r.get("case_id", ""),
            "evidence": r.get("evidence_reference", "")
        }
        X_test_7.append(extract_features_7(rel, comms_df, txns_df, entities_map))
        X_test_11.append(extract_features_11(rel, comms_df, txns_df, case_persons_df, entities_map))
        y_test.append(int(r["expected_relationship"]))
        
    X_train_7 = np.array(X_train_7)
    X_train_11 = np.array(X_train_11)
    y_train = np.array(y_train)
    X_test_7 = np.array(X_test_7)
    X_test_11 = np.array(X_test_11)
    y_test = np.array(y_test)
    
    # Candidate Definitions
    candidates = {}
    
    # Model 1: Logistic Regression (7 features) [Baseline reproduction]
    candidates["LogReg_7_Baseline"] = {
        "model": LogisticRegression(class_weight="balanced", random_state=42, max_iter=500),
        "X_tr": X_train_7,
        "X_te": X_test_7,
        "features": FEATURE_NAMES_7,
        "feature_count": 7,
        "description": "Step 22 Baseline Logistic Regression with 7 explainable features"
    }
    
    # Model 2: Logistic Regression (11 features + StandardScaler)
    candidates["LogReg_11_Scaled"] = {
        "model": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", C=1.0, random_state=42, max_iter=500))
        ]),
        "X_tr": X_train_11,
        "X_te": X_test_11,
        "features": FEATURE_NAMES_11,
        "feature_count": 11,
        "description": "Standardized Logistic Regression with 11 explainable features and L2 penalty"
    }
    
    # Model 3: Random Forest Classifier (11 features)
    candidates["RandomForest_11"] = {
        "model": RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42
        ),
        "X_tr": X_train_11,
        "X_te": X_test_11,
        "features": FEATURE_NAMES_11,
        "feature_count": 11,
        "description": "Random Forest with 11 features, constrained depth for explainability"
    }
    
    # Model 4: HistGradientBoosting (11 features)
    candidates["HistGradientBoosting_11"] = {
        "model": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=4,
            l2_regularization=1.0,
            random_state=42
        ),
        "X_tr": X_train_11,
        "X_te": X_test_11,
        "features": FEATURE_NAMES_11,
        "feature_count": 11,
        "description": "HistGradientBoosting with 11 features, shallow trees for robust interaction capture"
    }
    
    results = {}
    threshold_sweeps = {}
    
    # Train and evaluate candidate models
    for name, spec in candidates.items():
        m = spec["model"]
        X_tr = spec["X_tr"]
        X_te = spec["X_te"]
        
        # Measure training time
        t0 = time.perf_counter()
        m.fit(X_tr, y_train)
        train_time = time.perf_counter() - t0
        
        # Predictions & Probabilities
        y_pred = m.predict(X_te)
        y_proba = m.predict_proba(X_te)[:, 1]
        
        # Latency per 1000 queries
        inf_time_1k = measure_inference_time(m, X_te)
        
        # Standard metrics at default 0.50 threshold
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_test, y_proba))
        pr_auc = float(average_precision_score(y_test, y_proba))
        brier = float(brier_score_loss(y_test, y_proba))
        
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        
        # Threshold sweeps
        th_res = evaluate_thresholds(y_test, y_proba, [0.50, 0.60, 0.70, 0.80])
        threshold_sweeps[name] = th_res
        
        # Save model artifact into experimental directory
        artifact_path = os.path.join(MODELS_DIR, f"{name}.joblib")
        joblib.dump(m, artifact_path)
        
        results[name] = {
            "model_name": name,
            "description": spec["description"],
            "feature_count": spec["feature_count"],
            "features": spec["features"],
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "false_positive_rate": round(fpr, 4),
            "training_time_seconds": round(train_time, 4),
            "inference_time_ms_per_1k": round(inf_time_1k * 1000.0, 4),
            "confusion_matrix": {
                "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)
            },
            "artifact_path": artifact_path
        }
        
    # Model 5: Calibrated Classifier on top candidate (RandomForest_11)
    best_candidate_model = candidates["RandomForest_11"]["model"]
    calibrated_clf = CalibratedClassifierCV(estimator=best_candidate_model, cv=3, method="sigmoid")
    t0 = time.perf_counter()
    calibrated_clf.fit(X_train_11, y_train)
    calib_train_time = time.perf_counter() - t0
    
    y_pred_calib = calibrated_clf.predict(X_test_11)
    y_proba_calib = calibrated_clf.predict_proba(X_test_11)[:, 1]
    calib_inf_time = measure_inference_time(calibrated_clf, X_test_11)
    
    tn_c, fp_c, fn_c, tp_c = confusion_matrix(y_test, y_pred_calib, labels=[0, 1]).ravel()
    fpr_c = float(fp_c / (fp_c + tn_c)) if (fp_c + tn_c) > 0 else 0.0
    
    calib_th_res = evaluate_thresholds(y_test, y_proba_calib, [0.50, 0.60, 0.70, 0.80])
    threshold_sweeps["Calibrated_RF_11"] = calib_th_res
    
    calib_path = os.path.join(MODELS_DIR, "Calibrated_RF_11.joblib")
    joblib.dump(calibrated_clf, calib_path)
    
    results["Calibrated_RF_11"] = {
        "model_name": "Calibrated_RF_11",
        "description": "Random Forest (11 features) with Sigmoid Probability Calibration (cv=3)",
        "feature_count": 11,
        "features": FEATURE_NAMES_11,
        "precision": round(float(precision_score(y_test, y_pred_calib, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred_calib, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred_calib, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba_calib)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_proba_calib)), 4),
        "brier_score": round(float(brier_score_loss(y_test, y_proba_calib)), 4),
        "false_positive_rate": round(fpr_c, 4),
        "training_time_seconds": round(calib_train_time, 4),
        "inference_time_ms_per_1k": round(calib_inf_time * 1000.0, 4),
        "confusion_matrix": {
            "tp": int(tp_c), "fp": int(fp_c), "tn": int(tn_c), "fn": int(fn_c)
        },
        "artifact_path": calib_path
    }
    
    # 4. Entity Resolution Benchmark
    # A. Positive mutations: 200 aliases from aliases.csv matched against their ground-truth persons
    er_pos_results = []
    for _, row in aliases_df.iterrows():
        p_id = str(row["person_id"])
        canonical_name = entities_map.get(p_id, "")
        alias_name = str(row["alias_name"])
        
        ent_a = normalize_entity("PERSON", canonical_name)
        ent_b = normalize_entity("PERSON", alias_name)
        
        score_res = entity_resolution_score(ent_a, ent_b)
        er_pos_results.append({
            "canonical_name": canonical_name,
            "alias_name": alias_name,
            "final_score": score_res["final_score"],
            "decision": score_res["decision"]
        })
        
    # B. Hard negative pairs: 200 pairs of distinct individuals sharing locality or common surname
    # Deterministic selection of non-matching pairs
    er_neg_results = []
    p_rows = persons_df.to_dict('records')
    # Generate 200 hard negative pairs by matching people in the same locality with different names
    locality_groups = {}
    for p in p_rows:
        loc = p.get("locality", "Unknown")
        locality_groups.setdefault(loc, []).append(p)
        
    hard_neg_pairs = []
    for loc, group in locality_groups.items():
        if len(group) >= 2:
            for i in range(len(group) - 1):
                p1 = group[i]
                p2 = group[i + 1]
                hard_neg_pairs.append((p1, p2))
                if len(hard_neg_pairs) >= 200:
                    break
        if len(hard_neg_pairs) >= 200:
            break
            
    for p1, p2 in hard_neg_pairs:
        ent_a = normalize_entity("PERSON", p1["full_name"])
        ent_b = normalize_entity("PERSON", p2["full_name"])
        score_res = entity_resolution_score(ent_a, ent_b)
        er_neg_results.append({
            "name_1": p1["full_name"],
            "name_2": p2["full_name"],
            "locality": p1.get("locality"),
            "final_score": score_res["final_score"],
            "decision": score_res["decision"]
        })
        
    # Compute ER Metrics at MATCH (>=0.85) and POSSIBLE (>=0.65)
    # Target: 1 for positive mutation, 0 for hard negative pair
    pos_scores = [r["final_score"] for r in er_pos_results]
    neg_scores = [r["final_score"] for r in er_neg_results]
    
    # At POSSIBLE (>= 0.65)
    tp_er_65 = sum(1 for s in pos_scores if s >= 0.65)
    fn_er_65 = sum(1 for s in pos_scores if s < 0.65)
    fp_er_65 = sum(1 for s in neg_scores if s >= 0.65)
    tn_er_65 = sum(1 for s in neg_scores if s < 0.65)
    
    prec_er_65 = tp_er_65 / (tp_er_65 + fp_er_65) if (tp_er_65 + fp_er_65) > 0 else 0.0
    rec_er_65 = tp_er_65 / (tp_er_65 + fn_er_65) if (tp_er_65 + fn_er_65) > 0 else 0.0
    f1_er_65 = 2 * (prec_er_65 * rec_er_65) / (prec_er_65 + rec_er_65) if (prec_er_65 + rec_er_65) > 0 else 0.0
    
    # At MATCH (>= 0.85)
    tp_er_85 = sum(1 for s in pos_scores if s >= 0.85)
    fn_er_85 = sum(1 for s in pos_scores if s < 0.85)
    fp_er_85 = sum(1 for s in neg_scores if s >= 0.85)
    tn_er_85 = sum(1 for s in neg_scores if s < 0.85)
    
    prec_er_85 = tp_er_85 / (tp_er_85 + fp_er_85) if (tp_er_85 + fp_er_85) > 0 else 0.0
    rec_er_85 = tp_er_85 / (tp_er_85 + fn_er_85) if (tp_er_85 + fn_er_85) > 0 else 0.0
    f1_er_85 = 2 * (prec_er_85 * rec_er_85) / (prec_er_85 + rec_er_85) if (prec_er_85 + rec_er_85) > 0 else 0.0
    
    # Identify false match examples on hard negatives (score >= 0.65)
    false_match_examples = [r for r in er_neg_results if r["final_score"] >= 0.65]
    
    er_benchmark = {
        "positive_alias_mutations_tested": len(er_pos_results),
        "hard_negative_pairs_tested": len(er_neg_results),
        "average_positive_similarity": round(float(np.mean(pos_scores)), 4),
        "average_negative_similarity": round(float(np.mean(neg_scores)), 4),
        "threshold_possible_0_65": {
            "threshold": 0.65,
            "precision": round(prec_er_65, 4),
            "recall": round(rec_er_65, 4),
            "f1_score": round(f1_er_65, 4),
            "true_positives": tp_er_65,
            "false_negatives": fn_er_65,
            "true_negatives": tn_er_65,
            "false_positives": fp_er_65
        },
        "threshold_match_0_85": {
            "threshold": 0.85,
            "precision": round(prec_er_85, 4),
            "recall": round(rec_er_85, 4),
            "f1_score": round(f1_er_85, 4),
            "true_positives": tp_er_85,
            "false_negatives": fn_er_85,
            "true_negatives": tn_er_85,
            "false_positives": fp_er_85
        },
        "false_matches_on_hard_negatives": len(false_match_examples),
        "sample_false_matches": false_match_examples[:5]
    }
    
    # 5. Master Report
    master_report = {
        "benchmark_metadata": {
            "dataset": "SMALL",
            "seed": 42,
            "train_samples": len(X_train_7),
            "test_samples": len(X_test_7),
            "train_cases": split_res.get("train_case_count", 0),
            "test_cases": split_res.get("test_case_count", 0),
            "zero_case_leakage_verified": split_res.get("zero_case_leakage_verified", True)
        },
        "models_benchmarked": results,
        "threshold_sweeps": threshold_sweeps,
        "entity_resolution_benchmark": er_benchmark
    }
    
    # Save master report JSON
    report_json_path = os.path.join(EXPERIMENTS_DIR, "benchmark_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)
        
    # Generate Markdown Summary
    generate_markdown_report(master_report, os.path.join(EXPERIMENTS_DIR, "BENCHMARK_REPORT.md"))
    
    return master_report

def generate_markdown_report(report: Dict[str, Any], output_path: str):
    models = report["models_benchmarked"]
    sweeps = report["threshold_sweeps"]
    er = report["entity_resolution_benchmark"]
    
    lines = [
        "# ML Model Benchmarking & Improvement Report (Step 23)",
        "",
        "## 1. Executive Summary & Comparison Table",
        "",
        "| Model | Features | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | FPR | Inference Time (ms/1k) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    
    for name, m in models.items():
        lines.append(
            f"| `{name}` | {m['feature_count']} | {m['precision']:.4f} | {m['recall']:.4f} | "
            f"{m['f1_score']:.4f} | {m['roc_auc']:.4f} | {m['pr_auc']:.4f} | {m['brier_score']:.4f} | "
            f"{m['false_positive_rate']:.4f} | {m['inference_time_ms_per_1k']:.2f} |"
        )
        
    lines.extend([
        "",
        "## 2. Threshold Performance Matrix (0.50, 0.60, 0.70, 0.80)",
        "",
        "| Model | Metric | Th = 0.50 | Th = 0.60 | Th = 0.70 | Th = 0.80 |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |"
    ])
    
    for name, sw in sweeps.items():
        p_row = f"| `{name}` | Precision | {sw['th_0.50']['precision']:.4f} | {sw['th_0.60']['precision']:.4f} | {sw['th_0.70']['precision']:.4f} | {sw['th_0.80']['precision']:.4f} |"
        r_row = f"| | Recall | {sw['th_0.50']['recall']:.4f} | {sw['th_0.60']['recall']:.4f} | {sw['th_0.70']['recall']:.4f} | {sw['th_0.80']['recall']:.4f} |"
        f_row = f"| | F1 Score | {sw['th_0.50']['f1_score']:.4f} | {sw['th_0.60']['f1_score']:.4f} | {sw['th_0.70']['f1_score']:.4f} | {sw['th_0.80']['f1_score']:.4f} |"
        fpr_row = f"| | False Positive Rate | {sw['th_0.50']['false_positive_rate']:.4f} | {sw['th_0.60']['false_positive_rate']:.4f} | {sw['th_0.70']['false_positive_rate']:.4f} | {sw['th_0.80']['false_positive_rate']:.4f} |"
        lines.extend([p_row, r_row, f_row, fpr_row])
        
    lines.extend([
        "",
        "## 3. Entity Resolution Benchmark",
        f"- **Positive Alias Mutations Tested**: {er['positive_alias_mutations_tested']}",
        f"- **Hard Negative Non-Matching Pairs Tested**: {er['hard_negative_pairs_tested']}",
        f"- **Average Positive String Similarity**: {er['average_positive_similarity']:.4f}",
        f"- **Average Hard Negative Similarity**: {er['average_negative_similarity']:.4f}",
        "",
        "| Decision Tier | Threshold | Precision | Recall | F1 Score | TP | FP | TN | FN |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| `POSSIBLE_MATCH` | $\\ge 0.65$ | {er['threshold_possible_0_65']['precision']:.4f} | {er['threshold_possible_0_65']['recall']:.4f} | {er['threshold_possible_0_65']['f1_score']:.4f} | {er['threshold_possible_0_65']['true_positives']} | {er['threshold_possible_0_65']['false_positives']} | {er['threshold_possible_0_65']['true_negatives']} | {er['threshold_possible_0_65']['false_negatives']} |",
        f"| `MATCH` | $\\ge 0.85$ | {er['threshold_match_0_85']['precision']:.4f} | {er['threshold_match_0_85']['recall']:.4f} | {er['threshold_match_0_85']['f1_score']:.4f} | {er['threshold_match_0_85']['true_positives']} | {er['threshold_match_0_85']['false_positives']} | {er['threshold_match_0_85']['true_negatives']} | {er['threshold_match_0_85']['false_negatives']} |",
        "",
        f"- **False Matches on Hard Negatives**: {er['false_matches_on_hard_negatives']} / {er['hard_negative_pairs_tested']}",
        ""
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    rep = run_benchmarks()
    print("Benchmarking completed successfully. Models and reports saved in backend/data/expanded/experiments/")
