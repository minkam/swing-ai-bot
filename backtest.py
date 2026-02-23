import pandas as pd
import numpy as np
import xgboost as xgb
import yfinance as yf

# =========================
# SETTINGS
# =========================

THRESHOLDS = [0.65, 0.70, 0.75, 0.80]
STOP_LEVELS = [0.02, 0.03, 0.04]

MAX_HOLD = 5
TRADE_COST = 0.002
RISK_PER_TRADE = 0.01
INITIAL_CAPITAL = 100000

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("dataset.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.dropna()

FEATURES = ["return_5", "return_10", "dist_sma20", "rsi"]

# =========================
# LOAD MODELS
# =========================

model_long = xgb.XGBClassifier()
model_long.load_model("model_long.json")

model_short = xgb.XGBClassifier()
model_short.load_model("model_short.json")

X = df[FEATURES]
df["long_prob"] = model_long.predict_proba(X)[:, 1]
df["short_prob"] = model_short.predict_proba(X)[:, 1]

# =========================
# MARKET REGIME
# =========================

spy = yf.download("SPY", period="10y", interval="1d", progress=False)

if isinstance(spy.columns, pd.MultiIndex):
    spy.columns = spy.columns.get_level_values(0)

spy["sma50"] = spy["Close"].rolling(50).mean()
spy["regime"] = np.where(spy["Close"] > spy["sma50"], "BULL", "BEAR")

spy.reset_index(inplace=True)

if "Date" not in spy.columns:
    spy.rename(columns={spy.columns[0]: "Date"}, inplace=True)

spy["Date"] = pd.to_datetime(spy["Date"])
spy = spy[["Date", "regime"]]

df = df.merge(spy, on="Date", how="left")

# =========================
# OUT OF SAMPLE (2 YEARS)
# =========================

cutoff_date = df["Date"].max() - pd.DateOffset(years=2)
df = df[df["Date"] >= cutoff_date].reset_index(drop=True)

# =========================
# ROBUSTNESS TEST
# =========================

print("\n===== ROBUSTNESS TEST RESULTS =====\n")

for threshold in THRESHOLDS:
    for stop_pct in STOP_LEVELS:

        capital = INITIAL_CAPITAL
        trades = []

        for i in range(len(df) - MAX_HOLD):

            row = df.iloc[i]
            regime = row["regime"]
            entry_price = row["Close"]

            position = None

            if regime == "BULL" and row["long_prob"] >= threshold:
                position = "LONG"

            elif regime == "BEAR" and row["short_prob"] >= threshold:
                position = "SHORT"

            if position is None:
                continue

            risk_amount = capital * RISK_PER_TRADE
            stop_distance = entry_price * stop_pct
            shares = risk_amount / stop_distance

            exit_price = None

            for j in range(1, MAX_HOLD + 1):
                future_price = df.iloc[i + j]["Close"]

                if position == "LONG":
                    if future_price <= entry_price * (1 - stop_pct):
                        exit_price = entry_price * (1 - stop_pct)
                        break

                elif position == "SHORT":
                    if future_price >= entry_price * (1 + stop_pct):
                        exit_price = entry_price * (1 + stop_pct)
                        break

            if exit_price is None:
                exit_price = df.iloc[i + MAX_HOLD]["Close"]

            if position == "LONG":
                ret = (exit_price - entry_price) / entry_price
            else:
                ret = (entry_price - exit_price) / entry_price

            ret -= TRADE_COST

            profit = shares * entry_price * ret
            capital += profit
            trades.append(ret)

        if len(trades) > 0:
            trades = np.array(trades)
            win_rate = np.mean(trades > 0)
            expectancy = np.mean(trades)

            print(f"Threshold: {threshold:.2f} | Stop: {stop_pct:.2f} "
                  f"| Trades: {len(trades)} "
                  f"| Win%: {win_rate*100:.1f} "
                  f"| Exp: {expectancy*100:.2f}% "
                  f"| Final: ${round(capital)}")
