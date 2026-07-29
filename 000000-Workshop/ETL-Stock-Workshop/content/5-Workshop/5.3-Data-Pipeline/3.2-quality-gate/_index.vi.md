---
title : "Lambda Quality Gate"
date: ""
weight : 2
chapter : false
pre : " <b> 5.3.2. </b> "
---

#### Lambda Quality Gate — Kiểm duyệt & Cách ly Dữ liệu

`lambda_quality_gate.py` nhận dữ liệu thô từ S3 Raw và kiểm duyệt nghiêm ngặt trước khi cho vào pipeline xử lý tiếp theo.

> *[TODO: Thêm ảnh sơ đồ luồng Quality Gate — `/images/3.2/quality-gate-flow.png`]*

---

#### Cơ chế hoạt động

```
S3 Raw Data
     │
     ▼
lambda_quality_gate
     │
     ├── ✅ Hợp lệ → S3 cleansed_daily/YYYY-MM-DD/
     │
     └── ❌ Lỗi   → S3 quarantine/YYYY-MM-DD/
```

---

#### Các quy tắc kiểm duyệt

`src/validator.py` thực hiện các kiểm tra sau:

| Loại kiểm tra | Quy tắc |
|:---|:---|
| **Schema Check** | Đảm bảo đủ các cột: `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`, `Volume` |
| **Giá trị âm** | Loại bỏ records có `Close < 0` hoặc `Volume < 0` |
| **Tính hợp lệ OHLC** | Kiểm tra `High >= Low`, `High >= Open`, `High >= Close` |
| **Null/NaN Check** | Lọc mã có tỷ lệ dữ liệu null vượt ngưỡng cho phép |

---

#### Bước 1: Tạo Lambda Function

- **Function name:** `nasdaq-quality-gate`
- **CMD override:** `src.lambda_quality_gate.lambda_handler`
- **Memory:** `512 MB`
- **Timeout:** `5 phút`

Biến môi trường:

| Key | Value |
|:---|:---|
| `RAW_BUCKET` | `my-nasdaq-stock-market-raw-2026-ap-southeast-1` |
| `PROCESSED_BUCKET` | `my-nasdaq-stock-processed-2026-ap-southeast-1` |
| `CLEANSED_DAILY_PREFIX` | `cleansed_daily/` |
| `QUARANTINE_PREFIX` | `quarantine/` |

> *[TODO: Thêm ảnh màn hình Lambda Quality Gate configuration — `/images/3.2/lambda-quality-gate-config.png`]*

---

#### Bước 2: Kiểm tra Quarantine Bucket

Sau khi pipeline chạy, kiểm tra dữ liệu bị cách ly:

```bash
aws s3 ls s3://my-nasdaq-stock-processed-2026-ap-southeast-1/quarantine/ --recursive
```

Mỗi file trong `quarantine/` chứa metadata về lý do bị loại:

```json
{
    "ticker": "XYZ",
    "date": "2026-07-29",
    "reason": "OHLC_INVALID: High < Low detected",
    "row_count": 1
}
```

{{%notice tip%}}
Dữ liệu trong `quarantine/` không bị xóa — bạn có thể kiểm tra lại để debug và cải thiện quy tắc kiểm duyệt.
{{%/notice%}}

> *[TODO: Thêm ảnh S3 Console hiển thị file trong quarantine/ — `/images/3.2/s3-quarantine-files.png`]*
