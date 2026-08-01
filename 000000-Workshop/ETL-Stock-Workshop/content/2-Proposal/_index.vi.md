---
title : "Đề xuất dự án"
date: ""
weight : 2
chapter : false
pre : " <b> 2. </b> "
---

#### Đề xuất dự án

*Tài liệu đề xuất dự án chi tiết bao gồm tổng quan bài toán, mục tiêu cốt lõi, kiến trúc AWS Cloud, mô hình kho dữ liệu, bộ máy kiểm thử chiến lược Backtesting và kết quả mong đợi.*

---

#### Tóm tắt thông tin dự án

| Mục | Nội dung |
|:---|:---|
| **Tên dự án** | END-TO-END DATA PIPELINE & BACKTESTING ENGINE FOR STOCK MARKET DIRECTION |
| **Tác giả** | Vương Nhật Minh - 2212094, Phạm Đức Hoài Nam - 2212157, Doãn Anh Khôi - 2352601, Trần Quốc Khánh - 2311538, Nguyễn Huy Lượng - 2311997 |
| **Người hướng dẫn** | Lữ Hoàn Thiện |
| **Ngày bắt đầu** | 08/06/2026 |
| **Ngày kết thúc** | 31/07/2026 |

---

### 1. Tổng quan bài toán và Mục tiêu cốt lõi

Hệ thống được thiết kế nhằm tự động hóa toàn bộ chu trình từ thu thập dữ liệu chứng khoán, xử lý chuẩn hóa, huấn luyện mô hình học máy đến kiểm thử chiến lược (Backtesting) và đưa ra dự báo xu hướng giá cổ phiếu hằng ngày.

#### 1.1. Bài toán Core (Core Objective)
* **Mô tả:** Phân loại nhị phân xu hướng dịch chuyển giá cổ phiếu cho ngày giao dịch tiếp theo T+1.
* **Định nghĩa Nhãn (Target Label):**
  * **Label 1 (Tăng):** (T+1) > (T)
  * **Label 0 (Giảm hoặc Đi ngang):** (T+1) <= (T)

#### 1.2. Bài toán Mở rộng (Business Value Extension)
* **Top Stock Recommendation:** Xếp hạng và gợi ý danh mục cổ phiếu tiềm năng nhất trong ngày dựa trên xác suất chiến thắng (Confidence Score) đầu ra của mô hình Core.

#### 1.3. Mục tiêu Hệ thống
* Tự động hóa hoàn toàn Luồng dữ liệu (Data Pipeline) và chu trình MLOps trên nền tảng điện toán đám mây AWS.
* Cung cấp giao diện tương tác trực quan, độ trễ thấp cho người dùng cuối thông qua ứng dụng Streamlit Dashboard.

---

### 2. Kiến trúc Hệ thống (AWS Architecture)

Hệ thống vận hành dựa trên kiến trúc Serverless, chia làm 2 phân hệ độc lập nhằm tối ưu hiệu năng:

#### 2.1. Phân hệ Luồng dữ liệu & Huấn luyện (Batch Data Pipeline & Training)
* **Data Validation & ETL Pipeline:**
  * **EventBridge** kích hoạt `Lambda Downloader` vào cuối mỗi ngày giao dịch.
  * **Lambda Downloader** tải dữ liệu OHLCV từ Yahoo Finance và lưu trực tiếp vào `S3 Raw Zone` dưới định dạng Parquet (`{SYMBOL}.parquet`).
  * Khi có object mới trong thư mục `raw/`, **S3 Event Notification** tự động kích hoạt `Lambda ETL`.
  * **Lambda ETL (Container Image):**
    1. Đọc Parquet từ S3 bằng **Polars**.
    2. Kiểm tra schema bằng **Pandera**.
    3. Kiểm tra quy tắc nghiệp vụ ($\text{High} \ge \text{Low}$, $\text{Open} > 0$, $\text{Close} > 0$, $\text{Volume} \ge 0$).
    4. Loại bỏ bản ghi trùng lặp theo `(Date, Symbol)`.
    5. Xử lý Missing Values và chuẩn hóa kiểu dữ liệu.
    6. Gom các mã tổ chức lại theo năm nhằm giảm số lượng object trên S3 và tối ưu hiệu năng xử lý.
    7. Ghi kết quả sang `S3 Processed Zone`.

```text
[Yahoo Finance] ──(EventBridge + Lambda lấy data hàng ngày)──> [S3 Raw Zone] (raw parquet)
                                                                    │
                                                           (S3 Event Trigger)
                                                                    ▼
                                                              [Lambda ETL]
                                                                    │
                                                           (Validation Pandera)
                                                                    ▼
                                                     [S3 Processed Zone] (clean parquet)
                                                                    │
                                                      (Feature Engineering Polars)
                                                                    ▼
[Athena + Glue Catalog] <──────────────────────────────── [S3 Feature Store]
           │                                                        │
           ▼                                                        ▼
     [QuickSight]                                       [Local Training] (XGBoost)
      *(Optional)                                                   │
                                                                    ▼
                                                          [S3 Model Registry]
                                                                    │
                                                                    ▼
            [EventBridge] ──────trigger──────> [Lambda Batch Inference]
                                                                    │
                                                      (Dự đoán hàng ngày & Lưu kết quả)
                                                                    ▼
                                                               [DynamoDB]
                                                                    ▲
                                                                    │
                                                          [Lambda API Handler]
                                                                    ▲
                                                                    │
                                                              [API Gateway]
                                                                    ▲
                                                                    │
                                                    [Web Dashboard] (Streamlit)
```

#### 2.2. Phân hệ Dự đoán & Phục vụ Giao diện (Inference & Serving Pipeline)
* **Batch Inference:** Định kỳ hằng ngày, EventBridge trigger Lambda tải `model.pkl` mới nhất từ S3 \(\rightarrow\) Lấy các đặc trưng mới nhất từ Feature Store \(\rightarrow\) Thực hiện dự đoán xu hướng cho toàn bộ danh sách mã cổ phiếu \(\rightarrow\) Lưu kết quả kèm Confidence Score vào **Amazon DynamoDB**.
* **API Serving:** Người dùng tương tác trên Streamlit Dashboard \(\rightarrow\) Gửi yêu cầu qua **API Gateway** \(\rightarrow\) `Lambda API Handler` truy vấn trực tiếp từ DynamoDB để trả về kết quả ngay lập tức (giảm thiểu tối đa Latency so với việc chạy mô hình Real-time).

#### 2.3. Đóng gói Container (Containerized ETL Deployment)
`Lambda ETL` được đóng gói dưới dạng **Docker Container Image** tải lên **Amazon ECR** thay vì ZIP package nhằm hỗ trợ các thư viện có kích thước lớn như:
* `Polars` & `PyArrow`
* `Pandera` & `Scikit-Learn` / `XGBoost`

**Quy trình triển khai:**
\[\text{Local Source Code} \longrightarrow \text{Docker Build} \longrightarrow \text{Amazon ECR} \longrightarrow \text{AWS Lambda Container} \longleftarrow \text{S3 Trigger}\]

#### 2.4. Cấu trúc Mô-đun Lambda
```text
Lambda ETL Architecture
├── lambda_function.py     # Entry Point
├── config.py              # Biến môi trường & Đường dẫn S3
├── validation/
│   ├── schemas.py         # Pandera Data Schemas
│   └── validator.py       # Quy tắc kiểm định Data Quality
├── transform/
│   └── cleaning.py        # Polars ETL & Làm sạch dữ liệu
├── services/
│   └── s3_service.py      # Module tương tác Boto3 S3
└── utils/
    └── logger.py          # Log hệ thống
```

---

### 3. Chi tiết các Thành phần Kỹ thuật

#### 3.1. Dữ liệu và Feature Engineering
* **Dữ liệu đầu vào (OHLCV):** Open, High, Low, Close, Volume.
* **Danh sách Đặc trưng (Features):**
  * **Momentum & Trend:** SMA20, SMA50, EMA20, EMA50, MACD.
  * **Oscillators:** RSI (14 days).
  * **Volatility:** ATR (Average True Range), Volatility (20 days).
  * **Volume:** Volume Ratio (\(\text{Volume}_T / \text{SMA20}(\text{Volume})\)).
  * **Returns:** Return_1 (Lợi nhuận 1 ngày), Return_5 (Lợi nhuận 5 ngày).

#### 3.2. Kho dữ liệu (Data Warehouse Star Schema)
* **Fact Tables:**
  * `FactPrice`: `Date` | `Symbol` | `Open` | `High` | `Low` | `Close` | `Volume`
  * `FactFeature`: `Date` | `Symbol` | `RSI` | `MACD` | `ATR` | `Target`
* **Dimension Tables:**
  * `DimDate`: `Date` | `Month` | `Quarter` | `Year`
  * `DimSymbol`: `Symbol` | `AssetType` (Stock/ETF) | `Sector`

#### 3.3. Bộ máy Kiểm thử (Backtesting Engine)
Mô phỏng hiệu năng tài chính của mô hình dựa trên quy tắc giao dịch:
* **Tín hiệu Mua/Nắm giữ:** Khi Model dự đoán nhãn 1 (Xu hướng tăng).
* **Tín hiệu Bán/Đứng ngoài:** Khi Model dự đoán nhãn 0 (Xu hướng giảm/đi ngang).
* **Chỉ số đánh giá chính (Financial Metrics):**
  * **Total Profit:** Lợi nhuận ròng cuối kỳ.
  * **Win Rate:** Tỷ lệ lệnh sinh lời trên tổng số lệnh cấu thành.
  * **Sharpe Ratio:** Đo lường hiệu suất sinh lời trên một đơn vị rủi ro.
  * **Max Drawdown:** Mức sụt giảm vốn lớn nhất tính từ đỉnh vốn (Đo lường rủi ro hệ thống).
  * **Đối chứng:** So sánh trực tiếp hiệu quả của chiến lược với phương pháp Mua và Nắm giữ thụ động (Buy & Hold).
