import pandas as pd
import numpy as np
import yfinance as yf
from tqdm import tqdm

# =========================
# SETTINGS
# =========================

START_DATE = "2015-01-01"
END_DATE = None
FUTURE_DAYS = 5
TARGET_MOVE = 0.04   # 4% move target (aggressive)

# =========================
# S&P 500 LIQUID SUBSET
# =========================

def get_sp500():
    return [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
        "JPM","V","MA","HD","XOM","LLY","PG","COST",
        "ABBV","KO","BAC","CRM","WMT","MCD","NFLX",
        "AMD","DIS","ORCL","INTC","TMO","ADBE","AVGO"
    ]

# =========================
# FEATURE ENGINEERING
# =========================

def build_features(df):

    # Momentum
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    # Trend
    df["sma20"] = df["Close"].rolling(20).mean()
    df["sma50"] = df["Close"].rolling(50).mean()
    df["sma200"] = df["Close"].rolling(200).mean()

    df["above_sma20"] = (df["Close"] > df["sma20"]).astype(int)
    df["above_sma50"] = (df["Close"] > df["sma50"]).astype(int)
    df["above_sma200"] = (df["Close"] > df["sma200"]).astype(int)

    # Distance from short MA
    df["dist_sma20"] = (df["Close"] - df["sma20"]) / df["sma20"]

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # Volume expansion
    df["volume_spike"] = df["Volume"] / df["Volume"].rolling(20).mean()

    # Breakout detection
    df["breakout_20d"] = (
        df["Close"] > df["Close"].rolling(20).max().shift(1)
    ).astype(int)

    return df

# =========================
# LABEL CREATION (LONG ONLY)
# =========================

def build_labels(df):

    df["future_max"] = (
        df["High"]
        .rolling(FUTURE_DAYS)
        .max()
        .shift(-FUTURE_DAYS)
    )

    df["target_long"] = (
        (df["future_max"] - df["Close"]) / df["Close"]
        >= TARGET_MOVE
    ).astype(int)

    return df

# =========================
# MAIN BUILDER
# =========================

def main():

    tickers = get_sp500()
    all_data = []

    for ticker in tqdm(tickers):

        try:
            df = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                progress=False
            )

            if df.empty or len(df) < 250:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index()
            df["Ticker"] = ticker

            df = build_features(df)
            df = build_labels(df)

            df = df.dropna()

            all_data.append(df)

        except Exception as e:
            print(f"{ticker} failed:", e)

    if not all_data:
        print("No data collected.")
        return

    data = pd.concat(all_data)
    data.to_csv("dataset.csv", index=False)

    print("\nLong-Only Aggressive Dataset Built")
    print("Rows:", len(data))
    print("Tickers:", len(data["Ticker"].unique()))

if __name__ == "__main__":
    main()