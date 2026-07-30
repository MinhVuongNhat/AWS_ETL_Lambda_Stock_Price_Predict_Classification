---
title : "Tạo IAM Roles"
date: ""
weight : 4
chapter : false
pre : " <b> 5.2.4. </b> "
---

#### Tạo IAM Roles cho Lambda Functions

Mỗi Lambda Function cần một **IAM Execution Role** để có quyền truy cập các dịch vụ AWS khác (S3, SQS, CloudWatch Logs).

---

#### Bước 1: Tạo Trust Policy Document

Tạo file `lambda-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

#### Bước 2: Tạo IAM Role

```bash
aws iam create-role \
    --role-name nasdaq-etl-lambda-role \
    --assume-role-policy-document file://lambda-trust-policy.json
```

---

#### Bước 3: Gắn các Policies cần thiết

```bash
# Quyền CloudWatch Logs (bắt buộc cho mọi Lambda)
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Quyền S3 Full Access
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Quyền SQS Full Access
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess
```

{{%notice warning%}}
Trong môi trường production, hãy áp dụng nguyên tắc **Least Privilege** — chỉ cấp đúng những quyền cần thiết cho từng Lambda, thay vì dùng `FullAccess`.
{{%/notice%}}

---

#### Bước 4: Lấy Role ARN

```bash
aws iam get-role --role-name nasdaq-etl-lambda-role \
    --query 'Role.Arn' --output text
```

Lưu lại **Role ARN** — ví dụ:
```
arn:aws:iam::123456789012:role/nasdaq-etl-lambda-role
```

![Iam Role Created](/images/2.4/iam-role-created.png)

---

#### Bước 5: Build & Push Docker Image lên ECR

Tất cả Lambda Functions sử dụng **Docker Container Image** để đóng gói thư viện Python phức tạp (Polars, XGBoost, yfinance).

```bash
# 1. Đăng nhập ECR
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Tạo ECR Repository
aws ecr create-repository \
    --repository-name nasdaq-etl-lambda \
    --region ap-southeast-1

# 3. Build Docker Image
docker build -t nasdaq-etl-lambda:latest .

# 4. Tag Image
docker tag nasdaq-etl-lambda:latest \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/nasdaq-etl-lambda:latest

# 5. Push lên ECR
docker push \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/nasdaq-etl-lambda:latest
```

![Ecr Image Pushed](/images/2.4/ecr-image-pushed.png)
