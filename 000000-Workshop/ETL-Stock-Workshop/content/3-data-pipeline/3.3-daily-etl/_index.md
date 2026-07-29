---
title : "Lambda Daily ETL"
date: ""
weight : 3
chapter : false
pre : " <b> 3.3 </b> "
---

#### Lambda Daily ETL — Parquet Aggregation

`lambda_daily_etl.py` is the final step of Pipeline B. It reads all data from the `cleansed_daily/YYYY-MM-DD/` buffer, applies **Feature Engineering**, and merges it into the main yearly Parquet file (`processed/YYYY.parquet`).

---

#### Processing Flow

```
S3 cleansed_daily/YYYY-MM-DD/
         │
         ▼
  lambda_daily_etl
         │
    1. Read cleansed data from buffer
    2. Load current year: processed/YYYY.parquet
    3. Merge & Deduplicate (prefer latest data)
    4. Recalculate Feature Engineering (Polars)
    5. Write back: processed/YYYY.parquet
    6. Delete cleansed_daily/ buffer
         │
         ▼
  S3 processed/YYYY.parquet (updated)
```

---

#### Parquet Structure After Feature Engineering

Each `processed/YYYY.parquet` file contains:

| Group | Columns |
|:---|:---|
| **Raw OHLCV** | `Date`, `Symbol`, `Open`, `High`, `Low`, `Close`, `Adj_Close`, `Volume` |
| **Trend** | `SMA_5`, `SMA_20`, `EMA_12`, `EMA_26` |
| **Momentum** | `MACD`, `MACD_Signal`, `MACD_Hist`, `RSI_14` |
| **Volatility** | `BB_Upper`, `BB_Lower`, `BB_Width`, `Intraday_Volatility` |
| **Lag & Return** | `Lag_Close_1`, `Lag_Close_2`, `Lag_Close_3`, `Daily_Return` |
| **Label** | `Label` (1=Up, 0=Down) |
