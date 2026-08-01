---
title : "Tự đánh giá"
date: ""
weight : 6
chapter : false
pre : " <b> 6. </b> "
---

#### Tự đánh giá

*Đánh giá cá nhân về kết quả học tập, kỹ năng kỹ thuật đạt được, quyết định kiến trúc và bài học kinh nghiệm trong suốt 8 tuần thực hiện dự án Big Data ETL & Machine Learning trên AWS.*

---

#### Bảng tự đánh giá kỹ năng kỹ thuật

| Kỹ năng / Công nghệ | Mức độ trước dự án | Mức độ sau dự án | Thu hoạch & Kỹ năng đạt được |
|:---|:---:|:---:|:---|
| **AWS Lambda** | Cơ bản | Nâng cao | Nắm vững mô hình Serverless, biến môi trường, quản lý Timeout, giới hạn Concurrency và đóng gói Docker ECR. |
| **Amazon S3** | Cơ bản | Trung cấp | Thiết kế kiến trúc lưu trữ 4 tầng (`raw/`, `cleansed/`, `processed/`, `quarantine/`) và tối ưu định dạng Snappy Parquet. |
| **Amazon SQS** | Mới bắt đầu | Trung cấp | Áp dụng mô hình thiết kế Fan-Out với hàng đợi SQS batching, giải quyết hoàn toàn lỗi Lambda 15 phút Timeout. |
| **Amazon EventBridge** | Mới bắt đầu | Trung cấp | Cấu hình lịch biểu tự động (`cron(0 22 ? * MON-FRI *)`) để kích hoạt luồng cào dữ liệu chứng khoán hàng ngày. |
| **Amazon API Gateway** | Mới bắt đầu | Trung cấp | Xây dựng REST API tích hợp Lambda Proxy integration, xử lý CORS và phục vụ truy vấn dự đoán real-time. |
| **Amazon ECR / Docker** | Mới bắt đầu | Trung cấp | Đóng gói các thư viện Python nặng (Polars, PyArrow, Pandera, XGBoost) thành Docker Container Image tải lên ECR. |
| **Feature Engineering** | Trung cấp | Nâng cao | Tính toán 16 chỉ báo kỹ thuật tài chính (SMA, EMA, RSI, MACD, Bollinger Bands, Volatility) tránh lỗi Look-ahead bias. |
| **XGBoost / Machine Learning** | Trung cấp | Nâng cao | Huấn luyện mô hình phân loại nhị phân, đánh giá chỉ số (AUC-ROC, Precision, Recall, F1), xử lý mất cân bằng nhãn. |
| **Polars / Apache Parquet** | Mới bắt đầu | Nâng cao | Làm chủ thư viện Polars (Rust-based) tăng tốc độ xử lý dữ liệu gấp 10-50 lần so với Pandas truyền thống. |

---

#### Nhận xét tổng thể dự án

##### 1. Những điều đã làm tốt (Thành công chính)
* **Khả năng mở rộng & Chi phí:** Xử lý thành công dữ liệu của hơn 3,000+ mã cổ phiếu NASDAQ song song bằng mô hình Fan-Out (EventBridge + SQS + Lambda) với chi phí AWS xấp xỉ 0 (nằm trong Free Tier).
* **Quản lý chất lượng dữ liệu (Data Quality):** Xây dựng thành công cơ chế Quality Gate (`validator.py` + S3 `quarantine/`) tự động lọc và cách ly bản ghi rác mà không làm ngắt ngắt kết nối luồng ETL.
* **Tối ưu hiệu năng bộ nhớ:** Chuyển đổi toàn bộ từ Pandas/CSV sang Polars/Parquet giúp giảm đáng kể thời gian I/O và dung lượng bộ nhớ RAM trong quá trình trích xuất đặc trưng.
* **Tự động hóa End-to-End:** Hoàn thành hệ thống Serverless hoàn chỉnh từ bước cào data thô đến phục vụ API Gateway và hiển thị trên Streamlit Dashboard.

##### 2. Những điểm cần cải thiện (Hướng phát triển)
* **Độ chính xác mô hình ML:** Chỉ số AUC-ROC hiện tại (~0.55) còn khiêm tốn; cần bổ sung thêm các đặc trưng vĩ mô (Macro-economics) hoặc phân tích cảm xúc tin tức (Sentiment Analysis) để tăng độ chính xác.
* **Infrastructure as Code (IaC):** Các tài nguyên AWS hiện khởi tạo qua Console/CLI; cần nâng cấp sang sử dụng Terraform hoặc AWS CDK để tự động hóa khâu triển khai hạ tầng.
* **Tự động hóa CI/CD:** Tích hợp GitHub Actions để tự động build Docker Image và deploy Lambda code mỗi khi push code mới.

##### 3. Bài học kinh nghiệm quý giá
1. **Dữ liệu sạch là nền tảng:** Không bao giờ tin tưởng dữ liệu thô từ API bên ngoài; việc kiểm định dữ liệu nghiêm ngặt ngay từ đầu giúp tiết kiệm hàng chục giờ debug mô hình ML về sau.
2. **Hiểu rõ giới hạn Serverless:** Việc nắm vững giới hạn Memory và Timeout của AWS Lambda là yếu tố quyết định khi thiết kế hệ thống Big Data—chia nhỏ công việc qua SQS Queue là chìa khóa xử lý batch lớn.
3. **Lựa chọn công cụ phù hợp:** Việc chuyển từ Pandas sang Polars làm giảm thời gian chạy từ hàng chục phút xuống vài giây, minh chứng cho tầm quan trọng của việc chọn đúng Data Stack.
