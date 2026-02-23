import requests
import time
import subprocess
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import pytz

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
SEND_URL = f"{BASE_URL}/sendMessage"

eastern = pytz.timezone("US/Eastern")

last_update_id = None
last_morning_alert = None
last_eod_report = None

# Simplified S&P 500 list (reliable subset)
SP500 = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","UNH","JPM",
    "V","XOM","LLY","MA","AVGO","HD","PG","MRK","COST","PEP",
    "ABBV","KO","ADBE","CRM","BAC","WMT","MCD","CSCO","TMO","ACN",
    "LIN","ABT","NFLX","AMD","CMCSA","DIS","ORCL","INTC","VZ","TXN",
    "PFE","NEE","INTU","PM","QCOM","NKE","HON","DHR","AMGN","IBM"
]

def send_message(text):
    if not text.strip():
        text = "No data available."
    requests.post(
        SEND_URL,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )
import sys

def run_scanner():
    result = subprocess.run(
        [sys.executable, "scan_today.py"],
        capture_output=True,
        text=True
    )
    return result.stdout
def get_top_movers():
    data = yf.download(SP500, period="2d", interval="1d", progress=False)

    closes = data["Close"]
    pct_change = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100

    movers = pct_change.sort_values(ascending=False)

    top_gainers = movers.head(10)
    top_losers = movers.tail(10)

    return top_gainers, top_losers

def format_eod_report():
    gainers, losers = get_top_movers()

    report = "📊 END OF DAY – S&P 500 MOVERS\n\n"

    report += "🚀 Top 10 Gainers:\n"
    for ticker, pct in gainers.items():
        report += f"{ticker}: {pct:.2f}%\n"

    report += "\n📉 Top 10 Losers:\n"
    for ticker, pct in losers.items():
        report += f"{ticker}: {pct:.2f}%\n"

    return report

def check_morning_alert():
    global last_morning_alert
    now = datetime.now(eastern)

    if now.weekday() < 5:
        if now.hour == 9 and now.minute == 35:
            today_str = now.strftime("%Y-%m-%d")
            if last_morning_alert != today_str:
                signal = run_scanner()
                send_message("📈 MORNING SIGNAL\n\n" + signal)
                last_morning_alert = today_str

def check_eod_report():
    global last_eod_report
    now = datetime.now(eastern)

    if now.weekday() < 5:
        if now.hour == 16 and now.minute == 10:
            today_str = now.strftime("%Y-%m-%d")
            if last_eod_report != today_str:
                report = format_eod_report()
                send_message(report)
                last_eod_report = today_str

def check_messages():
    global last_update_id

    updates = requests.get(
        f"{BASE_URL}/getUpdates",
        params={"offset": last_update_id}
    ).json()

    if "result" in updates:
        for update in updates["result"]:
            last_update_id = update["update_id"] + 1

            if "message" in update:
                text = update["message"].get("text", "").lower()

                if "signal" in text:
                    send_message("🔍 Scanning...")
                    output = run_scanner()
                    send_message(output)

                elif "recap" in text:
                    send_message("📊 Generating recap...")
                    report = format_eod_report()
                    send_message(report)

def main():
    print("Bot running...")

    while True:
        try:
            check_messages()
            check_morning_alert()
            check_eod_report()
            time.sleep(10)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()