---
title : "Lambda Daily Collector"
date: ""
weight : 1
chapter : false
pre : " <b> 3.1 </b> "
---

#### Lambda Daily Collector — Fan-Out Producer

`lambda_daily_collector.py` is the first **Lambda Producer** in Pipeline B. It is triggered by **Amazon EventBridge** on a daily schedule and:

1. Reads `tickers.json` from S3 to get the list of tracked stock tickers.
2. Splits the list into chunks (`CHUNK_SIZE=100` tickers each).
3. Sends each chunk as an SQS message to `daily-collector-queue`.

> *[TODO: Add flow diagram: EventBridge → Lambda → SQS — `/images/3.1/eventbridge-lambda-sqs-flow.png`]*

---

#### Step 1: Create Lambda Function

Go to **AWS Lambda Console** and create a new function:

- **Function name:** `nasdaq-daily-collector`
- **Container image:** Select from ECR `nasdaq-etl-lambda:latest`
- **CMD override:** `src.lambda_daily_collector.lambda_handler`
- **Execution role:** `nasdaq-etl-lambda-role`
- **Memory:** `512 MB`
- **Timeout:** `5 minutes`

---

#### Step 2: Configure Environment Variables

In **Configuration → Environment variables**, add:

| Key | Value |
|:---|:---|
| `PROCESSED_BUCKET` | `my-nasdaq-stock-processed-2026-ap-southeast-1` |
| `SQS_QUEUE_URL` | `https://sqs.ap-southeast-1.amazonaws.com/123456789012/daily-collector-queue` |
| `TICKERS_S3_KEY` | `config/tickers.json` |
| `CHUNK_SIZE` | `100` |
| `AWS_REGION` | `ap-southeast-1` |

---

#### Step 3: Set up EventBridge Trigger

```bash
aws events put-rule \
    --name "nasdaq-daily-pipeline-trigger" \
    --schedule-expression "cron(0 0 ? * MON-FRI *)" \
    --state ENABLED \
    --region ap-southeast-1
```

{{%notice info%}}
The schedule `cron(0 0 ? * MON-FRI *)` means **0:00 UTC, Monday through Friday** — after the US market closes.
{{%/notice%}}
