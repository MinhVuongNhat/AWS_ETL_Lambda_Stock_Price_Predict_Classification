---
title : "Clean up Resources"
date: ""
weight : 6
chapter : false
pre : " <b> 5.6. </b> "
---

#### Clean up Resources

After completing the workshop, delete all AWS resources to avoid unexpected charges.

{{%notice warning%}}
**Warning:** The steps below will permanently delete all data and resources created during this workshop. Make sure to back up anything you need before proceeding.
{{%/notice%}}

---

#### Step 1: Delete Lambda Functions

```bash
aws lambda delete-function --function-name nasdaq-daily-collector --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-collector-producer --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-quality-gate --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-daily-etl --region ap-southeast-1
aws lambda delete-function --function-name nasdaq-stock-predictor --region ap-southeast-1
```

---

#### Step 2: Delete EventBridge Rule

```bash
aws events remove-targets --rule nasdaq-daily-pipeline-trigger --ids lambda-target --region ap-southeast-1
aws events delete-rule --name nasdaq-daily-pipeline-trigger --region ap-southeast-1
```

---

#### Step 3: Delete SQS Queue

```bash
aws sqs delete-queue \
    --queue-url "https://sqs.ap-southeast-1.amazonaws.com/<ACCOUNT_ID>/daily-collector-queue" \
    --region ap-southeast-1
```

---

#### Step 4: Empty & Delete S3 Buckets

```bash
aws s3 rm s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-processed-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-models-2026-ap-southeast-1 --recursive
aws s3 rm s3://my-nasdaq-stock-simulation-2026-ap-southeast-1 --recursive

aws s3 rb s3://my-nasdaq-stock-market-raw-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-processed-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-models-2026-ap-southeast-1
aws s3 rb s3://my-nasdaq-stock-simulation-2026-ap-southeast-1
```

---

#### Step 5: Delete ECR Repository

```bash
aws ecr delete-repository --repository-name nasdaq-etl-lambda --force --region ap-southeast-1
```

---

#### Step 6: Delete IAM Role

```bash
aws iam detach-role-policy --role-name nasdaq-etl-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam detach-role-policy --role-name nasdaq-etl-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam detach-role-policy --role-name nasdaq-etl-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess
aws iam delete-role --role-name nasdaq-etl-lambda-role
```

---

#### Verification Checklist

- ✅ Lambda Console — No more `nasdaq-` functions
- ✅ S3 Console — No more `my-nasdaq-` buckets
- ✅ SQS Console — `daily-collector-queue` deleted
- ✅ ECR Console — `nasdaq-etl-lambda` repository deleted
- ✅ EventBridge Console — `nasdaq-daily-pipeline-trigger` rule deleted

{{%notice tip%}}
Check **AWS Cost Explorer** after 24 hours to confirm no remaining charges from this workshop.
{{%/notice%}}
