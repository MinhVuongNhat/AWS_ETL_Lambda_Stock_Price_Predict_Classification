---
title : "Proposal"
date: ""
weight : 2
chapter : false
pre : " <b> 2. </b> "
---

#### Project Proposal

*Project proposal detailing the background, core objectives, AWS cloud architecture, data warehouse model, backtesting engine, and expected outcomes.*

---

#### Project Overview Summary

| Field | Details |
|:---|:---|
| **Project Title** | END-TO-END DATA PIPELINE & BACKTESTING ENGINE FOR STOCK MARKET DIRECTION |
| **Authors** | Vương Nhật Minh - 2212094, Phạm Đức Hoài Nam - 2212157, Doãn Anh Khôi - 2352601, Trần Quốc Khánh - 2311538, Nguyễn Huy Lượng - 2311997 |
| **Supervisor** | Lữ Hoàn Thiện |
| **Start Date** | June 8, 2026 |
| **End Date** | July 31, 2026 |

---

### 1. Project Overview & Core Objectives

The system is designed to automate the complete end-to-end lifecycle from stock market data ingestion, data cleansing & standardization, machine learning model training, backtesting strategy simulation, to serving daily stock price directional predictions.

#### 1.1. Core Problem Statement
* **Objective:** Binary classification of next-day stock price directional movement T+1.
* **Target Label Definition:**
  * **Label 1 (Up / Bullish):** (T+1) > (T)
  * **Label 0 (Down or Bearish/Sideways):** (T+1) <= (T)

#### 1.2. Business Value Extension (Optional / Future Scope)
* **Top Stock Recommendation:** Rank and suggest top potential stock portfolios daily based on the model's prediction confidence scores.

#### 1.3. System Goals
* Fully automate the Data Pipeline and MLOps lifecycle on AWS cloud infrastructure.
* Provide a low-latency, interactive web dashboard for end-users via Streamlit.

---

### 2. System Architecture (AWS Architecture)

The solution operates on a Serverless Architecture decoupled into 2 independent sub-systems for maximum performance:

#### 2.1. Batch Data Pipeline & Training Subsystem
* **Data Validation & ETL Pipeline:**
  * **EventBridge** triggers `Lambda Downloader` at the end of each trading day.
  * **Lambda Downloader** fetches OHLCV market data from Yahoo Finance and uploads raw records to `S3 Raw Zone` formatted as Parquet files (`{SYMBOL}.parquet`).
  * Object creation in `raw/` triggers **S3 Event Notifications** to invoke `Lambda ETL`.
  * **Lambda ETL (Container Image):**
    1. Reads Parquet from S3 using **Polars**.
    2. Validates Schema with **Pandera**.
    3. Enforces business validation rules ($\text{High} \ge \text{Low}$, $\text{Open} > 0$, $\text{Close} > 0$, $\text{Volume} \ge 0$).
    4. Deduplicates records on `(Date, Symbol)`.
    5. Imputes missing values and standardizes data types.
    6. Aggregates data by year to reduce S3 object counts and optimize query throughput.
    7. Writes cleansed output to `S3 Processed Zone`.

```text
[Yahoo Finance] ──(EventBridge + Daily Lambda Collector)──> [S3 Raw Zone] (raw parquet)
                                                                 │
                                                      (S3 Event Notification)
                                                                 ▼
                                                           [Lambda ETL]
                                                                 │
                                                       (Validation Pandera)
                                                                 ▼
                                                  [S3 Processed Zone] (clean parquet)
                                                                 │
                                                    (Feature Engineering Polars)
                                                                 ▼
[Athena + Glue Catalog] <───────────────────────────── [S3 Feature Store]
           │                                                     │
           ▼                                                     ▼
     [QuickSight]                                    [Model Training] (XGBoost)
      *(Optional)                                                │
                                                                 ▼
                                                       [S3 Model Registry]
                                                                 │
                                                                 ▼
            [EventBridge] ──────trigger──────> [Lambda Batch Inference]
                                                                 │
                                                    (Daily Predictions & Storage)
                                                                 ▼
                                                            [DynamoDB]
                                                                 ▲
                                                                 │
                                                       [Lambda API Handler]
                                                                 ▲
                                                                 │
                                                           [API Gateway]
                                                                 ▲
                                                                 │
                                                     [Web Dashboard] (Streamlit)
```

#### 2.2. Inference & Serving Subsystem
* **Batch Inference:** EventBridge daily trigger launches Lambda to load the latest `model.pkl` from S3 \(\rightarrow\) Fetch latest features from Feature Store \(\rightarrow\) Run directional inference for all NASDAQ symbols \(\rightarrow\) Persist predictions with confidence scores into **Amazon DynamoDB**.
* **API Serving:** Users interact with the Streamlit Dashboard \(\rightarrow\) Requests sent to **AWS API Gateway** \(\rightarrow\) `Lambda API Handler` fetches directly from DynamoDB for sub-second latency response (eliminating real-time model inference overhead).

#### 2.3. Containerization (Containerized ETL Deployment)
`Lambda ETL` is containerized using **Docker** pushed to **Amazon ECR** instead of standard ZIP packages to accommodate heavy dependencies:
* `Polars` & `PyArrow`
* `Pandera` & `Scikit-Learn` / `XGBoost`

**Deployment Workflow:**
\[\text{Local Source Code} \longrightarrow \text{Docker Build} \longrightarrow \text{Amazon ECR} \longrightarrow \text{AWS Lambda Container} \longleftarrow \text{S3 Trigger}\]

#### 2.4. Lambda Project Structure
```text
Lambda ETL Architecture
├── lambda_function.py     # Entry Point
├── config.py              # Environment Variables & S3 Paths
├── validation/
│   ├── schemas.py         # Pandera Data Schemas
│   └── validator.py       # Data Quality Rules
├── transform/
│   └── cleaning.py        # Polars ETL & Indicators
├── services/
│   └── s3_service.py      # Boto3 S3 Helpers
└── utils/
    └── logger.py          # Structured Logger
```

---

### 3. Detailed Technical Components

#### 3.1. Data & Feature Engineering
* **Raw Input (OHLCV):** Open, High, Low, Close, Volume.
* **Engineered Feature Set:**
  * **Momentum & Trend:** SMA20, SMA50, EMA20, EMA50, MACD.
  * **Oscillators:** RSI (14 days).
  * **Volatility:** ATR (Average True Range), Volatility (20 days).
  * **Volume:** Volume Ratio (\(\text{Volume}_T / \text{SMA20}(\text{Volume})\)).
  * **Returns:** 1-day Return ($\text{Return}_1$), 5-day Return ($\text{Return}_5$).

#### 3.2. Data Warehouse (Star Schema Model)
* **Fact Tables:**
  * `FactPrice`: `Date` | `Symbol` | `Open` | `High` | `Low` | `Close` | `Volume`
  * `FactFeature`: `Date` | `Symbol` | `RSI` | `MACD` | `ATR` | `Target`
* **Dimension Tables:**
  * `DimDate`: `Date` | `Month` | `Quarter` | `Year`
  * `DimSymbol`: `Symbol` | `AssetType` (Stock/ETF) | `Sector`

#### 3.3. Financial Backtesting Engine
Simulates real-world financial performance based on model prediction signals:
* **Buy / Hold Signal:** Model predicts Label 1 (Bullish trend).
* **Sell / Cash Signal:** Model predicts Label 0 (Bearish / Sideways trend).
* **Evaluation Metrics:**
  * **Total Profit:** Net cumulative portfolio return.
  * **Win Rate:** Percentage of profitable trades out of total executed trades.
  * **Sharpe Ratio:** Risk-adjusted return metric.
  * **Max Drawdown:** Maximum peak-to-trough decline in portfolio equity (systemic risk assessment).
  * **Benchmark:** Direct performance comparison against a passive **Buy & Hold** strategy.
