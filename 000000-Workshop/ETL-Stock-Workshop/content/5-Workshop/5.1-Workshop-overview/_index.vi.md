---
title : "Tổng quan Workshop"
date: ""
weight : 1
chapter : false
pre : " <b> 5.1. </b> "
---

#### Workshop này về gì?

Workshop này hướng dẫn bạn xây dựng một **hệ thống Serverless Big Data Pipeline hoàn toàn tự động trên AWS** để dự đoán xu hướng giá cổ phiếu sàn NASDAQ bằng Machine Learning.

Bạn sẽ thực hành:
- Thiết kế **kiến trúc Fan-Out** sử dụng AWS Lambda kết hợp Amazon SQS.
- Xây dựng **Data Quality Gate** để kiểm duyệt và cách ly dữ liệu lỗi.
- Thực hiện **Feature Engineering** trên dữ liệu chuỗi thời gian tài chính bằng thư viện Polars.
- Huấn luyện và triển khai **XGBoost Classifier** để phân loại xu hướng giá cổ phiếu.
- Phục vụ dự đoán qua **AWS API Gateway** và hiển thị kết quả trên Dashboard.

---

#### Các dịch vụ AWS được sử dụng

| Dịch vụ | Vai trò |
|:---|:---|
| **AWS Lambda** | Thực thi serverless cho tất cả các giai đoạn pipeline |
| **Amazon S3** | Lưu trữ dữ liệu thô, đã làm sạch, đã xử lý và mô hình ML |
| **Amazon SQS** | Hàng đợi message cho xử lý song song Fan-Out |
| **Amazon EventBridge** | Kích hoạt cron hàng ngày để chạy pipeline |
| **Amazon API Gateway** | REST API phục vụ dự đoán ML |
| **Amazon ECR** | Registry Docker image cho Lambda Container |

---

#### Kiến trúc hệ thống

![Sơ đồ kiến trúc hệ thống](/images/1-introduce/system-architecture.png)

Pipeline gồm **ba luồng xử lý chính**:

{{%notice info%}}
**Pipeline A – Backfill Dữ liệu Lịch sử:** Thu thập dữ liệu cổ phiếu NASDAQ từ năm 1962 đến nay, thực hiện Feature Engineering và lưu dưới dạng file Apache Parquet theo từng năm (`processed/YYYY.parquet`) vào S3.
{{%/notice%}}

{{%notice info%}}
**Pipeline B – Cập nhật Hàng ngày:** Chạy mỗi ngày giao dịch — thu thập dữ liệu mới, kiểm duyệt qua Quality Gate, gộp vào kho dữ liệu Parquet và kích hoạt tính điểm lại mô hình.
{{%/notice%}}

{{%notice info%}}
**Pipeline C – Dự đoán & Phục vụ:** AWS Lambda nạp mô hình XGBoost đã huấn luyện từ S3 và phục vụ dự đoán real-time qua REST API và Dashboard.
{{%/notice%}}

---

#### Luồng xử lý của Workshop

Sau khi hoàn thành workshop này, bạn sẽ có một pipeline hoạt động đầu-cuối:

1. **EventBridge** kích hoạt `lambda_daily_collector` hàng ngày.
2. Collector đọc `tickers.json` và đẩy các chunk vào **SQS**.
3. `lambda_collector_producer` nhận SQS message và tải dữ liệu cổ phiếu từ **Yahoo Finance**.
4. `lambda_quality_gate` kiểm duyệt dữ liệu — dữ liệu hợp lệ vào `cleansed_daily/`, dữ liệu lỗi vào `quarantine/`.
5. `lambda_daily_etl` gộp dữ liệu đã làm sạch vào kho Parquet chính `processed/`.
6. `lambda_stock_predictor` nạp mô hình XGBoost và trả kết quả dự đoán qua **API Gateway**.

---

#### Mã nguồn & Repository

{{% notice tip %}}
💻 Toàn bộ mã nguồn dự án được công bố công khai trên GitHub. Clone về để thực hành cùng các bước trong workshop.
{{% /notice %}}

**Repository:** [MinhVuongNhat/AWS\_ETL\_Lambda\_Stock\_Price\_Predict\_Classification](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification)

```bash
git clone https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification.git
cd AWS_ETL_Lambda_Stock_Price_Predict_Classification
```

#### Cấu trúc thư mục dự án

```
AWS_ETL_Lambda_Stock_Price_Predict_Classification/
├── src/                          # Mã nguồn các Lambda function
│   ├── lambda_daily_collector.py    # Producer: chia tickers gửi vào SQS
│   ├── lambda_collector_producer.py # Consumer: tải dữ liệu cổ phiếu từ Yahoo Finance
│   ├── lambda_quality_gate.py       # Kiểm tra chất lượng dữ liệu & cách ly
│   ├── lambda_daily_etl.py          # Feature engineering & ghi Parquet
│   ├── lambda_stock_predictor.py    # Nạp mô hình XGBoost & dự đoán real-time
│   └── lambda_api_handler.py        # Xử lý REST API qua API Gateway
├── train_model.py                # Script huấn luyện mô hình ML (XGBoost)
├── dashboard/                    # Web Dashboard (Node.js / Vite / React)
├── tickers.json                  # Danh sách ~3.000 mã cổ phiếu NASDAQ
├── Dockerfile                    # Đóng gói Lambda Container Image
├── requirements.txt              # Các thư viện Python cần thiết
└── 000000-Workshop/              # Tài liệu Hugo workshop này
```

#### Các file nguồn quan trọng

| File | Mô tả |
|:---|:---|
| [`src/lambda_daily_collector.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_daily_collector.py) | Lambda Producer: đọc `tickers.json`, chia chunk và gửi vào SQS |
| [`src/lambda_collector_producer.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_collector_producer.py) | Lambda Consumer: tải dữ liệu cổ phiếu qua YFinance API |
| [`src/lambda_quality_gate.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_quality_gate.py) | Kiểm tra chất lượng dữ liệu bằng Pandera schema |
| [`src/lambda_daily_etl.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_daily_etl.py) | Feature engineering với Polars: SMA, EMA, RSI, MACD, Bollinger Bands |
| [`src/lambda_stock_predictor.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_stock_predictor.py) | Nạp mô hình XGBoost và dự đoán real-time |
| [`src/lambda_api_handler.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/src/lambda_api_handler.py) | Xử lý API Gateway: `/predictions/latest` và `/predictions/{symbol}` |
| [`train_model.py`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/train_model.py) | Pipeline ML đầy đủ: TimeSeriesSplit, huấn luyện XGBoost, đánh giá, upload S3 |
| [`Dockerfile`](https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification/blob/main/Dockerfile) | Định nghĩa Docker image để deploy Lambda Container lên ECR |
