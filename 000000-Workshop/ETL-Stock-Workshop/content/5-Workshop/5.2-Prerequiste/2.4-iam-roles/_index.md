---
title : "Create IAM Roles"
date: ""
weight : 4
chapter : false
pre : " <b> 5.2.4. </b> "
---

#### Create IAM Roles for Lambda Functions

Each Lambda Function needs an **IAM Execution Role** to access other AWS services (S3, SQS, CloudWatch Logs).

---

#### Step 1: Create Trust Policy Document

Create `lambda-trust-policy.json`:

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

#### Step 2: Create IAM Role

```bash
aws iam create-role \
    --role-name nasdaq-etl-lambda-role \
    --assume-role-policy-document file://lambda-trust-policy.json
```

---

#### Step 3: Attach Required Policies

```bash
# CloudWatch Logs (required for all Lambda)
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# S3 Full Access
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# SQS Full Access
aws iam attach-role-policy \
    --role-name nasdaq-etl-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess
```

{{%notice warning%}}
In production, apply the **Least Privilege** principle — grant only the exact permissions each Lambda needs, instead of using `FullAccess`.
{{%/notice%}}

---

#### Step 4: Build & Push Docker Image to ECR

All Lambda Functions use **Docker Container Images** to package complex Python libraries (Polars, XGBoost, yfinance).

```bash
# 1. Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Create ECR Repository
aws ecr create-repository \
    --repository-name nasdaq-etl-lambda \
    --region ap-southeast-1

# 3. Build Docker Image
docker build -t nasdaq-etl-lambda:latest .

# 4. Tag Image
docker tag nasdaq-etl-lambda:latest \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/nasdaq-etl-lambda:latest

# 5. Push to ECR
docker push \
    <YOUR_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/nasdaq-etl-lambda:latest
```

![Ecr Image Pushed](/images/2.4/ecr-image-pushed.png)
