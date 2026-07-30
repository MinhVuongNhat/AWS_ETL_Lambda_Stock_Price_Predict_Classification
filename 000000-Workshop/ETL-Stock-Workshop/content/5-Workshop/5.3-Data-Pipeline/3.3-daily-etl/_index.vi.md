---
title : "Lambda Daily ETL"
date: ""
weight : 3
chapter : false
pre : " <b> 5.3.3. </b> "
---

#### Lambda Daily ETL — Tổng hợp Parquet

`lambda_daily_etl.py` là bước cuối của Pipeline B. Lambda này đọc toàn bộ dữ liệu từ buffer `cleansed_daily/YYYY-MM-DD/`, thực hiện **Feature Engineering** và gộp vào file Parquet chính theo năm (`processed/YYYY.parquet`).

---

#### Luồng xử lý

```
S3 cleansed_daily/YYYY-MM-DD/
         │
         ▼
  lambda_daily_etl
         │
    1. Đọc dữ liệu sạch từ buffer
    2. Load năm hiện tại: processed/YYYY.parquet
    3. Merge & Deduplicate (ưu tiên dữ liệu mới)
    4. Recalculate Feature Engineering (Polars)
    5. Ghi lại: processed/YYYY.parquet
    6. Xóa buffer cleansed_daily/
         │
         ▼
  S3 processed/YYYY.parquet (đã cập nhật)
```

---

#### Bước 1: Tạo Lambda Function

- **Function name:** `nasdaq-daily-etl`
- **CMD override:** `src.lambda_daily_etl.lambda_handler`
- **Memory:** `3008 MB` (cần nhiều RAM cho Polars xử lý Parquet lớn)
- **Timeout:** `15 phút`

Biến môi trường:

| Key | Value |
|:---|:---|
| `PROCESSED_BUCKET` | `my-nasdaq-stock-processed-2026-ap-southeast-1` |
| `CLEANSED_DAILY_PREFIX` | `cleansed_daily/` |
| `PROCESSED_PREFIX` | `processed/` |

![Lambda Daily Etl Config](/images/3.3/lambda-daily-etl-config.png)

---

#### Bước 2: Kiểm tra kết quả

Sau khi Lambda chạy thành công, file Parquet phải được cập nhật:

```bash
aws s3 ls s3://my-nasdaq-stock-processed-2026-ap-southeast-1/processed/
```

Kết quả mong đợi:
```
2026-07-29 01:30:00   1234567890 2026.parquet
2025-01-01 00:00:00   987654321  2025.parquet
...
```

{{%notice info%}}
**Tại sao dùng Polars thay vì Pandas?**

Polars sử dụng kiến trúc đa luồng native và Apache Arrow format, nhanh hơn Pandas **10-50 lần** khi xử lý dữ liệu lớn. Với hàng chục triệu dòng dữ liệu từ 3,000+ tickers qua 60 năm, hiệu năng là yếu tố then chốt.
{{%/notice%}}

---

#### Cấu trúc file Parquet sau Feature Engineering

Mỗi file `processed/YYYY.parquet` chứa các cột:

| Nhóm | Cột |
|:---|:---|
| **Raw OHLCV** | `Date`, `Symbol`, `Open`, `High`, `Low`, `Close`, `Adj_Close`, `Volume` |
| **Trend** | `SMA_5`, `SMA_20`, `EMA_12`, `EMA_26` |
| **Momentum** | `MACD`, `MACD_Signal`, `MACD_Hist`, `RSI_14` |
| **Volatility** | `BB_Upper`, `BB_Lower`, `BB_Width`, `Intraday_Volatility` |
| **Lag & Return** | `Lag_Close_1`, `Lag_Close_2`, `Lag_Close_3`, `Daily_Return` |
| **Label** | `Label` (1=Tăng, 0=Giảm) |
