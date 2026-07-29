---
title : "Huấn luyện & Deploy Mô hình"
date: ""
weight : 2
chapter : false
pre : " <b> 4.2 </b> "
---

#### Huấn luyện & Deploy Mô hình XGBoost

---

#### Bước 1: Huấn luyện Mô hình Local

Script `train_model.py` thực hiện toàn bộ pipeline huấn luyện:

```bash
python train_model.py
```

Script sẽ:
1. Tải tất cả file `processed/YYYY.parquet` từ S3.
2. Loại bỏ các dòng có giá trị null (dữ liệu không đủ lịch sử cho rolling window).
3. Chia dữ liệu theo thời gian — **70% Train / 30% Test** (không shuffle để tránh data leakage).
4. Huấn luyện `XGBoostClassifier`.
5. Đánh giá mô hình và xuất báo cáo `training_report.md`.
6. Lưu file mô hình `xgboost_model.json` lên S3 Model Bucket.

---

#### Thuật toán & Hyperparameters

```python
XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
```

---

#### Kết quả Huấn luyện

> *[TODO: Thêm ảnh biểu đồ Confusion Matrix — `/images/4.2/confusion-matrix.png`]*

> *[TODO: Thêm ảnh biểu đồ Feature Importance — `/images/4.2/feature-importance.png`]*

> *[TODO: Thêm ảnh biểu đồ ROC Curve — `/images/4.2/roc-curve.png`]*

| Chỉ số | Giá trị |
|:---|:---|
| **Accuracy** | 53.12% |
| **Precision** | 0.5311 |
| **Recall** | 0.4828 |
| **F1 Score** | 0.5058 |
| **AUC-ROC** | 0.5487 |

{{%notice info%}}
**Tại sao Accuracy chỉ ~53%?**

Dự đoán xu hướng thị trường chứng khoán là bài toán cực kỳ khó do thị trường gần như là **Random Walk**. Một mô hình đạt >52% trên dữ liệu unseen (test set đúng thời gian) là đã có giá trị thực tế cho chiến lược giao dịch thống kê.
{{%/notice%}}

---

#### Bước 2: Deploy Lambda Predictor

- **Function name:** `nasdaq-stock-predictor`
- **CMD override:** `src.lambda_stock_predictor.lambda_handler`
- **Memory:** `2048 MB`
- **Timeout:** `30 giây`

Biến môi trường:

| Key | Value |
|:---|:---|
| `MODEL_BUCKET` | `my-nasdaq-stock-models-2026-ap-southeast-1` |
| `PROCESSED_BUCKET` | `my-nasdaq-stock-processed-2026-ap-southeast-1` |

Lambda Predictor sẽ:
1. Load mô hình XGBoost từ S3.
2. Lấy dữ liệu mới nhất của ticker được yêu cầu.
3. Tính toán Feature Engineering.
4. Trả về xác suất dự đoán `P(Tăng)` và nhãn `1/0`.

> *[TODO: Thêm ảnh màn hình cấu hình Lambda Predictor — `/images/4.2/lambda-predictor-config.png`]*

---

#### Bước 3: Cấu hình API Gateway

Tạo REST API endpoint để gọi Lambda Predictor:

```
POST /predict
Body: {"ticker": "AAPL"}

Response:
{
    "ticker": "AAPL",
    "prediction": 1,
    "probability": 0.623,
    "label": "UP",
    "date": "2026-07-29"
}
```

> *[TODO: Thêm ảnh màn hình API Gateway endpoint đã cấu hình — `/images/4.2/api-gateway-endpoint.png`]*
