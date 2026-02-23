import subprocess
import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
UPDATE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

eastern = pytz.timezone("US/Eastern")

last_update_id = None
last_alert_date = None


def send_message(text):
    requests.post(
        SEND_URL,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def run_scanner():
    result = subprocess.run(
        ["python", "scan_today.py"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_updates(offset=None):
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset
    response = requests.get(UPDATE_URL, params=params)
    return response.json()


def auto_morning_alert():
    global last_alert_date

    now = datetime.now(eastern)

    # Weekdays only
    if now.weekday() < 5:
        # 9:25 AM trigger window
        if True:
            today_str = now.strftime("%Y-%m-%d")

            if last_alert_date != today_str:
                print("Running auto morning scan...")
                output = run_scanner()

                if output == "":
                    send_message("No high-quality trade today.")
                else:
                    send_message("📈 Morning Auto Signal\n\n" + output)

                last_alert_date = today_str


def main():
    global last_update_id

    print("Bot running with auto alerts...")

    while True:
        # --- AUTO ALERT ---
        auto_morning_alert()

        # --- MANUAL TELEGRAM COMMAND ---
        updates = get_updates(last_update_id)

        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1

                if "message" in update:
                    text = update["message"].get("text", "").lower()

                    if "signal" in text:
                        output = run_scanner()

                        if output == "":
                            send_message("No high-quality trade today.")
                        else:
                            send_message(output)

        time.sleep(30)


if __name__ == "__main__":
    main()