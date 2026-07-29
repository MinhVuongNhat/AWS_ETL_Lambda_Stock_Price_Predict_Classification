---
title : "Dọn dẹp tài nguyên"
date: ""
weight : 6
chapter : false
pre : " <b> 5.6. </b> "
---

#### Dọn dẹp tài nguyên

Sau khi hoàn thành workshop, hãy xóa tất cả tài nguyên AWS để tránh phát sinh chi phí không mong muốn.

{{%notice warning%}}
**Cẩn thận:** Các bước dưới đây sẽ xóa vĩnh viễn tất cả dữ liệu và tài nguyên đã tạo. Hãy đảm bảo bạn đã sao lưu những gì cần thiết trước khi tiến hành.
{{%/notice%}}

---

#### Bước 1: Xóa Lambda Functions

```bash
aws lambda delete-function --function-name nasdaq-daily-collector --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-collector-producer --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-quality-gate --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-daily-etl --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-stock-predictor --region ap-southeast-1
```

---

#### Bước 2: Xóa EventBridge Rule

```bash
# Xóa targets trước
aws events remove-targets \
    --rule nasdaq-daily-pipeline-trigger \
    --ids lambda-target \
    --region ap-southeast-1

# Sau đó xóa rule
aws events delete-rule \
    --name nasdaq-daily-pipeline-trigger \
    --region ap-southeast-1
```

---

#### Bước 3: Xóa SQS Queue

```bash
aws sqs delete-queue \
    --queue-url "https://sqs.ap-southeast-1.amazonaws.com/<ACCOUNT_ID>/daily-collector-queue" \
    --region ap-southeast-1
```

---

#### Bước 4: Xóa S3 Buckets

{{%notice warning%}}
**Lưu ý:** Bạn phải xóa hết toàn bộ objects bên trong bucket trước khi có thể xóa bucket.
{{%/notice%}}

```bash
# Xóa toàn bộ objects trong từng bucket
aws s3 rm s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-processed-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-models-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-simulation-2026-ap-southeast-1 --recursive

# Sau đó xóa bucket
aws s3 rb s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-processed-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-models-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-simulation-2026-ap-southeast-1
```

---

#### Bước 5: Xóa ECR Repository

```bash
aws ecr delete-repository \
    --repository-name nasdaq-etl-lambda \
    --force \
    --region ap-southeast-1
```

---

#### Bước 6: Xóa IAM Role

```bash
# Gỡ policies trước
aws iam detach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam detach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam detach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess

# Sau đó xóa role
aws iam delete-role --role-name nasdaq-etl-lambda-role
```

---

#### Xác nhận đã dọn dẹp xong

Kiểm tra lại trên AWS Console:
- ✅ Lambda Console — Không còn function nào liên quan đến `nasdaq-`.
- ✅ S3 Console — Không còn bucket nào liên quan đến `my-nasdaq-`.
- ✅ SQS Console — Queue `daily-collector-queue` đã bị xóa.
- ✅ ECR Console — Repository `nasdaq-etl-lambda` đã bị xóa.
- ✅ EventBridge Console — Rule `nasdaq-daily-pipeline-trigger` đã bị xóa.

{{%notice tip%}}
Bạn cũng có thể kiểm tra **AWS Cost Explorer** sau 24 giờ để đảm bảo không còn chi phí phát sinh từ workshop này.
{{%/notice%}}
