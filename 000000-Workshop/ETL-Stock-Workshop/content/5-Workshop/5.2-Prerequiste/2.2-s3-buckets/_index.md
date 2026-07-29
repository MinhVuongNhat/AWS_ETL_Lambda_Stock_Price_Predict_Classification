---
title : "Create S3 Buckets"
date: ""
weight : 2
chapter : false
pre : " <b> 5.2.2. </b> "
---

#### Create S3 Buckets

The project uses **4 S3 Buckets** to store different types of data in the pipeline:

| Bucket | Purpose |
|:---|:---|
| `Raw Bucket` | Stores raw data scraped from Yahoo Finance (JSON/Parquet) under `raw/` prefix |
| `Processed Bucket` | Stores Feature-Engineered data, cleansed data (`cleansed_daily/`), and reports (`reports/`) |
| `Model Bucket` | Stores trained XGBoost model files (`models/xgboost_v1/`) |
| `Simulation Bucket` | A separate sandbox environment for the Replay Simulator |

{{%notice info%}}
**Note:** `Quarantine Bucket` and `Cleansed Bucket` share the `Processed Bucket` by default but under different prefixes (`quarantine/` and `cleansed/`). You can split them into separate buckets if desired.
{{%/notice%}}

---

#### Step 1: Create Buckets with AWS CLI

Run the following commands in your terminal:

```bash
# Raw Bucket — stores raw Yahoo Finance data
aws s3 mb s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1 \
    --region ap-southeast-1

# Processed Bucket — stores processed Parquet, cleansed_daily, reports, quarantine
aws s3 mb s3://my-nasdaq-stock-processed-2026-ap-southeast-1 \
    --region ap-southeast-1

# Model Bucket — stores trained XGBoost model
aws s3 mb s3://my-nasdaq-stock-models-2026-ap-southeast-1 \
    --region ap-southeast-1

# Simulation Bucket — sandbox for Replay Simulator
aws s3 mb s3://my-nasdaq-stock-simulation-2026-ap-southeast-1 \
    --region ap-southeast-1
```

> *[TODO: Add screenshot of S3 buckets successfully created — `/images/2.2/s3-buckets-created.png`]*

---

#### Step 2: Verify Buckets

```bash
aws s3 ls | grep my-nasdaq
```

Expected output:

```
2026-07-29 10:00:00 my-nasdaq-stock-market-raw-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-models-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-processed-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-simulation-2026-ap-southeast-1
```

---

#### Step 3: Upload Tickers List to S3

The `tickers.json` file contains **3,000+ NASDAQ tickers**. Upload it to S3:

```bash
python upload_tickers_config.py --file tickers.json
```

> *[TODO: Add screenshot of tickers.json uploaded in S3 — `/images/2.2/s3-tickers-uploaded.png`]*

{{%notice tip%}}
Refresh the ticker list with the latest NASDAQ tickers using:
```bash
python refresh_tickers_from_nasdaq.py
```
{{%/notice%}}
