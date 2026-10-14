# Step 24 — ML Robustness, Hard-Negative & Stress Testing Report

## 1. Candidate Model Performance on Adversarial Robustness Corpus (500 Pairs)

| Model | Feature Count | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | False Positive Rate | Inference Time (ms/1k) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `LogReg_7_Baseline` | 7 | 0.5602 | 0.9680 | 0.7097 | 0.8297 | 0.8321 | 0.2874 | 0.7600 | 0.52 |
| `LogReg_11_Scaled` | 11 | 0.5000 | 1.0000 | 0.6667 | 0.6000 | 0.5556 | 0.5000 | 1.0000 | 1.71 |
| `RandomForest_11` | 11 | 0.6849 | 1.0000 | 0.8130 | 0.8256 | 0.7570 | 0.2192 | 0.4600 | 35.66 |
| `HistGradientBoosting_11` | 11 | 0.6849 | 1.0000 | 0.8130 | 0.7849 | 0.7044 | 0.2293 | 0.4600 | 5.48 |
| `Calibrated_RF_11` | 11 | 0.6849 | 1.0000 | 0.8130 | 0.8024 | 0.7028 | 0.2327 | 0.4600 | 100.96 |

## 2. Controlled Feature Ablation Study

| Configuration | Feat Count | Precision | Recall | F1 Score | ROC-AUC | Brier Loss | False Positive Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Baseline_7_Features` | 7 | 0.5000 | 1.0000 | 0.6667 | 0.5300 | 0.5000 | 1.0000 |
| `7_Plus_Evidence_Diversity` | 8 | 0.5000 | 1.0000 | 0.6667 | 0.5300 | 0.5000 | 1.0000 |
| `7_Plus_Case_Cooccurrence` | 8 | 0.5000 | 1.0000 | 0.6667 | 0.5300 | 0.5000 | 1.0000 |
| `7_Plus_Bidirectional_Activity` | 8 | 0.5000 | 1.0000 | 0.6667 | 0.6000 | 0.5000 | 1.0000 |
| `7_Plus_Transaction_Volume` | 8 | 0.5000 | 1.0000 | 0.6667 | 0.6000 | 0.5000 | 1.0000 |
| `All_11_Features` | 11 | 0.5000 | 1.0000 | 0.6667 | 0.6000 | 0.5000 | 1.0000 |

## 3. Entity Resolution Stress Benchmark (300 Challenging Pairs)
- **Total Pairs Tested**: 300 (150 positive mutations, 150 hard negatives)

| Decision Tier | Threshold | Precision | Recall | F1 Score | False Match Rate | TP | FP | TN | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `POSSIBLE_MATCH` | $\ge 0.65$ | 0.7905 | 0.7800 | 0.7852 | 0.2067 | 117 | 31 | 119 | 33 |
| `MATCH` | $\ge 0.85$ | 0.9048 | 0.1267 | 0.2222 | 0.0133 | 19 | 2 | 148 | 131 |
