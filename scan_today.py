import pandas as pd
import numpy as np
import yfinance as yf
from xgboost import XGBClassifier

# =========================
# SETTINGS
# =========================

THRESHOLD = 0.80
RISK_PER_TRADE = 60
HOLD_DAYS = 5

# =========================
# LOAD MODEL
# =========================

model = XGBClassifier()
model.load_model("model_long.json")

# =========================
# FEATURES
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

# =========================
# TICKERS
# =========================

tickers = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "JPM","V","MA","HD","XOM","LLY","PG","COST",
    "ABBV","KO","BAC","CRM","WMT","MCD","NFLX",
    "AMD","DIS","ORCL","INTC","TMO","ADBE","AVGO"
]

# =========================
# FEATURE BUILDER
# =========================

def build_features(df):

    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["sma200"] = df["Close"].rolling(200).mean()

    df["above_sma20"] = (df["Close"] > df["sma20"]).astype(int)
    df["above_sma50"] = (df["Close"] > df["sma50"]).astype(int)
    df["above_sma200"] = (df["Close"] > df["sma200"]).astype(int)

    df["dist_sma20"] = (df["Close"] - df["sma20"]) / df["sma20"]

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df["volume_spike"] = df["Volume"] / df["Volume"].rolling(20).mean()

    df["breakout_20d"] = (
        df["Close"] > df["Close"].rolling(20).max().shift(1)
    ).astype(int)

    df["atr"] = (df["High"] - df["Low"]).rolling(14).mean()

    return df

# =========================
# SCAN
# =========================

best_signal = None

for ticker in tickers:

    try:

        df = yf.download(ticker, period="1y", progress=False)

        if df.empty or len(df) < 200:
            continue

        # Flatten MultiIndex if needed
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = build_features(df)
        df = df.dropna()

        latest = df.iloc[-1]

        X = latest[features].values.reshape(1, -1)
        prob = model.predict_proba(X)[0][1]

        if prob > THRESHOLD:

            entry = latest["Close"]
            atr = latest["atr"]

            stop = entry - atr * 1.5
            risk = entry - stop

            if risk <= 0:
                continue

            target = entry + 3 * risk
            shares = int(RISK_PER_TRADE / risk)

            signal = {
                "ticker": ticker,
                "prob": prob,
                "entry": entry,
                "stop": stop,
                "target": target,
                "shares": shares
            }

            if best_signal is None or prob > best_signal["prob"]:
                best_signal = signal

    except Exception:
        continue

# =========================
# OUTPUT
# =========================

if best_signal:

    print("\n==============================")
    print("AGGRESSIVE LONG EXECUTION PLAN")
    print("==============================\n")

    print("Ticker:", best_signal["ticker"])
    print("Probability:", round(best_signal["prob"] * 100, 2), "%")
    print("\nEntry:", round(best_signal["entry"], 2))
    print("Stop:", round(best_signal["stop"], 2))
    print("3R Target:", round(best_signal["target"], 2))
    print("Shares:", best_signal["shares"])
    print("Max Hold:", HOLD_DAYS, "days")

    print("\nTrailing Plan:")
    print("• Move stop to breakeven at 1R")
    print("• Trail 1 ATR after 2R")

else:
    print("No high-quality long setup today.")
