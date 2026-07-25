# 📊 Báo Cáo Chất Lượng Mô Hình XGBoost

| Thông tin | Giá trị |
|-----------|---------|
| Thời gian train | `2026-07-24 14:49:48` |
| Mục tiêu | Phân loại hướng giá cổ phiếu NASDAQ |
| Label | `1` = Tăng, `0` = Giảm (so với ngày hôm sau) |
| Dữ liệu | 1962 – 2026 |
| Kiến trúc | XGBoost Classifier |

---

## 1. 📈 Kết Quả Đánh Giá (Test Set — 20% cuối theo thời gian)

| Metric | Giá trị |
|--------|---------|
| **Accuracy** | `0.5312` (53.12%) |
| **Precision** | `0.5311` |
| **Recall** | `0.4828` |
| **F1 Score** | `0.5058` |
| **AUC-ROC** | `0.5487` |

---

## 2. 🔢 Confusion Matrix (Chi tiết)

|  | Dự đoán Giảm | Dự đoán Tăng |
|--|--|--|
| **Thực tế Giảm** | TN = `1,971,290` ✅ | FP = `1,433,751` ❌ |
| **Thực tế Tăng** | FN = `1,739,658` ❌ | TP = `1,624,190` ✅ |

- **Specificity (True Negative Rate)**: `0.5789`
- **False Positive Rate**: `0.4211`

---

## 3. 📉 Biểu đồ

### Confusion Matrix
![Confusion Matrix](confusion_matrix.png)

### ROC Curve
> AUC = **0.5487** (Kém)

![ROC Curve](roc_curve.png)

### Feature Importance
![Feature Importance](feature_importance.png)

---

## 4. 🔧 Hyperparameters

```json
{
  "objective": "binary:logistic",
  "base_score": null,
  "booster": null,
  "callbacks": null,
  "colsample_bylevel": null,
  "colsample_bynode": null,
  "colsample_bytree": 0.8,
  "device": null,
  "early_stopping_rounds": 20,
  "enable_categorical": false,
  "eval_metric": "logloss",
  "feature_types": null,
  "feature_weights": null,
  "gamma": 0.1,
  "grow_policy": null,
  "importance_type": null,
  "interaction_constraints": null,
  "learning_rate": 0.05,
  "max_bin": null,
  "max_cat_threshold": null,
  "max_cat_to_onehot": null,
  "max_delta_step": null,
  "max_depth": 6,
  "max_leaves": null,
  "min_child_weight": 5,
  "missing": NaN,
  "monotone_constraints": null,
  "multi_strategy": null,
  "n_estimators": 200,
  "n_jobs": null,
  "num_parallel_tree": null,
  "random_state": 42,
  "reg_alpha": 0.1,
  "reg_lambda": 1.0,
  "sampling_method": null,
  "scale_pos_weight": null,
  "subsample": 0.8,
  "tree_method": null,
  "validate_parameters": null,
  "verbosity": null
}
```

---
*Báo cáo tự động sinh bởi `train_model.py`*
