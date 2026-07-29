---
title : "Giới thiệu"
date: ""
weight : 1
chapter : false
pre : " <b> 1. </b> "
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

> *[TODO: Thêm ảnh sơ đồ kiến trúc — `/images/1-introduce/system-architecture.png`]*

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
