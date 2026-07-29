---
title : "API & Dashboard"
date: ""
weight : 5
chapter : false
pre : " <b> 5. </b> "
---

#### API & Dashboard

Sau khi hoàn thành pipeline và deploy Lambda Predictor, bạn có thể truy cập kết quả dự đoán qua hai kênh:

---

#### 5.1 — AWS API Gateway REST API

Lambda `nasdaq-stock-predictor` được expose qua **AWS API Gateway** như một REST endpoint:

**Endpoint:** `POST https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/prod/predict`

**Request:**
```json
{
    "ticker": "AAPL"
}
```

**Response:**
```json
{
    "ticker": "AAPL",
    "prediction": 1,
    "probability": 0.623,
    "label": "UP",
    "date": "2026-07-29",
    "features": {
        "RSI_14": 58.3,
        "MACD": 1.24,
        "BB_Width": 0.043
    }
}
```

Test API bằng curl:
```bash
curl -X POST \
    "https://<api-id>.execute-api.ap-southeast-1.amazonaws.com/prod/predict" \
    -H "Content-Type: application/json" \
    -d '{"ticker": "AAPL"}'
```

> *[TODO: Thêm ảnh màn hình API Gateway đang test — `/images/5/api-gateway-test.png`]*

---

#### 5.2 — Streamlit Dashboard (Local)

Chạy Dashboard tương tác Streamlit tại local:

```bash
streamlit run dashboard/streamlit_app.py
```

Mở trình duyệt tại `http://localhost:8501`.

Dashboard gồm hai trang:
- **Trang 1 — Top Buy Signals:** Danh sách các mã cổ phiếu có xác suất tăng cao nhất theo mô hình ML.
- **Trang 2 — Chi tiết Mã:** Biểu đồ kỹ thuật, chỉ báo và lịch sử dự đoán của một mã cụ thể.

> *[TODO: Thêm ảnh màn hình Dashboard Trang 1 — Top Buy Signals — `/images/5/dashboard-top-buy.png`]*

> *[TODO: Thêm ảnh màn hình Dashboard Trang 2 — Chi tiết mã AAPL — `/images/5/dashboard-ticker-detail.png`]*

---

#### 5.3 — Bảng Lambda Functions tổng hợp

| Lambda Function | Handler | Memory | Timeout | Trigger |
|:---|:---|:---|:---|:---|
| `nasdaq-daily-collector` | `src.lambda_daily_collector.lambda_handler` | 512 MB | 5 phút | EventBridge daily |
| `nasdaq-collector-producer` | `src.lambda_collector_producer.lambda_handler` | 1024 MB | 15 phút | SQS trigger |
| `nasdaq-quality-gate` | `src.lambda_quality_gate.lambda_handler` | 512 MB | 5 phút | S3 Event |
| `nasdaq-daily-etl` | `src.lambda_daily_etl.lambda_handler` | 3008 MB | 15 phút | S3 Event |
| `nasdaq-stock-predictor` | `src.lambda_stock_predictor.lambda_handler` | 2048 MB | 30 giây | API Gateway |
