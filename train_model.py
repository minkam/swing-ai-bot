import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("dataset.csv")
df = df.dropna()

FEATURES = ["return_5", "return_10", "dist_sma20", "rsi"]

X = df[FEATURES]

y_long = df["long_target"]
y_short = df["short_target"]

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_long_train, y_long_test = train_test_split(
    X, y_long, test_size=0.2, shuffle=False
)

_, _, y_short_train, y_short_test = train_test_split(
    X, y_short, test_size=0.2, shuffle=False
)

# =========================
# HANDLE CLASS IMBALANCE
# =========================

scale_long = (len(y_long_train) - np.sum(y_long_train)) / np.sum(y_long_train)
scale_short = (len(y_short_train) - np.sum(y_short_train)) / np.sum(y_short_train)

# =========================
# LONG MODEL
# =========================

model_long = xgb.XGBClassifier(
    n_estimators=400,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_long,
    random_state=42
)

model_long.fit(X_train, y_long_train)

y_long_pred = model_long.predict(X_test)

print("\nLONG MODEL RESULTS")
print("Accuracy:", accuracy_score(y_long_test, y_long_pred))
print(classification_report(y_long_test, y_long_pred))

model_long.save_model("model_long.json")

# =========================
# SHORT MODEL
# =========================

model_short = xgb.XGBClassifier(
    n_estimators=400,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_short,
    random_state=42
)

model_short.fit(X_train, y_short_train)

y_short_pred = model_short.predict(X_test)

print("\nSHORT MODEL RESULTS")
print("Accuracy:", accuracy_score(y_short_test, y_short_pred))
print(classification_report(y_short_test, y_short_pred))

model_short.save_model("model_short.json")

print("\nModels saved successfully.")