---
title : "Self Evaluation"
date: ""
weight : 6
chapter : false
pre : " <b> 6. </b> "
---

#### Self Evaluation

*Personal evaluation of learning outcomes, technical skills gained, architectural decisions, and key lessons learned throughout the 8-week AWS Big Data ETL & Machine Learning project.*

---

#### Technical Skills Evaluation Matrix

| Skill / Technology | Level Before | Level After | Key Takeaways & Competencies Gained |
|:---|:---:|:---:|:---|
| **AWS Lambda** | Basic | Advanced | Mastered Serverless execution model, environment variables, timeout management, concurrency limits, and Docker ECR packaging. |
| **Amazon S3** | Basic | Intermediate | Designed multi-tiered storage architecture (`raw/`, `cleansed/`, `processed/`, `quarantine/`) and implemented Snappy Parquet partitioning. |
| **Amazon SQS** | Beginner | Intermediate | Implemented Fan-Out architecture pattern using SQS batching queues to solve Lambda 15-minute execution timeout issues. |
| **Amazon EventBridge** | Beginner | Intermediate | Configured automated cron schedules (`cron(0 22 ? * MON-FRI *)`) for daily market ingestion triggering. |
| **Amazon API Gateway** | Beginner | Intermediate | Built REST API integrations with Lambda proxy routing, CORS handling, and sub-second prediction query serving. |
| **Amazon ECR / Docker** | Beginner | Intermediate | Containerized heavy Python dependencies (Polars, PyArrow, Pandera, XGBoost) into optimized Docker images pushed to ECR. |
| **Feature Engineering** | Intermediate | Advanced | Computed 16 time-series technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, Volatility) while avoiding look-ahead bias. |
| **XGBoost / Machine Learning** | Intermediate | Advanced | Trained binary classification models, evaluated metrics (AUC-ROC, Precision, Recall, F1), handled class balance, and exported artifacts. |
| **Polars / Apache Parquet** | Beginner | Advanced | Leveraged high-performance Rust-backed Polars for 10-50x faster data transformation compared to traditional Pandas pipelines. |

---

#### Overall Project Assessment

##### 1. What Went Well (Key Successes)
* **High Scalability & Cost Efficiency:** Successfully processed over 3,000+ NASDAQ tickers in parallel using the Fan-Out pattern (EventBridge + SQS + Lambda) within AWS Free Tier limits.
* **Robust Data Quality Control:** Implemented an automated Data Quality Gate (`validator.py` + `quarantine/` S3 bucket) that isolates corrupted or incomplete records without crashing the ETL pipeline.
* **Modern High-Performance Stack:** Transitioned from Pandas/CSV to Polars/Parquet, drastically reducing I/O latency and memory footprint during batch feature engineering.
* **End-to-End Automation:** Built a fully functional serverless architecture from ingestion to serving via API Gateway and an interactive Streamlit dashboard.

##### 2. What Could Be Improved (Areas for Growth)
* **Model Accuracy & Hyperparameter Tuning:** The current AUC-ROC metric (~0.55) indicates room for improvement; adding macro-economic sentiment or order book features could enhance predictive power.
* **Infrastructure as Code (IaC):** AWS resources were created via AWS Console and CLI scripts; implementing Terraform or AWS CDK would make the infrastructure deployment reproducible.
* **CI/CD Pipeline Automation:** Integrating GitHub Actions for automated Docker image builds and Lambda code deployments would improve code delivery efficiency.

##### 3. Key Lessons Learned
1. **Data Quality First:** Never assume raw market data from external APIs is clean; building validation layers upfront saves countless hours of debugging downstream model failures.
2. **Serverless Architectural Limits:** Understanding Lambda memory and timeout constraints is critical for big data engineering—decoupling workloads with SQS queues is vital for large batch jobs.
3. **Tool Selection Matters:** Choosing Polars over Pandas reduced processing times from tens of minutes to seconds, demonstrating the impact of tool selection in big data processing.
