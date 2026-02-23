import subprocess
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in .env")
    exit()

SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
UPDATE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"


def send_message(text):
    response = requests.post(
        SEND_URL,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )
    print("Send response:", response.text)


def run_scanner():
    result = subprocess.run(
        ["python", "scan_today.py"],
        capture_output=True,
        text=True
    )
    return result.stdout


def get_updates(offset=None):
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset

    response = requests.get(UPDATE_URL, params=params)
    return response.json()


def main():
    print("Bot running...")
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)

        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1

                if "message" in update:
                    text = update["message"].get("text", "").lower()
                    print("Received:", text)

                    if "signal" in text:
                        output = run_scanner()

                        if output.strip() == "":
                            send_message("No high-quality trade today.")
                        else:
                            send_message(output)

        time.sleep(2)


if __name__ == "__main__":
    main()