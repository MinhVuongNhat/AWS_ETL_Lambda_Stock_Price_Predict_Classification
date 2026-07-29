---
title : "Lambda Daily Collector"
date: ""
weight : 1
chapter : false
pre : " <b> 5.3.1. </b> "
---

#### Lambda Daily Collector — Fan-Out Producer

`lambda_daily_collector.py` là **Lambda Producer** đầu tiên trong Pipeline B. Nó được kích hoạt bởi **Amazon EventBridge** theo lịch hàng ngày và có nhiệm vụ:

1. Đọc file `tickers.json` từ S3 để lấy danh sách mã cổ phiếu cần theo dõi.
2. Chia nhỏ danh sách thành các chunk (mỗi chunk `CHUNK_SIZE=100` tickers).
3. Gửi từng chunk như một SQS message vào `daily-collector-queue`.

> *[TODO: Thêm ảnh minh họa luồng EventBridge → Lambda → SQS — `/images/3.1/eventbridge-lambda-sqs-flow.png`]*

---

#### Bước 1: Tạo Lambda Function

Truy cập **AWS Lambda Console** và tạo function mới:

- **Function name:** `nasdaq-daily-collector`
- **Container image:** Chọn image từ ECR `nasdaq-etl-lambda:latest`
- **CMD override:** `src.lambda_daily_collector.lambda_handler`
- **Execution role:** `nasdaq-etl-lambda-role`
- **Memory:** `512 MB`
- **Timeout:** `5 phút`

> *[TODO: Thêm ảnh màn hình tạo Lambda Function — `/images/3.1/lambda-create-function.png`]*

---

#### Bước 2: Cấu hình biến môi trường Lambda

Trong tab **Configuration → Environment variables**, thêm:

| Key | Value |
|:---|:---|
| `PROCESSED_BUCKET` | `my-nasdaq-stock-processed-2026-ap-southeast-1` |
| `SQS_QUEUE_URL` | `https://sqs.ap-southeast-1.amazonaws.com/123456789012/daily-collector-queue` |
| `TICKERS_S3_KEY` | `config/tickers.json` |
| `CHUNK_SIZE` | `100` |
| `AWS_REGION` | `ap-southeast-1` |

> *[TODO: Thêm ảnh màn hình Environment Variables trong Lambda — `/images/3.1/lambda-env-vars.png`]*

---

#### Bước 3: Thiết lập EventBridge Trigger

Tạo **EventBridge Rule** để kích hoạt Lambda tự động hàng ngày:

```bash
aws events put-rule \
    --name "nasdaq-daily-pipeline-trigger" \
    --schedule-expression "cron(0 0 ? * MON-FRI *)" \
    --state ENABLED \
    --region ap-southeast-1
```

Sau đó gắn Lambda như target:

```bash
aws events put-targets \
    --rule nasdaq-daily-pipeline-trigger \
    --targets "Id=lambda-target,Arn=arn:aws:lambda:ap-southeast-1:<ACCOUNT_ID>:function:nasdaq-daily-collector" \
    --region ap-southeast-1
```

{{%notice info%}}
Lịch `cron(0 0 ? * MON-FRI *)` nghĩa là **0:00 UTC từ Thứ Hai đến Thứ Sáu** — tương ứng với sau khi thị trường Mỹ đóng cửa (7:00 AM giờ Việt Nam).
{{%/notice%}}

> *[TODO: Thêm ảnh màn hình EventBridge Rule đã tạo — `/images/3.1/eventbridge-rule.png`]*

---

#### Bước 4: Test thủ công Lambda

Tạo test event trong Lambda Console để kiểm tra hoạt động:

```json
{
    "source": "manual-test",
    "detail-type": "Scheduled Event"
}
```

Kiểm tra CloudWatch Logs để xác nhận Lambda đã đọc tickers và gửi SQS messages thành công.

> *[TODO: Thêm ảnh CloudWatch Logs của Lambda chạy thành công — `/images/3.1/cloudwatch-logs.png`]*

---

#### Cấu hình Lambda Collector Consumer

`lambda_collector_producer.py` là Lambda Consumer nhận SQS messages và cào dữ liệu từ Yahoo Finance:

- **Function name:** `nasdaq-collector-producer`
- **CMD override:** `src.lambda_collector_producer.lambda_handler`
- **Memory:** `1024 MB`
- **Timeout:** `15 phút`
- **SQS Trigger:** `daily-collector-queue`, batch size `1`

{{%notice tip%}}
Cài batch size = 1 để mỗi Lambda Consumer chỉ xử lý 1 SQS message (100 tickers) một lần, giúp tối ưu thời gian và tránh timeout khi gọi Yahoo Finance API.
{{%/notice%}}
