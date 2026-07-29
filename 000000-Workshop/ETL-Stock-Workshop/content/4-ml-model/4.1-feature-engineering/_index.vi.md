---
title : "Feature Engineering"
date: ""
weight : 1
chapter : false
pre : " <b> 4.1 </b> "
---

#### Feature Engineering — 16 Chỉ báo Kỹ thuật

Feature Engineering là bước quan trọng nhất trong pipeline ML. Module `src/transform.py` tính toán **16 chỉ báo kỹ thuật** từ dữ liệu OHLCV lịch sử bằng thư viện **Polars**.

---

#### Tại sao cần Feature Engineering cho cổ phiếu?

Mô hình ML không thể học trực tiếp từ giá OHLCV thô (không có xu hướng). Chúng ta cần **tạo ra các đặc trưng** mô tả:
- **Xu hướng ngắn và dài hạn** (Moving Averages).
- **Động lượng** — giá đang tăng/giảm với tốc độ như thế nào (MACD, RSI).
- **Biến động** — mức độ dao động giá (Bollinger Bands, Volatility).
- **Giá quá khứ** — mô hình học từ pattern lịch sử (Lag Features).

---

#### Danh sách 16 chỉ báo kỹ thuật

**Nhóm 1: Xu hướng & Trung bình động (Trend)**

| Chỉ báo | Công thức | Ý nghĩa |
|:---|:---|:---|
| `SMA_5` | Trung bình động đơn giản 5 ngày | Xu hướng ngắn hạn |
| `SMA_20` | Trung bình động đơn giản 20 ngày | Xu hướng trung hạn |
| `EMA_12` | Trung bình động hàm mũ span=12 | Phản ứng nhanh với biến động giá |
| `EMA_26` | Trung bình động hàm mũ span=26 | Xu hướng dài hạn hơn |

**Nhóm 2: Động lượng (Momentum)**

| Chỉ báo | Công thức | Ý nghĩa |
|:---|:---|:---|
| `MACD` | EMA_12 - EMA_26 | Xác nhận xu hướng & điểm đảo chiều |
| `MACD_Signal` | EMA_9 của MACD | Đường tín hiệu MACD |
| `MACD_Hist` | MACD - MACD_Signal | Biểu đồ thanh MACD |
| `RSI_14` | Wilder's Smoothing, window=14 | Chỉ báo quá mua (>70) / quá bán (<30) |

**Nhóm 3: Biến động (Volatility)**

| Chỉ báo | Công thức | Ý nghĩa |
|:---|:---|:---|
| `BB_Upper` | SMA_20 + 2 × STD_20 | Dải trên Bollinger Bands |
| `BB_Lower` | SMA_20 - 2 × STD_20 | Dải dưới Bollinger Bands |
| `BB_Width` | (BB_Upper - BB_Lower) / SMA_20 | Độ rộng dải — đo mức độ biến động |
| `Intraday_Volatility` | (High - Low) / Open | Biên độ dao động trong phiên |

**Nhóm 4: Giá quá khứ & Lợi nhuận**

| Chỉ báo | Công thức | Ý nghĩa |
|:---|:---|:---|
| `Lag_Close_1` | Close của ngày T-1 | Pattern từ ngày hôm qua |
| `Lag_Close_2` | Close của ngày T-2 | Pattern từ 2 ngày trước |
| `Lag_Close_3` | Close của ngày T-3 | Pattern từ 3 ngày trước |
| `Daily_Return` | Adj_Close / Adj_Close(T-1) - 1 | Tỷ suất lợi nhuận ngày |

---

#### Label — Mục tiêu phân loại

```
Label = 1  nếu Close(T+1) > Close(T)   → Dự đoán giá TĂNG
Label = 0  nếu Close(T+1) ≤ Close(T)  → Dự đoán giá GIẢM
```

---

#### Chạy Feature Engineering thủ công (Local)

```bash
# Chạy backfill local — tải từ S3 và tính toán Feature Engineering
python local_backfill.py
```

Hoặc chạy pipeline ETL hoàn chỉnh để kiểm tra:

```bash
python debug_daily_pipeline.py
```

> *[TODO: Thêm ảnh biểu đồ ví dụ các chỉ báo kỹ thuật trên một mã cổ phiếu — `/images/4.1/technical-indicators-chart.png`]*
