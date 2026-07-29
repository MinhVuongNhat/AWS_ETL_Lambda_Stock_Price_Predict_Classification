---
title : "Workshop Overview"
date: ""
weight : 1
chapter : false
pre : " <b> 5.1. </b> "
---

#### What is this Workshop About?

This workshop guides you through building a **fully automated Serverless Big Data Pipeline** on AWS to predict NASDAQ stock price trends using Machine Learning.

You will practice:
- Designing a **Fan-Out Architecture** using AWS Lambda + SQS.
- Building a **Data Quality Gate** to validate and isolate bad data.
- Performing **Feature Engineering** on financial time-series data using Polars.
- Training and deploying an **XGBoost Classifier** to predict stock movements.
- Exposing predictions via **AWS API Gateway** and visualizing with a Dashboard.

---

#### AWS Services Used

| Service | Role |
|:---|:---|
| **AWS Lambda** | Serverless compute for all pipeline stages |
| **Amazon S3** | Storage for raw, cleansed, and processed data & models |
| **Amazon SQS** | Message queue for Fan-Out parallel processing |
| **Amazon EventBridge** | Daily cron trigger to kick off the pipeline |
| **Amazon API Gateway** | REST API to serve ML predictions |
| **Amazon ECR** | Docker image registry for Lambda containers |

---

#### System Architecture

> *[TODO: Add architecture diagram image — `/images/1-introduce/system-architecture.png`]*

The pipeline has **three main flows**:

{{%notice info%}}
**Pipeline A – Historical Backfill:** Collects historical NASDAQ stock data from 1962 to present, applies Feature Engineering, and stores it as yearly Apache Parquet files (`processed/YYYY.parquet`) in S3.
{{%/notice%}}

{{%notice info%}}
**Pipeline B – Daily Increment:** Runs every trading day — collects new data, validates it through a Quality Gate, appends to the processed Parquet, and triggers model re-scoring.
{{%/notice%}}

{{%notice info%}}
**Pipeline C – Prediction & Serving:** AWS Lambda loads the trained XGBoost model from S3 and serves real-time predictions via REST API and Dashboard.
{{%/notice%}}

---

#### Workshop Flow

After completing this workshop, you will have a running end-to-end pipeline:

1. **EventBridge** triggers `lambda_daily_collector` daily.
2. The collector reads `tickers.json` and pushes chunks to **SQS**.
3. `lambda_collector_producer` consumes SQS messages and fetches stock data from **Yahoo Finance**.
4. `lambda_quality_gate` validates data — valid data goes to `cleansed_daily/`, bad data to `quarantine/`.
5. `lambda_daily_etl` merges cleansed data into the main `processed/` Parquet store.
6. `lambda_stock_predictor` loads the XGBoost model and returns predictions via **API Gateway**.
