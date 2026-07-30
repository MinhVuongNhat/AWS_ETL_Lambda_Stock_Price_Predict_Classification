---
title : "API & Dashboard"
date: ""
weight : 5
chapter : false
pre : " <b> 5.5. </b> "
---

#### API & Dashboard

After completing the pipeline and deploying the Lambda Predictor, you can access predictions via two channels:

---

#### 5.1 — AWS API Gateway REST API

Lambda `nasdaq-stock-predictor` is exposed via **AWS API Gateway** as a REST endpoint:

**Endpoint:** `POST https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/prod/predict`

**Request:**
```json
{"ticker": "AAPL"}
```

**Response:**
```json
{
    "ticker": "AAPL",
    "prediction": 1,
    "probability": 0.623,
    "label": "UP",
    "date": "2026-07-29"
}
```

![Api Gateway Test](/images/5/api-gateway-test.png)

---

#### 5.2 — Streamlit Dashboard (Local)

```bash
streamlit run dashboard/streamlit_app.py
```

Open browser at `http://localhost:8501`.

![Dashboard Top Buy](/images/5/dashboard-top-buy.png)

![Dashboard Ticker Detail](/images/5/dashboard-ticker-detail.png)

---

#### 5.3 — Lambda Functions Summary

| Lambda Function | Handler | Memory | Timeout | Trigger |
|:---|:---|:---|:---|:---|
| `nasdaq-daily-collector` | `src.lambda_daily_collector.lambda_handler` | 512 MB | 5 min | EventBridge daily |
| `nasdaq-collector-producer` | `src.lambda_collector_producer.lambda_handler` | 1024 MB | 15 min | SQS trigger |
| `nasdaq-quality-gate` | `src.lambda_quality_gate.lambda_handler` | 512 MB | 5 min | S3 Event |
| `nasdaq-daily-etl` | `src.lambda_daily_etl.lambda_handler` | 3008 MB | 15 min | S3 Event |
| `nasdaq-stock-predictor` | `src.lambda_stock_predictor.lambda_handler` | 2048 MB | 30 sec | API Gateway |
