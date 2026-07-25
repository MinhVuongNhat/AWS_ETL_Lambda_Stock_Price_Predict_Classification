import io
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import boto3
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend cho server/script
import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
import xgboost as xgb
from botocore.config import Config
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve
)
from sklearn.model_selection import train_test_split

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("train_model")

# Cấu hình bucket
PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an")
PROCESSED_PREFIX = "processed/"
MODEL_BUCKET = os.environ.get("MODEL_BUCKET", "my-nasdaq-stock-models-2026-430970051812-ap-southeast-1-an")
MODEL_PREFIX = "models/xgboost_v1/"

# Thêm retry config để tránh lỗi SSL transient
boto3_config = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},
    connect_timeout=30,
    read_timeout=120
)
s3_client = boto3.client("s3", config=boto3_config)

FEATURE_COLS = [
    "SMA_5", "SMA_20", "EMA_12", "EMA_26",
    "Lag_Close_1", "Lag_Close_2", "Lag_Close_3",
    "Daily_Return", "Intraday_Volatility",
    "MACD", "MACD_Signal", "MACD_Hist",
    "RSI_14", "BB_Upper", "BB_Lower", "BB_Width"
]
TARGET_COL = "Label"


def ensure_model_bucket_exists():
    """Tạo S3 bucket cho models nếu chưa tồn tại"""
    try:
        s3_client.head_bucket(Bucket=MODEL_BUCKET)
        logger.info(f"✅ Bucket {MODEL_BUCKET} đã tồn tại.")
    except Exception as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            logger.info(f"Đang tạo bucket {MODEL_BUCKET}...")
            region = s3_client.meta.region_name
            if region == "us-east-1":
                s3_client.create_bucket(Bucket=MODEL_BUCKET)
            else:
                s3_client.create_bucket(
                    Bucket=MODEL_BUCKET,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
            logger.info(f"✅ Đã tạo bucket {MODEL_BUCKET}")
        else:
            raise


def read_parquet_s3_with_retry(bucket, key, max_retries=3):
    """Đọc file parquet từ S3 với retry khi gặp lỗi SSL/network"""
    for attempt in range(1, max_retries + 1):
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return pl.read_parquet(io.BytesIO(response["Body"].read()))
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt  # exponential backoff
                logger.warning(f"  ⚠️  Lỗi đọc {key} (lần {attempt}/{max_retries}): {e}. Thử lại sau {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"  ❌ Không thể đọc {key} sau {max_retries} lần thử.")
                raise


def load_all_data_from_s3() -> pl.DataFrame:
    """Tải toàn bộ data từ PROCESSED_BUCKET/processed/"""
    logger.info(f"Đang tìm các file parquet trong s3://{PROCESSED_BUCKET}/{PROCESSED_PREFIX}...")

    for attempt in range(1, 4):
        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=PROCESSED_BUCKET, Prefix=PROCESSED_PREFIX)
            keys = []
            for page in pages:
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".parquet"):
                        keys.append(obj["Key"])
            break
        except Exception as e:
            if attempt < 3:
                wait = 5 * attempt
                logger.warning(f"⚠️ Lỗi liệt kê S3 objects (lần {attempt}/3): {e}. Thử lại sau {wait}s...")
                time.sleep(wait)
            else:
                raise

    if not keys:
        raise ValueError(f"Không tìm thấy file parquet nào trong s3://{PROCESSED_BUCKET}/{PROCESSED_PREFIX}")

    logger.info(f"Tìm thấy {len(keys)} file. Đang tải và gom data...")

    dfs = []
    for i, key in enumerate(sorted(keys), 1):
        logger.info(f"  [{i}/{len(keys)}] Đang đọc {key}")
        df = read_parquet_s3_with_retry(PROCESSED_BUCKET, key)
        dfs.append(df)

    full_df = pl.concat(dfs, how="diagonal_relaxed")
    logger.info(f"✅ Đã tải xong toàn bộ dữ liệu. Tổng số dòng: {full_df.height:,}")
    return full_df


def prepare_data(df: pl.DataFrame):
    """Lọc dữ liệu, drop null, chia tập train/test"""
    logger.info("Đang xử lý dữ liệu trước khi train...")

    # Drop rows nơi Label là null (thường là dòng cuối của mỗi ticker)
    df_clean = df.drop_nulls(subset=[TARGET_COL] + FEATURE_COLS)
    logger.info(f"Sau khi drop null, còn lại: {df_clean.height:,} dòng.")

    X = df_clean.select(FEATURE_COLS).to_pandas()
    y = df_clean.select(TARGET_COL).to_pandas().iloc[:, 0]

    # Chia theo thứ tự thời gian (80/20 không shuffle)
    logger.info("Chia tập train (80%) và test (20%) theo thứ tự thời gian...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    logger.info(f"Kích thước Train: {X_train.shape[0]:,} dòng")
    logger.info(f"Kích thước Test : {X_test.shape[0]:,} dòng")

    return X_train, X_test, y_train, y_test


def train_xgboost(X_train, X_test, y_train, y_test):
    """Train XGBoost model"""
    logger.info("Khởi tạo và train mô hình XGBoost...")

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        eval_metric="logloss",
        early_stopping_rounds=20
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=20
    )

    logger.info("✅ Train hoàn tất!")
    return model


def evaluate_model(model, X_test, y_test):
    """Đánh giá model trên tập test"""
    logger.info("Đang đánh giá mô hình trên tập test...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_prob)

    logger.info("=== KẾT QUẢ ĐÁNH GIÁ (TEST SET) ===")
    logger.info(f"Accuracy  : {acc:.4f}")
    logger.info(f"Precision : {prec:.4f}")
    logger.info(f"Recall    : {rec:.4f}")
    logger.info(f"F1 Score  : {f1:.4f}")
    logger.info(f"AUC-ROC   : {auc:.4f}")
    logger.info("=====================================")

    return {
        "accuracy":  acc,
        "precision": prec,
        "recall":    rec,
        "f1":        f1,
        "auc_roc":   auc
    }


def generate_report(model, X_test, y_test, metrics):
    """Tạo báo cáo chất lượng mô hình + biểu đồ PNG và xuất training_report.md"""
    logger.info("Đang tạo báo cáo chất lượng (Quality Report)...")

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    sns.set_theme(style="darkgrid")

    # 1. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Giảm (0)", "Tăng (1)"],
        yticklabels=["Giảm (0)", "Tăng (1)"],
        ax=ax
    )
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    ax.set_ylabel("Thực tế")
    ax.set_xlabel("Dự đoán")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("  ✓ confusion_matrix.png")

    # 2. ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#f97316", lw=2.5, label=f"AUC = {metrics['auc_roc']:.4f}")
    ax.plot([0, 1], [0, 1], color="#6b7280", lw=1.5, linestyle="--", label="Random (AUC = 0.5)")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("roc_curve.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("  ✓ roc_curve.png")

    # 3. Feature Importance
    importance = model.feature_importances_
    sorted_idx = importance.argsort()
    sorted_features = [FEATURE_COLS[i] for i in sorted_idx]
    sorted_values   = importance[sorted_idx]

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(sorted_features, sorted_values, color="#3b82f6", edgecolor="white")
    ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=9)
    ax.set_title("XGBoost Feature Importance", fontsize=14, fontweight="bold")
    ax.set_xlabel("Mức độ quan trọng (F-Score)")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("  ✓ feature_importance.png")

    # 4. Xuất training_report.md
    tn, fp, fn, tp = cm.ravel()
    report_md = f"""# 📊 Báo Cáo Chất Lượng Mô Hình XGBoost

| Thông tin | Giá trị |
|-----------|---------|
| Thời gian train | `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` |
| Mục tiêu | Phân loại hướng giá cổ phiếu NASDAQ |
| Label | `1` = Tăng, `0` = Giảm (so với ngày hôm sau) |
| Dữ liệu | 1962 – 2026 |
| Kiến trúc | XGBoost Classifier |

---

## 1. 📈 Kết Quả Đánh Giá (Test Set — 20% cuối theo thời gian)

| Metric | Giá trị |
|--------|---------|
| **Accuracy** | `{metrics['accuracy']:.4f}` ({metrics['accuracy']*100:.2f}%) |
| **Precision** | `{metrics['precision']:.4f}` |
| **Recall** | `{metrics['recall']:.4f}` |
| **F1 Score** | `{metrics['f1']:.4f}` |
| **AUC-ROC** | `{metrics['auc_roc']:.4f}` |

---

## 2. 🔢 Confusion Matrix (Chi tiết)

|  | Dự đoán Giảm | Dự đoán Tăng |
|--|--|--|
| **Thực tế Giảm** | TN = `{tn:,}` ✅ | FP = `{fp:,}` ❌ |
| **Thực tế Tăng** | FN = `{fn:,}` ❌ | TP = `{tp:,}` ✅ |

- **Specificity (True Negative Rate)**: `{tn / (tn + fp):.4f}`
- **False Positive Rate**: `{fp / (fp + tn):.4f}`

---

## 3. 📉 Biểu đồ

### Confusion Matrix
![Confusion Matrix](confusion_matrix.png)

### ROC Curve
> AUC = **{metrics['auc_roc']:.4f}** ({'Xuất sắc' if metrics['auc_roc'] >= 0.75 else 'Tốt' if metrics['auc_roc'] >= 0.65 else 'Chấp nhận được' if metrics['auc_roc'] >= 0.55 else 'Kém'})

![ROC Curve](roc_curve.png)

### Feature Importance
![Feature Importance](feature_importance.png)

---

## 4. 🔧 Hyperparameters

```json
{json.dumps(model.get_params(), indent=2, default=str)}
```

---
*Báo cáo tự động sinh bởi `train_model.py`*
"""

    with open("training_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    logger.info("✅ Đã tạo xong training_report.md và 3 file ảnh PNG.")


def upload_to_s3(model, metrics):
    """Lưu model ra local và upload lên S3"""
    logger.info(f"Đang upload lên s3://{MODEL_BUCKET}/{MODEL_PREFIX}...")

    ensure_model_bucket_exists()

    # Save model
    model_path = "xgboost_model.json"
    model.save_model(model_path)

    metadata = {
        "version": "1.0",
        "train_date": datetime.utcnow().isoformat() + "Z",
        "metrics": metrics,
        "feature_names": FEATURE_COLS
    }

    metadata_path = "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    feature_names_path = "feature_names.json"
    with open(feature_names_path, "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)

    # Upload files
    files_to_upload = [
        (model_path,         f"{MODEL_PREFIX}model.json"),
        (metadata_path,      f"{MODEL_PREFIX}metadata.json"),
        (feature_names_path, f"{MODEL_PREFIX}feature_names.json"),
        ("confusion_matrix.png",   f"{MODEL_PREFIX}reports/confusion_matrix.png"),
        ("roc_curve.png",          f"{MODEL_PREFIX}reports/roc_curve.png"),
        ("feature_importance.png", f"{MODEL_PREFIX}reports/feature_importance.png"),
    ]

    for local_path, s3_key in files_to_upload:
        if os.path.exists(local_path):
            s3_client.upload_file(local_path, MODEL_BUCKET, s3_key)
            logger.info(f"  ✓ Uploaded {local_path} → s3://{MODEL_BUCKET}/{s3_key}")

    # Dọn dẹp
    for local_path, _ in files_to_upload:
        if os.path.exists(local_path):
            os.remove(local_path)

    logger.info("✅ Upload thành công!")


def main():
    start_time = time.time()
    try:
        df = load_all_data_from_s3()
        X_train, X_test, y_train, y_test = prepare_data(df)
        model = train_xgboost(X_train, X_test, y_train, y_test)
        metrics = evaluate_model(model, X_test, y_test)

        # Tạo báo cáo local
        generate_report(model, X_test, y_test, metrics)

        # Chỉ upload nếu model tốt hơn random (AUC > 0.5)
        if metrics["auc_roc"] > 0.5:
            upload_to_s3(model, metrics)
        else:
            logger.warning("⚠️ Model có AUC <= 0.5. KHÔNG upload lên S3.")

        elapsed = (time.time() - start_time) / 60
        logger.info(f"🎉 Toàn bộ pipeline train hoàn thành trong {elapsed:.1f} phút.")
        logger.info("📄 Xem báo cáo tại: training_report.md")

    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình train: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
