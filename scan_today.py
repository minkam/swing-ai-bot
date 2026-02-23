import pandas as pd
import numpy as np
import xgboost as xgb
import yfinance as yf
from datetime import datetime, timedelta

# =========================
# SETTINGS
# =========================

THRESHOLD_SHARES = 0.75
THRESHOLD_OPTIONS = 0.80
RISK_SHARES = 0.02
RISK_OPTIONS = 0.03
ACCOUNT_SIZE = 3000
MAX_HOLD = 5
ATR_MULTIPLIER = 1.5

FEATURES = ["return_5", "return_10", "dist_sma20", "rsi"]

# =========================
# LOAD DATASET
# =========================

df = pd.read_csv("dataset.csv")

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"])

df = df.dropna()

latest_rows = df.sort_values("Date").groupby("Ticker").tail(1)

# =========================
# LOAD MODELS
# =========================

model_long = xgb.XGBClassifier()
model_long.load_model("model_long.json")

model_short = xgb.XGBClassifier()
model_short.load_model("model_short.json")

X = latest_rows[FEATURES]

latest_rows["long_prob"] = model_long.predict_proba(X)[:, 1]
latest_rows["short_prob"] = model_short.predict_proba(X)[:, 1]

# =========================
# MARKET REGIME (SPY 50 SMA)
# =========================

spy = yf.download("SPY", period="1y", interval="1d", progress=False)

if isinstance(spy.columns, pd.MultiIndex):
    spy.columns = spy.columns.get_level_values(0)

spy["sma50"] = spy["Close"].rolling(50).mean()

current_regime = (
    "BULL"
    if spy["Close"].iloc[-1] > spy["sma50"].iloc[-1]
    else "BEAR"
)

# =========================
# FIND BEST CANDIDATE
# =========================

candidates = []

for _, row in latest_rows.iterrows():

    if current_regime == "BULL" and row["long_prob"] >= THRESHOLD_SHARES:
        candidates.append((row["Ticker"], "LONG", row["long_prob"]))

    elif current_regime == "BEAR" and row["short_prob"] >= THRESHOLD_SHARES:
        candidates.append((row["Ticker"], "SHORT", row["short_prob"]))

if not candidates:
    print("\nNo high-quality trade today.")
    exit()

candidates = sorted(candidates, key=lambda x: x[2], reverse=True)
ticker, signal, prob = candidates[0]

# =========================
# LIVE PRICE + ATR
# =========================

data = yf.download(ticker, period="6mo", interval="1d", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

price = data["Close"].iloc[-1]

# ATR Calculation
high_low = data["High"] - data["Low"]
high_close = np.abs(data["High"] - data["Close"].shift())
low_close = np.abs(data["Low"] - data["Close"].shift())

ranges = pd.concat([high_low, high_close, low_close], axis=1)
true_range = ranges.max(axis=1)
atr = true_range.rolling(14).mean().iloc[-1]

stop_distance = atr * ATR_MULTIPLIER

# =========================
# STOP + TARGET
# =========================

if signal == "LONG":
    stop_price = round(price - stop_distance, 2)
    target_price = round(price + (stop_distance * 2), 2)
else:
    stop_price = round(price + stop_distance, 2)
    target_price = round(price - (stop_distance * 2), 2)

risk_per_share = abs(price - stop_price)
shares = int((ACCOUNT_SIZE * RISK_SHARES) / risk_per_share)

# =========================
# EARNINGS CHECK (SAFE)
# =========================

earnings_warning = ""

try:
    earnings_data = yf.Ticker(ticker).calendar

    if isinstance(earnings_data, pd.DataFrame) and not earnings_data.empty:
        earnings_date = earnings_data.index[0]
        if earnings_date < datetime.now() + timedelta(days=MAX_HOLD):
            earnings_warning = "⚠ Earnings within hold window!"

    elif isinstance(earnings_data, dict) and len(earnings_data) > 0:
        possible_date = list(earnings_data.values())[0]
        if isinstance(possible_date, (pd.Timestamp, datetime)):
            if possible_date < datetime.now() + timedelta(days=MAX_HOLD):
                earnings_warning = "⚠ Earnings within hold window!"

except Exception:
    earnings_warning = ""

# =========================
# OUTPUT
# =========================

print("\n==============================")
print("ADVANCED EXECUTION PLAN")
print("==============================\n")

print("Market Regime:", current_regime)
print("Ticker:", ticker)
print("Signal:", signal)
print("Probability:", round(prob * 100, 2), "%")
print("ATR:", round(atr, 2))

if earnings_warning:
    print(earnings_warning)

print("\n------ SHARES TRADE ------")
print("Entry Price:", round(price, 2))
print("ATR Stop:", stop_price)
print("2R Target:", target_price)
print("Shares:", shares)
print("Max Risk:", round(ACCOUNT_SIZE * RISK_SHARES, 2))
print("Max Hold:", MAX_HOLD, "days")

if prob >= THRESHOLD_OPTIONS:
    print("\n------ OPTIONS BOOST ------")
    print("Type:", "CALL" if signal == "LONG" else "PUT")
    print("Expiration: 10–21 days out")
    print("Strike: ATM")
    print("Risk:", round(ACCOUNT_SIZE * RISK_OPTIONS, 2))
    print("Exit: +100% gain or -50% loss")

print("\nTrailing Stop Rules:")
print("• Move stop to breakeven at 1R")
print("• Trail 1 ATR once in profit")

print("\n==============================\n")