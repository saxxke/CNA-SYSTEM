# ML Model Benchmarking & Improvement Report (Step 23)

## 1. Executive Summary & Comparison Table

| Model | Features | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Brier Loss | FPR | Inference Time (ms/1k) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `LogReg_7_Baseline` | 7 | 0.9000 | 0.6154 | 0.7310 | 0.7584 | 0.8955 | 0.2054 | 0.2105 | 1.34 |
| `LogReg_11_Scaled` | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0003 | 0.0000 | 4.16 |
| `RandomForest_11` | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0176 | 0.0000 | 100.57 |
| `HistGradientBoosting_11` | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0001 | 0.0000 | 17.73 |
| `Calibrated_RF_11` | 11 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0002 | 0.0000 | 290.26 |

## 2. Threshold Performance Matrix (0.50, 0.60, 0.70, 0.80)

| Model | Metric | Th = 0.50 | Th = 0.60 | Th = 0.70 | Th = 0.80 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `LogReg_7_Baseline` | Precision | 0.9000 | 0.9130 | 0.9032 | 0.9167 |
| | Recall | 0.6154 | 0.5385 | 0.2393 | 0.1880 |
| | F1 Score | 0.7310 | 0.6774 | 0.3784 | 0.3121 |
| | False Positive Rate | 0.2105 | 0.1579 | 0.0789 | 0.0526 |
| `LogReg_11_Scaled` | Precision | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | Recall | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | F1 Score | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | False Positive Rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `RandomForest_11` | Precision | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | Recall | 1.0000 | 1.0000 | 1.0000 | 0.9231 |
| | F1 Score | 1.0000 | 1.0000 | 1.0000 | 0.9600 |
| | False Positive Rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `HistGradientBoosting_11` | Precision | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | Recall | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | F1 Score | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | False Positive Rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `Calibrated_RF_11` | Precision | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | Recall | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | F1 Score | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| | False Positive Rate | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 3. Entity Resolution Benchmark
- **Positive Alias Mutations Tested**: 200
- **Hard Negative Non-Matching Pairs Tested**: 200
- **Average Positive String Similarity**: 0.7412
- **Average Hard Negative Similarity**: 0.3819

| Decision Tier | Threshold | Precision | Recall | F1 Score | TP | FP | TN | FN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `POSSIBLE_MATCH` | $\ge 0.65$ | 0.9935 | 0.7600 | 0.8612 | 152 | 1 | 199 | 48 |
| `MATCH` | $\ge 0.85$ | 1.0000 | 0.1250 | 0.2222 | 25 | 0 | 200 | 175 |

- **False Matches on Hard Negatives**: 1 / 200
