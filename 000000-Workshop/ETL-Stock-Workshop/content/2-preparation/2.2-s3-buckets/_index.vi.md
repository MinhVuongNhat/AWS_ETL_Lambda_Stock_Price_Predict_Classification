---
title : "Tạo S3 Buckets"
date: ""
weight : 2
chapter : false
pre : " <b> 2.2 </b> "
---

#### Tạo S3 Buckets

Dự án sử dụng **4 S3 Bucket** để lưu trữ các loại dữ liệu khác nhau trong pipeline:

| Bucket | Mục đích |
|:---|:---|
| `Raw Bucket` | Lưu dữ liệu thô cào từ Yahoo Finance (JSON/Parquet) vào prefix `raw/` |
| `Processed Bucket` | Lưu dữ liệu đã qua Feature Engineering, dữ liệu sạch (`cleansed_daily/`), và báo cáo (`reports/`) |
| `Model Bucket` | Lưu file mô hình XGBoost đã huấn luyện (`models/xgboost_v1/`) |
| `Simulation Bucket` | Môi trường sandbox riêng biệt cho Replay Simulator |

{{%notice info%}}
**Lưu ý:** `Quarantine Bucket` và `Cleansed Bucket` mặc định dùng chung với `Processed Bucket` nhưng ở các prefix khác nhau (`quarantine/` và `cleansed/`). Bạn có thể tách ra bucket riêng nếu muốn.
{{%/notice%}}

---

#### Bước 1: Tạo Buckets bằng AWS CLI

Chạy lần lượt các lệnh sau trong terminal (thay `<YOUR_ACCOUNT_ID>` bằng Account ID thực tế của bạn):

```bash
# Raw Bucket — lưu dữ liệu thô từ Yahoo Finance
aws s3 mb s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1 \
    --region ap-southeast-1

# Processed Bucket — lưu dữ liệu đã xử lý (Parquet), cleansed_daily, reports, quarantine
aws s3 mb s3://my-nasdaq-stock-processed-2026-ap-southeast-1 \
    --region ap-southeast-1

# Model Bucket — lưu mô hình XGBoost
aws s3 mb s3://my-nasdaq-stock-models-2026-ap-southeast-1 \
    --region ap-southeast-1

# Simulation Bucket — sandbox cho Replay Simulator
aws s3 mb s3://my-nasdaq-stock-simulation-2026-ap-southeast-1 \
    --region ap-southeast-1
```

> *[TODO: Thêm ảnh màn hình S3 buckets đã tạo thành công — `/images/2.2/s3-buckets-created.png`]*

---

#### Bước 2: Kiểm tra Buckets

```bash
aws s3 ls | grep my-nasdaq
```

Kết quả mong đợi:

```
2026-07-29 10:00:00 my-nasdaq-stock-market-raw-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-models-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-processed-2026-ap-southeast-1
2026-07-29 10:00:00 my-nasdaq-stock-simulation-2026-ap-southeast-1
```

---

#### Bước 3: Upload danh sách Tickers lên S3

File `tickers.json` chứa danh sách hơn **3,000+ mã cổ phiếu NASDAQ** cần theo dõi. Upload lên S3:

```bash
python upload_tickers_config.py --file tickers.json
```

> *[TODO: Thêm ảnh màn hình file tickers.json đã upload lên S3 — `/images/2.2/s3-tickers-uploaded.png`]*

{{%notice tip%}}
Bạn có thể cập nhật danh sách mã cổ phiếu mới nhất từ NASDAQ bằng lệnh:
```bash
python refresh_tickers_from_nasdaq.py
```
{{%/notice%}}

---

#### Cấu trúc thư mục S3 sau khi setup

```
processed-bucket/
├── config/
│   └── tickers.json           ← Danh sách ticker cần theo dõi
├── raw/                       ← Dữ liệu thô từ Yahoo Finance
├── cleansed_daily/            ← Buffer dữ liệu đã qua Quality Gate (xóa sau khi ETL)
│   └── YYYY-MM-DD/
├── processed/                 ← Kho dữ liệu chính theo năm
│   ├── 2024.parquet
│   └── 2025.parquet
├── quarantine/                ← Dữ liệu lỗi bị cách ly
│   └── YYYY-MM-DD/
├── reports/                   ← Báo cáo chất lượng dữ liệu
└── models/                    ← Mô hình XGBoost đã huấn luyện
    └── xgboost_v1/
        └── xgboost_model.json
```
