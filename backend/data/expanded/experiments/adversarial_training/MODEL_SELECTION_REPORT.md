# Step 25 — Adversarial ML Training & Model Selection Report

## 1. Adversarial Test Split Performance (180 Unseen Pairs)

| Model | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | FPR | Inference Time (ms/1k) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Adv_LogReg_11_Scaled` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0147 | 0.0000 | 2.26 |
| `Adv_RandomForest_11` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0008 | 0.0000 | 49.52 |
| `Adv_HistGradientBoosting_11` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 12.87 |
| `Adv_Calibrated_RF_11` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0001 | 0.0000 | 162.11 |

## 2. Mandatory Step 24 Robustness Re-Test (500 Adversarial Pairs)

| Model | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | False Positive Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Adv_LogReg_11_Scaled` | 0.7184 | 1.0000 | 0.8361 | 0.8515 | 0.7519 | 0.1937 | 0.3920 |
| `Adv_RandomForest_11` | 0.7937 | 1.0000 | 0.8850 | 0.9520 | 0.9556 | 0.0894 | 0.2600 |
| `Adv_HistGradientBoosting_11` | 0.8333 | 1.0000 | 0.9091 | 0.9700 | 0.9434 | 0.0996 | 0.2000 |
| `Adv_Calibrated_RF_11` | 0.7937 | 1.0000 | 0.8850 | 0.9771 | 0.9766 | 0.0995 | 0.2600 |

## 3. Cross-Stage Evolution (Step 22 vs Step 23 vs Step 24 vs Step 25)

| Stage | Model | Evaluation Corpus | Precision | Recall | F1 Score | ROC-AUC | FPR |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Step 22 Baseline | `LogReg_7_Baseline` | Normal Test (155 pairs) | 0.9000 | 0.6154 | 0.7310 | 0.7584 | 0.2105 |
| Step 23 Expanded | `LogReg_11_Scaled` | Normal Test (155 pairs) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Step 23 Expanded | `RandomForest_11` | Normal Test (155 pairs) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Step 24 Stress | `LogReg_11_Scaled` | Step 24 Robustness (500 pairs) | 0.5000 | 1.0000 | 0.6667 | 0.6000 | 1.0000 |
| Step 24 Stress | `RandomForest_11` | Step 24 Robustness (500 pairs) | 0.6849 | 1.0000 | 0.8130 | 0.8256 | 0.4600 |
| Step 25 Adversarial | `Adv_LogReg_11_Scaled` | Step 24 Robustness (500 pairs) | 0.7184 | 1.0000 | 0.8361 | 0.8515 | 0.3920 |
| Step 25 Adversarial | `Adv_RandomForest_11` | Step 24 Robustness (500 pairs) | 0.7937 | 1.0000 | 0.8850 | 0.9520 | 0.2600 |
| Step 25 Adversarial | `Adv_HistGradientBoosting_11` | Step 24 Robustness (500 pairs) | 0.8333 | 1.0000 | 0.9091 | 0.9700 | 0.2000 |
| Step 25 Adversarial | `Adv_Calibrated_RF_11` | Step 24 Robustness (500 pairs) | 0.7937 | 1.0000 | 0.8850 | 0.9771 | 0.2600 |

## 4. Controlled Feature Ablation on Adversarially Trained Models

| Configuration | Feat Count | Precision (Robustness) | Recall (Robustness) | F1 Score | ROC-AUC | Brier Loss | FPR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Baseline_7_Features` | 7 | 0.6829 | 0.8960 | 0.7751 | 0.6877 | 0.2157 | 0.4160 |
| `7_Plus_Evidence_Diversity` | 8 | 0.6707 | 0.8960 | 0.7671 | 0.6796 | 0.2300 | 0.4400 |
| `7_Plus_Case_Cooccurrence` | 8 | 0.7225 | 1.0000 | 0.8389 | 0.7894 | 0.1816 | 0.3840 |
| `7_Plus_Bidirectional_Activity` | 8 | 0.7105 | 0.9720 | 0.8209 | 0.8225 | 0.1941 | 0.3960 |
| `7_Plus_Transaction_Volume` | 8 | 0.7025 | 0.9920 | 0.8226 | 0.6781 | 0.2162 | 0.4200 |
| `All_11_Features` | 11 | 0.7184 | 1.0000 | 0.8361 | 0.8515 | 0.1937 | 0.3920 |