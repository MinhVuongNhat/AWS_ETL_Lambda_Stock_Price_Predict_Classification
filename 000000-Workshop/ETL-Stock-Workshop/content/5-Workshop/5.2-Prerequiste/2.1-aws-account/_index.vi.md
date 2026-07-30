---
title : "Tài khoản AWS & Quyền IAM"
date: ""
weight : 1
chapter : false
pre : " <b> 5.2.1. </b> "
---

#### Tài khoản AWS & Quyền IAM

Trước khi bắt đầu workshop này, hãy đảm bảo bạn có:

{{%notice warning%}}
Workshop này tạo các tài nguyên AWS có thể phát sinh chi phí. Hãy đảm bảo **dọn dẹp tất cả tài nguyên** sau khi hoàn thành workshop để tránh các khoản phí không mong muốn.
{{%/notice%}}

#### Yêu cầu ban đầu

- Một **Tài khoản AWS** với quyền Administrator (hoặc IAM user với các quyền được liệt kê bên dưới).
- **AWS CLI** đã cài đặt và cấu hình (`aws configure`).
- **Python 3.12** trở lên.
- **Docker Desktop** (cần thiết để build và push Lambda Container image lên ECR).
- **Git** để clone repository.

---

#### Quyền AWS cần thiết

IAM user hoặc role của bạn cần quyền cho các dịch vụ sau:

| Dịch vụ | Quyền cần thiết |
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

Mở terminal và clone repository dự án:

```bash
git clone https://github.com/MinhVuongNhat/AWS_ETL_Lambda_Stock_Price_Predict_Classification.git
cd AWS_ETL_Lambda_Stock_Price_Predict_Classification

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
```

---

#### Cấu hình AWS CLI

```bash
aws configure
```

Nhập các thông tin:
- **AWS Access Key ID**
- **AWS Secret Access Key**
- **Default region:** `ap-southeast-1`
- **Default output format:** `json`

![Aws Cli Configure](/images/2.1/aws-cli-configure.png)
