import yfinance as yf
import pandas as pd
import numpy as np
from tqdm import tqdm

START_DATE = "2015-01-01"
HOLD_DAYS = 5
TARGET_RETURN = 0.03

def get_tickers():
    return [
        "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA",
        "JPM","V","UNH","HD","PG","MA","BAC","XOM",
        "DIS","NFLX","AMD","INTC","CRM","PFE","KO","PEP"
    ]

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def build_features(df):

    # Basic returns
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    # SMA
    df["sma_20"] = df["Close"].rolling(20).mean()
    df["dist_sma20"] = (df["Close"] - df["sma_20"]) / df["sma_20"]

    # RSI (manual implementation)
    df["rsi"] = compute_rsi(df["Close"], 14)

    # Future return
    df["future_return"] = df["Close"].shift(-HOLD_DAYS) / df["Close"] - 1

    # Long & Short targets
    df["target_long"] = (df["future_return"] > TARGET_RETURN).astype(int)
    df["target_short"] = (df["future_return"] < -TARGET_RETURN).astype(int)

    return df

def main():

    tickers = get_tickers()
    all_data = []

    for ticker in tqdm(tickers):

        try:
            df = yf.download(
                ticker,
                start=START_DATE,
                auto_adjust=True,
                progress=False
            )

            if df.empty:
                continue

            df = df[['Open','High','Low','Close','Volume']].copy()

            df = build_features(df)
            df.dropna(inplace=True)

            if len(df) < 200:
                continue

            df["ticker"] = ticker
            all_data.append(df)

        except Exception as e:
            print(f"{ticker} failed: {e}")
            continue

    if len(all_data) == 0:
        print("No usable data collected.")
        return

    data = pd.concat(all_data)
    data.to_csv("dataset.csv")

    print("\nDataset successfully built.")
    print("Total rows:", len(data))
    print("Tickers used:", len(all_data))

if __name__ == "__main__":
    main()