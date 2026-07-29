---
title : "AWS Account & Permissions"
date: ""
weight : 1
chapter : false
pre : " <b> 2.1 </b> "
---

#### AWS Account & IAM Permissions

Before starting this workshop, make sure you have:

{{%notice warning%}}
This workshop creates AWS resources that may incur costs. Make sure you **clean up all resources** after completing the workshop to avoid unexpected charges.
{{%/notice%}}

#### Prerequisites

- An **AWS Account** with Administrator access (or an IAM user with the permissions listed below).
- **AWS CLI** installed and configured (`aws configure`).
- **Python 3.12** or later.
- **Docker Desktop** (required to build and push Lambda Container images).
- **Git** for cloning the repository.

---

#### Required AWS Permissions

Your IAM user or role needs permissions for the following services:

| Service | Required Actions |
|:---|:---|
| **Amazon S3** | `s3:CreateBucket`, `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket` |
| **AWS Lambda** | `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, `lambda:InvokeFunction` |
| **Amazon SQS** | `sqs:CreateQueue`, `sqs:SendMessage`, `sqs:ReceiveMessage`, `sqs:DeleteMessage` |
| **Amazon ECR** | `ecr:CreateRepository`, `ecr:GetLoginPassword`, `ecr:BatchCheckLayerAvailability`, `ecr:PutImage` |
| **Amazon EventBridge** | `events:PutRule`, `events:PutTargets` |
| **Amazon API Gateway** | `apigateway:POST`, `apigateway:GET` |
| **AWS IAM** | `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole` |

---

#### Clone Repository

Open your terminal and clone the project repository:

```bash
git clone https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification.git
cd AWS_ETL_Lambda_Stock_Price_Predict_Classification

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

#### Configure AWS CLI

```bash
aws configure
```

Enter your:
- **AWS Access Key ID**
- **AWS Secret Access Key**
- **Default region:** `ap-southeast-1`
- **Default output format:** `json`

> *[TODO: Add screenshot of AWS CLI configuration — `/images/2.1/aws-cli-configure.png`]*
