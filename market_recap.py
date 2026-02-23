import yfinance as yf
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Static S&P 500 list (avoids Wikipedia 403 errors)
SP500 = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","UNH","JPM",
    "V","XOM","LLY","MA","AVGO","HD","PG","MRK","COST","PEP",
    "ABBV","KO","ADBE","CRM","BAC","WMT","MCD","CSCO","TMO","ACN",
    "LIN","ABT","NFLX","AMD","CMCSA","DIS","ORCL","INTC","VZ","TXN",
    "PFE","NEE","INTU","PM","QCOM","NKE","HON","DHR","AMGN","IBM"
]

def send_message(text):
    requests.post(
        SEND_URL,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def get_top_movers():
    data = yf.download(SP500, period="2d", interval="1d", progress=False)

    closes = data["Close"]
    pct_change = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100

    movers = pct_change.sort_values(ascending=False)

    top_gainers = movers.head(10)
    top_losers = movers.tail(10)

    return top_gainers, top_losers

def format_report(gainers, losers):
    report = "📊 END OF DAY – S&P 500 MOVERS\n\n"

    report += "🚀 Top 10 Gainers:\n"
    for ticker, pct in gainers.items():
        report += f"{ticker}: {pct:.2f}%\n"

    report += "\n📉 Top 10 Losers:\n"
    for ticker, pct in losers.items():
        report += f"{ticker}: {pct:.2f}%\n"

    return report

def main():
    gainers, losers = get_top_movers()
    report = format_report(gainers, losers)
    send_message(report)

if __name__ == "__main__":
    main()