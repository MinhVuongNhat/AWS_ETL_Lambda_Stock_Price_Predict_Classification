---
title : "Train & Deploy Model"
date: ""
weight : 2
chapter : false
pre : " <b> 5.4.2. </b> "
---

#### Train & Deploy XGBoost Model

---

#### Step 1: Train Model Locally

```bash
python train_model.py
```

The script:
1. Loads all `processed/YYYY.parquet` files from S3.
2. Drops rows with null values (insufficient history for rolling windows).
3. Splits data chronologically — **70% Train / 30% Test** (no shuffle to prevent data leakage).
4. Trains `XGBoostClassifier`.
5. Evaluates and exports `training_report.md`.
6. Saves `xgboost_model.json` to the S3 Model Bucket.

---

#### Training Results

| Metric | Value |
|:---|:---|
| **Accuracy** | 53.12% |
| **Precision** | 0.5311 |
| **Recall** | 0.4828 |
| **F1 Score** | 0.5058 |
| **AUC-ROC** | 0.5487 |

> *[TODO: Add Confusion Matrix chart — `/images/4.2/confusion-matrix.png`]*

> *[TODO: Add Feature Importance chart — `/images/4.2/feature-importance.png`]*

---

#### Step 2: Deploy Lambda Predictor

- **Function name:** `nasdaq-stock-predictor`
- **CMD override:** `src.lambda_stock_predictor.lambda_handler`
- **Memory:** `2048 MB`
- **Timeout:** `30 seconds`

The predictor returns:

```json
{
    "ticker": "AAPL",
    "prediction": 1,
    "probability": 0.623,
    "label": "UP",
    "date": "2026-07-29"
}
```

> *[TODO: Add API Gateway endpoint configuration screenshot — `/images/4.2/api-gateway-endpoint.png`]*
