---
title : "AWS ETL Dự đoán Giá Cổ Phiếu"
date: ""
weight : 1
chapter : false
---

# AWS Serverless ETL Pipeline & Dự đoán Giá Cổ Phiếu NASDAQ

### Tổng quan

Trong workshop này, bạn sẽ xây dựng một **hệ thống Big Data Pipeline hoàn toàn tự động trên nền Serverless của AWS** để thu thập, xử lý và phân loại xu hướng giá cổ phiếu sàn NASDAQ sử dụng Machine Learning (XGBoost).

Hệ thống bao gồm các thành phần chính:

- **Thu thập dữ liệu tự động** từ Yahoo Finance API qua AWS Lambda & SQS Fan-Out Pattern.
- **Kiểm duyệt & làm sạch dữ liệu** bằng Quality Gate & Quarantine cơ chế.
- **Trích xuất đặc trưng kỹ thuật** (Feature Engineering) với thư viện Polars và lưu trữ dạng Apache Parquet.
- **Huấn luyện mô hình XGBoost Classifier** phân loại xu hướng tăng/giảm.
- **Phục vụ dự đoán Real-time** qua AWS API Gateway & Streamlit Dashboard.

> **📌 GHI CHÚ:** Vị trí này cần thêm ảnh sơ đồ kiến trúc hệ thống.
>
> *[TODO: Thêm ảnh kiến trúc tổng quan — ví dụ: `/images/0-home/architecture-overview.png`]*

### Nội dung

 1. [Giới thiệu](1-introduce/)
 2. [Các bước chuẩn bị](2-preparation/)
 3. [Data Pipeline](3-data-pipeline/)
 4. [Machine Learning](4-ml-model/)
 5. [API & Dashboard](5-api-dashboard/)
 6. [Dọn dẹp tài nguyên](6-cleanup/)
