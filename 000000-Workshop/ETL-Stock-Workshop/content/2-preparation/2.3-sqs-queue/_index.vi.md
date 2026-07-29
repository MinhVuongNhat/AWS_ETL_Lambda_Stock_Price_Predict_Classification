---
title : "Tạo SQS Queue"
date: ""
weight : 3
chapter : false
pre : " <b> 2.3 </b> "
---

#### Tạo Amazon SQS Queue

Amazon SQS (Simple Queue Service) là trung tâm điều phối của kiến trúc **Fan-Out** trong Pipeline B. Lambda Producer sẽ đẩy các "chunk" danh sách ticker vào Queue, và các Lambda Consumer chạy song song để xử lý.

> *[TODO: Thêm ảnh minh họa kiến trúc Fan-Out SQS — `/images/2.3/sqs-fanout-architecture.png`]*

---

#### Bước 1: Tạo SQS Queue

```bash
aws sqs create-queue \
    --queue-name daily-collector-queue \
    --region ap-southeast-1 \
    --attributes '{
        "VisibilityTimeout": "300",
        "MessageRetentionPeriod": "86400",
        "ReceiveMessageWaitTimeSeconds": "20"
    }'
```

**Giải thích các thuộc tính:**

| Thuộc tính | Giá trị | Giải thích |
|:---|:---|:---|
| `VisibilityTimeout` | `300` giây | Thời gian Lambda Consumer giữ message trước khi trả lại queue nếu xử lý thất bại |
| `MessageRetentionPeriod` | `86400` giây (1 ngày) | Thời gian message được giữ lại trong queue |
| `ReceiveMessageWaitTimeSeconds` | `20` giây | Long-polling — giảm API calls không cần thiết |

---

#### Bước 2: Lấy Queue URL

```bash
aws sqs get-queue-url \
    --queue-name daily-collector-queue \
    --region ap-southeast-1
```

Kết quả mong đợi:
```json
{
    "QueueUrl": "https://sqs.ap-southeast-1.amazonaws.com/123456789012/daily-collector-queue"
}
```

Lưu lại **Queue URL** này — bạn sẽ cần nó khi cấu hình biến môi trường cho Lambda.

> *[TODO: Thêm ảnh màn hình SQS Queue đã tạo thành công trên AWS Console — `/images/2.3/sqs-queue-created.png`]*

---

#### Bước 3: Cấu hình biến môi trường

Tạo hoặc cập nhật file `.env` tại thư mục gốc dự án:

```ini
# .env
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET

# S3 Buckets
RAW_BUCKET=my-nasdaq-stock-market-raw-2026-ap-southeast-1
PROCESSED_BUCKET=my-nasdaq-stock-processed-2026-ap-southeast-1
MODEL_BUCKET=my-nasdaq-stock-models-2026-ap-southeast-1
SIM_BUCKET=my-nasdaq-stock-simulation-2026-ap-southeast-1

# SQS Queue URL
SQS_QUEUE_URL=https://sqs.ap-southeast-1.amazonaws.com/123456789012/daily-collector-queue

# Fan-Out chunk size (số tickers mỗi SQS message)
CHUNK_SIZE=100
```

{{%notice tip%}}
Giá trị `CHUNK_SIZE=100` nghĩa là mỗi SQS message chứa 100 ticker. Với 3,000 tickers, hệ thống sẽ tạo 30 message và 30 Lambda Consumer chạy song song để thu thập dữ liệu.
{{%/notice%}}
