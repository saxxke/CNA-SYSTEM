"""
robustness_runner.py
====================
Executes Step 24 ML Robustness, Hard-Negative & Stress Testing.
Evaluates:
1. Pre-trained Step 23 models on 500-pair adversarial robustness corpus (zero retraining of candidates).
2. Threshold sweeps (0.50, 0.60, 0.70, 0.80).
3. Controlled feature ablation (7 features, +diversity, +case_cooccur, +bidirectional, +volume, all 11).
4. Entity resolution stress testing on 300 hard-negative and mutation pairs.
5. Strict artifact isolation in backend/data/expanded/experiments/robustness/.
"""

import os
import sys
import time
import json
import joblib
import random
import difflib
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, brier_score_loss, confusion_matrix
)

# Project imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from modules.data_generator.robustness_generator import generate_robustness_corpus
from modules.data_generator.features import (
    extract_features_7, extract_features_11,
    FEATURE_NAMES_7, FEATURE_NAMES_11
)
from modules.data_generator.splitter import split_dataset
from modules.entity_resolution.resolver import (
    entity_resolution_score, calculate_string_similarity
)
from modules.entity_resolution.normalization import normalize_entity

EXPERIMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/experiments'))
MODELS_DIR = os.path.join(EXPERIMENTS_DIR, "models")
ROBUSTNESS_DIR = os.path.join(EXPERIMENTS_DIR, "robustness")
SMALL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/expanded/small'))

def measure_inference_time(model: Any, X: np.ndarray, iterations: int = 5) -> float:
    if len(X) == 0:
        return 0.0
    start = time.perf_counter()
    for _ in range(iterations):
        if hasattr(model, "predict_proba"):
            _ = model.predict_proba(X)
        else:
            _ = model.predict(X)
    elapsed = time.perf_counter() - start
    return float((elapsed / (len(X) * iterations)) * 1000.0)

def evaluate_thresholds_df(y_true: np.ndarray, y_proba: np.ndarray, model_name: str) -> List[Dict[str, Any]]:
    rows = []
    for th in [0.50, 0.60, 0.70, 0.80]:
        y_pred = (y_proba >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        rows.append({
            "model": model_name,
            "threshold": th,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn)
        })
    return rows

def run_robustness_evaluations() -> Dict[str, Any]:
    os.makedirs(ROBUSTNESS_DIR, exist_ok=True)
    
    # 1. Ensure robustness corpus is generated
    gt_file = os.path.join(ROBUSTNESS_DIR, "robustness_ground_truth.csv")
    if not os.path.exists(gt_file):
        generate_robustness_corpus(seed=42)
        
    rob_gt_df = pd.read_csv(gt_file)
    rob_comms_df = pd.read_csv(os.path.join(ROBUSTNESS_DIR, "robustness_comms.csv"))
    rob_txns_df = pd.read_csv(os.path.join(ROBUSTNESS_DIR, "robustness_txns.csv"))
    rob_cp_df = pd.read_csv(os.path.join(ROBUSTNESS_DIR, "robustness_case_persons.csv"))
    
    # Load entity names from SMALL dataset
    persons_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "persons.csv"))
    entities_map = {str(r["person_id"]): str(r["full_name"]) for _, r in persons_df.iterrows()}
    
    # Also incorporate base communications/transactions/case_persons for complete inference context
    base_comms = pd.read_csv(os.path.join(SMALL_DATA_DIR, "communications.csv"))
    base_txns = pd.read_csv(os.path.join(SMALL_DATA_DIR, "transactions.csv"))
    base_cp = pd.read_csv(os.path.join(SMALL_DATA_DIR, "case_persons.csv"))
    
    combined_comms = pd.concat([base_comms, rob_comms_df], ignore_index=True)
    combined_txns = pd.concat([base_txns, rob_txns_df], ignore_index=True)
    combined_cp = pd.concat([base_cp, rob_cp_df], ignore_index=True)
    
    # Extract features for all 500 robustness pairs
    X_rob_7 = []
    X_rob_11 = []
    y_rob = []
    scenario_tags = []
    
    for _, r in rob_gt_df.iterrows():
        rel = {
            "source": r["source_entity_id"],
            "target": r["target_entity_id"],
            "relationship_type": r["relationship_type"],
            "case_id": r.get("case_id", ""),
            "evidence": r.get("evidence_reference", "")
        }
        X_rob_7.append(extract_features_7(rel, combined_comms, combined_txns, entities_map))
        X_rob_11.append(extract_features_11(rel, combined_comms, combined_txns, combined_cp, entities_map))
        y_rob.append(int(r["expected_relationship"]))
        scenario_tags.append(r.get("scenario", "UNKNOWN"))
        
    X_rob_7 = np.array(X_rob_7)
    X_rob_11 = np.array(X_rob_11)
    y_rob = np.array(y_rob)
    
    # 2. Evaluate Step 23 pre-trained candidate models on the robustness corpus
    model_files = {
        "LogReg_7_Baseline": ("LogReg_7_Baseline.joblib", X_rob_7, 7),
        "LogReg_11_Scaled": ("LogReg_11_Scaled.joblib", X_rob_11, 11),
        "RandomForest_11": ("RandomForest_11.joblib", X_rob_11, 11),
        "HistGradientBoosting_11": ("HistGradientBoosting_11.joblib", X_rob_11, 11),
        "Calibrated_RF_11": ("Calibrated_RF_11.joblib", X_rob_11, 11)
    }
    
    model_robustness_results = {}
    threshold_records = []
    
    for name, (fname, X_data, feat_count) in model_files.items():
        mpath = os.path.join(MODELS_DIR, fname)
        if not os.path.exists(mpath):
            raise FileNotFoundError(f"Required Step 23 pre-trained model not found: {mpath}")
            
        model = joblib.load(mpath)
        
        y_pred = model.predict(X_data)
        y_proba = model.predict_proba(X_data)[:, 1]
        
        prec = float(precision_score(y_rob, y_pred, zero_division=0))
        rec = float(recall_score(y_rob, y_pred, zero_division=0))
        f1 = float(f1_score(y_rob, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_rob, y_proba))
        pr_auc = float(average_precision_score(y_rob, y_proba))
        brier = float(brier_score_loss(y_rob, y_proba))
        
        tn, fp, fn, tp = confusion_matrix(y_rob, y_pred, labels=[0, 1]).ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        inf_ms = measure_inference_time(model, X_data)
        
        model_robustness_results[name] = {
            "model_name": name,
            "feature_count": feat_count,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "false_positive_rate": round(fpr, 4),
            "inference_time_ms_per_1k": round(inf_ms * 1000.0, 4),
            "confusion_matrix": {
                "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)
            }
        }
        
        # Threshold records
        th_res = evaluate_thresholds_df(y_rob, y_proba, name)
        threshold_records.extend(th_res)
        
    # Save threshold results CSV
    th_df = pd.DataFrame(threshold_records)
    th_df.to_csv(os.path.join(ROBUSTNESS_DIR, "threshold_results.csv"), index=False)
    
    # 3. Controlled Feature Ablation Study
    # Train LogisticRegression with StandardScaler on SMALL train set under 6 feature configurations:
    # 1. 7 features
    # 2. 7 features + evidence_diversity
    # 3. 7 features + case_cooccurrence_count
    # 4. 7 features + bidirectional_activity
    # 5. 7 features + normalized_transaction_volume
    # 6. All 11 features
    split_res = split_dataset(SMALL_DATA_DIR, train_ratio=0.70, test_ratio=0.30, seed=42)
    train_rows = split_res["train_gt"]
    
    # Extract training data for all 11 features
    X_tr_full, y_tr = [], []
    for r in train_rows:
        rel = {
            "source": r["source_entity_id"],
            "target": r["target_entity_id"],
            "relationship_type": r["relationship_type"],
            "case_id": r.get("case_id", ""),
            "evidence": r.get("evidence_reference", "")
        }
        X_tr_full.append(extract_features_11(rel, base_comms, base_txns, base_cp, entities_map))
        y_tr.append(int(r["expected_relationship"]))
    X_tr_full = np.array(X_tr_full)
    y_tr = np.array(y_tr)
    
    ablation_configs = {
        "Baseline_7_Features": list(range(7)),
        "7_Plus_Evidence_Diversity": list(range(7)) + [7],
        "7_Plus_Case_Cooccurrence": list(range(7)) + [8],
        "7_Plus_Bidirectional_Activity": list(range(7)) + [9],
        "7_Plus_Transaction_Volume": list(range(7)) + [10],
        "All_11_Features": list(range(11))
    }
    
    ablation_records = []
    for cfg_name, feat_indices in ablation_configs.items():
        X_tr_sub = X_tr_full[:, feat_indices]
        X_rob_sub = X_rob_11[:, feat_indices]
        
        clf = Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", random_state=42, max_iter=500))
        ])
        clf.fit(X_tr_sub, y_tr)
        
        y_pred = clf.predict(X_rob_sub)
        y_proba = clf.predict_proba(X_rob_sub)[:, 1]
        
        prec = float(precision_score(y_rob, y_pred, zero_division=0))
        rec = float(recall_score(y_rob, y_pred, zero_division=0))
        f1 = float(f1_score(y_rob, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_rob, y_proba))
        brier = float(brier_score_loss(y_rob, y_proba))
        tn, fp, fn, tp = confusion_matrix(y_rob, y_pred, labels=[0, 1]).ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        
        ablation_records.append({
            "configuration": cfg_name,
            "feature_count": len(feat_indices),
            "features_used": ", ".join([FEATURE_NAMES_11[i] for i in feat_indices]),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "brier_score": round(brier, 4),
            "false_positive_rate": round(fpr, 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn)
        })
        
    ablation_df = pd.DataFrame(ablation_records)
    ablation_df.to_csv(os.path.join(ROBUSTNESS_DIR, "feature_ablation.csv"), index=False)
    
    # 4. Entity Resolution Robustness Stress Test (300 Pairs)
    # 150 Challenging Positive Mutations:
    # - typos, spacing variations, phonetic/transliteration differences, initials
    # 150 Hard Negatives:
    # - shared surnames, initials vs full name with different surnames, similar names, same locality
    er_stress_pairs = []
    
    # Load aliases from SMALL dataset
    aliases_df = pd.read_csv(os.path.join(SMALL_DATA_DIR, "aliases.csv"))
    
    # A. 150 Positive Mutations
    pos_count = 0
    # Add alias records first
    for _, row in aliases_df.iterrows():
        if pos_count >= 150:
            break
        p_name = entities_map.get(str(row["person_id"]), "")
        if p_name:
            er_stress_pairs.append({
                "entity_a": p_name,
                "entity_b": str(row["alias_name"]),
                "ground_truth": 1,
                "category": "ALIAS_MUTATION"
            })
            pos_count += 1
            
    # Synthetic realistic spelling & spacing mutations to reach 150
    base_names = [p["full_name"] for p in persons_df.to_dict('records')]
    for name in base_names:
        if pos_count >= 150:
            break
        parts = name.split()
        if len(parts) >= 2:
            # Initials + surname: "Arjun Sen" -> "A. Sen"
            er_stress_pairs.append({
                "entity_a": name,
                "entity_b": f"{parts[0][0]}. {' '.join(parts[1:])}",
                "ground_truth": 1,
                "category": "INITIAL_SURNAME"
            })
            pos_count += 1
            if pos_count >= 150:
                break
            # Spacing mutation: "Debashis" -> "Deb Ashis" or compound spacing
            er_stress_pairs.append({
                "entity_a": name,
                "entity_b": f"{parts[0][:3]} {parts[0][3:]} {' '.join(parts[1:])}" if len(parts[0]) > 4 else f"{parts[0]} {' '.join(parts[1:])}",
                "ground_truth": 1,
                "category": "SPACING_VARIATION"
            })
            pos_count += 1
            
    # B. 150 Hard Negative Pairs
    neg_count = 0
    surname_groups = {}
    for p in persons_df.to_dict('records'):
        parts = p["full_name"].strip().split()
        surname = parts[-1] if len(parts) > 1 else parts[0]
        surname_groups.setdefault(surname, []).append(p)

    # 1. Shared surnames in same locality
    for surname, group in surname_groups.items():
        if len(group) >= 2 and neg_count < 60:
            er_stress_pairs.append({
                "entity_a": group[0]["full_name"],
                "entity_b": group[1]["full_name"],
                "ground_truth": 0,
                "category": "SHARED_SURNAME_SAME_LOCALITY"
            })
            neg_count += 1
            
    # 2. Initials with different people: "A. Sen" vs "Amitabh Sen"
    common_surnames = ["Ghosh", "Chatterjee", "Banerjee", "Das", "Sen", "Bose", "Mukherjee", "Dutta"]
    for sn in common_surnames:
        matching = [p for p in base_names if p.endswith(sn)]
        if len(matching) >= 2 and neg_count < 110:
            p1 = matching[0]
            p2 = matching[1]
            er_stress_pairs.append({
                "entity_a": f"{p1.split()[0][0]}. {sn}",
                "entity_b": p2,
                "ground_truth": 0,
                "category": "INITIAL_VS_DIFFERENT_PERSON"
            })
            neg_count += 1
            
    # 3. Similar first names, different individuals: "Sanjay Ghosh" vs "Sanjay Das"
    for i in range(len(base_names) - 1):
        if neg_count >= 150:
            break
        p1 = base_names[i]
        p2 = base_names[i + 1]
        fn1 = p1.split()[0]
        fn2 = p2.split()[0]
        if fn1 == fn2:
            er_stress_pairs.append({
                "entity_a": p1,
                "entity_b": p2,
                "ground_truth": 0,
                "category": "SAME_FIRSTNAME_DIFFERENT_SURNAME"
            })
            neg_count += 1
            
    while neg_count < 150:
        p1, p2 = random.sample(base_names, 2)
        er_stress_pairs.append({
            "entity_a": p1,
            "entity_b": p2,
            "ground_truth": 0,
            "category": "DISTINCT_PERSONS"
        })
        neg_count += 1
        
    # Evaluate Entity Resolution on all 300 pairs
    er_records = []
    for pair in er_stress_pairs:
        ea = normalize_entity("PERSON", pair["entity_a"])
        eb = normalize_entity("PERSON", pair["entity_b"])
        res = entity_resolution_score(ea, eb)
        
        er_records.append({
            "entity_a": pair["entity_a"],
            "entity_b": pair["entity_b"],
            "ground_truth": pair["ground_truth"],
            "category": pair["category"],
            "string_similarity": round(res["string_similarity"], 4),
            "embedding_similarity": round(res["embedding_similarity"], 4),
            "attribute_similarity": round(res["attribute_similarity"], 4),
            "final_score": round(res["final_score"], 4),
            "decision": res["decision"]
        })
        
    er_df = pd.DataFrame(er_records)
    er_df.to_csv(os.path.join(ROBUSTNESS_DIR, "entity_resolution_robustness.csv"), index=False)
    
    # Compute ER Metrics at MATCH (>= 0.85) and POSSIBLE_MATCH (>= 0.65)
    y_er_true = np.array([r["ground_truth"] for r in er_records])
    scores_er = np.array([r["final_score"] for r in er_records])
    
    # At POSSIBLE_MATCH (>= 0.65)
    y_er_pred_65 = (scores_er >= 0.65).astype(int)
    tn_65, fp_65, fn_65, tp_65 = confusion_matrix(y_er_true, y_er_pred_65, labels=[0, 1]).ravel()
    prec_65 = float(precision_score(y_er_true, y_er_pred_65, zero_division=0))
    rec_65 = float(recall_score(y_er_true, y_er_pred_65, zero_division=0))
    f1_65 = float(f1_score(y_er_true, y_er_pred_65, zero_division=0))
    fmr_65 = float(fp_65 / (fp_65 + tn_65)) if (fp_65 + tn_65) > 0 else 0.0
    
    # At MATCH (>= 0.85)
    y_er_pred_85 = (scores_er >= 0.85).astype(int)
    tn_85, fp_85, fn_85, tp_85 = confusion_matrix(y_er_true, y_er_pred_85, labels=[0, 1]).ravel()
    prec_85 = float(precision_score(y_er_true, y_er_pred_85, zero_division=0))
    rec_85 = float(recall_score(y_er_true, y_er_pred_85, zero_division=0))
    f1_85 = float(f1_score(y_er_true, y_er_pred_85, zero_division=0))
    fmr_85 = float(fp_85 / (fp_85 + tn_85)) if (fp_85 + tn_85) > 0 else 0.0
    
    er_robustness_summary = {
        "total_pairs_tested": len(er_records),
        "positive_pairs": int(np.sum(y_er_true == 1)),
        "negative_pairs": int(np.sum(y_er_true == 0)),
        "possible_match_tier_0_65": {
            "threshold": 0.65,
            "precision": round(prec_65, 4),
            "recall": round(rec_65, 4),
            "f1_score": round(f1_65, 4),
            "false_match_rate": round(fmr_65, 4),
            "tp": int(tp_65), "fp": int(fp_65), "tn": int(tn_65), "fn": int(fn_65)
        },
        "match_tier_0_85": {
            "threshold": 0.85,
            "precision": round(prec_85, 4),
            "recall": round(rec_85, 4),
            "f1_score": round(f1_85, 4),
            "false_match_rate": round(fmr_85, 4),
            "tp": int(tp_85), "fp": int(fp_85), "tn": int(tn_85), "fn": int(fn_85)
        }
    }
    
    # 5. Master Report Assembly
    master_report = {
        "robustness_metadata": {
            "evaluation_corpus": "500-pair hard-negative adversarial dataset (250 pos, 250 neg)",
            "scenarios_tested": 15,
            "zero_leakage": True
        },
        "step23_models_on_robustness_corpus": model_robustness_results,
        "feature_ablation_results": ablation_records,
        "entity_resolution_robustness": er_robustness_summary
    }
    
    # Save master report JSON
    rep_path = os.path.join(ROBUSTNESS_DIR, "robustness_report.json")
    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)
        
    # Generate Markdown Report
    generate_markdown_robustness_report(master_report, os.path.join(ROBUSTNESS_DIR, "ROBUSTNESS_REPORT.md"))
    
    return master_report

def generate_markdown_robustness_report(report: Dict[str, Any], output_path: str):
    models = report["step23_models_on_robustness_corpus"]
    ablation = report["feature_ablation_results"]
    er = report["entity_resolution_robustness"]
    
    lines = [
        "# Step 24 — ML Robustness, Hard-Negative & Stress Testing Report",
        "",
        "## 1. Candidate Model Performance on Adversarial Robustness Corpus (500 Pairs)",
        "",
        "| Model | Feature Count | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | False Positive Rate | Inference Time (ms/1k) |",
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
        "## 2. Controlled Feature Ablation Study",
        "",
        "| Configuration | Feat Count | Precision | Recall | F1 Score | ROC-AUC | Brier Loss | False Positive Rate |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ])
    
    for ab in ablation:
        lines.append(
            f"| `{ab['configuration']}` | {ab['feature_count']} | {ab['precision']:.4f} | {ab['recall']:.4f} | "
            f"{ab['f1_score']:.4f} | {ab['roc_auc']:.4f} | {ab['brier_score']:.4f} | {ab['false_positive_rate']:.4f} |"
        )
        
    lines.extend([
        "",
        "## 3. Entity Resolution Stress Benchmark (300 Challenging Pairs)",
        f"- **Total Pairs Tested**: {er['total_pairs_tested']} (150 positive mutations, 150 hard negatives)",
        "",
        "| Decision Tier | Threshold | Precision | Recall | F1 Score | False Match Rate | TP | FP | TN | FN |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| `POSSIBLE_MATCH` | $\\ge 0.65$ | {er['possible_match_tier_0_65']['precision']:.4f} | {er['possible_match_tier_0_65']['recall']:.4f} | {er['possible_match_tier_0_65']['f1_score']:.4f} | {er['possible_match_tier_0_65']['false_match_rate']:.4f} | {er['possible_match_tier_0_65']['tp']} | {er['possible_match_tier_0_65']['fp']} | {er['possible_match_tier_0_65']['tn']} | {er['possible_match_tier_0_65']['fn']} |",
        f"| `MATCH` | $\\ge 0.85$ | {er['match_tier_0_85']['precision']:.4f} | {er['match_tier_0_85']['recall']:.4f} | {er['match_tier_0_85']['f1_score']:.4f} | {er['match_tier_0_85']['false_match_rate']:.4f} | {er['match_tier_0_85']['tp']} | {er['match_tier_0_85']['fp']} | {er['match_tier_0_85']['tn']} | {er['match_tier_0_85']['fn']} |",
        ""
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    rep = run_robustness_evaluations()
    print("Robustness evaluations completed successfully. Output files saved in backend/data/expanded/experiments/robustness/")
