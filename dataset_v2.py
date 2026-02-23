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
TARGET_MOVE = 0.03  # 3% move target

# =========================
# GET S&P 500 TICKERS
# =========================
def get_sp500():
    # Static S&P 500 subset for stability (top liquid names)
    tickers = [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG",
        "TSLA","BRK-B","UNH","XOM","JPM","V","PG","MA",
        "HD","CVX","ABBV","PEP","COST","AVGO","KO","MRK",
        "LLY","WMT","BAC","MCD","CRM","ACN","ADBE",
        "AMD","NFLX","TMO","INTC","LIN","ABT","DIS",
        "TXN","PM","VZ","CMCSA","QCOM","DHR","NEE",
        "RTX","HON","LOW","UPS","SPGI"
    ]
    return tickers

# =========================
# FEATURE ENGINEERING
# =========================

def build_features(df):
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)
    df["sma20"] = df["Close"].rolling(20).mean()
    df["dist_sma20"] = (df["Close"] - df["sma20"]) / df["sma20"]

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# =========================
# LABEL CREATION
# =========================

def build_labels(df):
    df["future_max"] = df["High"].rolling(FUTURE_DAYS).max().shift(-FUTURE_DAYS)
    df["future_min"] = df["Low"].rolling(FUTURE_DAYS).min().shift(-FUTURE_DAYS)

    df["long_target"] = (
        (df["future_max"] - df["Close"]) / df["Close"] >= TARGET_MOVE
    ).astype(int)

    df["short_target"] = (
        (df["Close"] - df["future_min"]) / df["Close"] >= TARGET_MOVE
    ).astype(int)

    return df

# =========================
# MAIN DATASET BUILDER
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
                progress=False,
            )

            if df.empty or len(df) < 100:
                continue

            # Flatten MultiIndex if needed
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

    if len(all_data) == 0:
        print("No data collected.")
        return

    data = pd.concat(all_data)
    data.to_csv("dataset.csv", index=False)

    print("\nDataset built successfully.")
    print("Rows:", len(data))
    print("Tickers used:", len(data["Ticker"].unique()))

if __name__ == "__main__":
    main()