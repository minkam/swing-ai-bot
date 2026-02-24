import requests
import time
import os
import pandas as pd
import numpy as np
import yfinance as yf
from xgboost import XGBClassifier

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

THRESHOLD = 0.80
RISK_PER_TRADE = 60
HOLD_DAYS = 5

model = XGBClassifier()
model.load_model("model_long.json")

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

tickers = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "JPM","V","MA","HD","XOM","LLY","PG","COST",
    "ABBV","KO","BAC","CRM","WMT","MCD","NFLX",
    "AMD","DIS","ORCL","INTC","TMO","ADBE","AVGO"
]

def send_message(text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )

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

def run_scanner():

    best_signal = None

    for ticker in tickers:

        try:
            df = yf.download(ticker, period="1y", progress=False)

            if df.empty or len(df) < 200:
                continue

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

                best_signal = (
                    f"\nAGGRESSIVE LONG SETUP\n\n"
                    f"Ticker: {ticker}\n"
                    f"Probability: {round(prob*100,2)}%\n"
                    f"Entry: {round(entry,2)}\n"
                    f"Stop: {round(stop,2)}\n"
                    f"Target: {round(target,2)}\n"
                    f"Shares: {shares}\n"
                    f"Max Hold: {HOLD_DAYS} days"
                )

                break

        except:
            continue

    if best_signal:
        return best_signal
    else:
        return "No high-quality long setup today."

def main():
    print("Bot running...")
    last_update_id = None

    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": last_update_id, "timeout": 5}
            )
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"] + 1

                    if "message" in update:
                        text = update["message"].get("text", "").lower()

                        if "signal" in text:
                            send_message("🔍 Scanning...")
                            output = run_scanner()
                            send_message(output)

        except Exception as e:
            print("Error:", e)

        time.sleep(3)

if __name__ == "__main__":
    main()