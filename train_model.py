import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import joblib

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("dataset.csv")

# =========================
# SELECT FEATURES
# =========================

features = [
    "return_5",
    "return_10",
    "dist_sma20",
    "rsi",
    "volume_spike",
    "above_sma20",
    "above_sma50",
    "above_sma200",
    "breakout_20d"
]

X = df[features]
y = df["target_long"]

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, shuffle=False
)

# Handle class imbalance automatically
scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

# =========================
# MODEL (AGGRESSIVE)
# =========================

model = XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.04,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    use_label_encoder=False,
    eval_metric="logloss"
)

model.fit(X_train, y_train)

# =========================
# EVALUATE
# =========================

preds = model.predict(X_test)

print("\nLONG MODEL RESULTS")
print(classification_report(y_test, preds))

# =========================
# SAVE MODEL
# =========================

model.save_model("model_long.json")

print("\nLong-only aggressive model saved successfully.")