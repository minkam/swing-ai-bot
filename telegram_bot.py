import requests
import time
import subprocess
import os

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =========================
# TELEGRAM FUNCTIONS
# =========================

def send_message(text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)


def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 100}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params)
    return response.json()


# =========================
# RUN SCANNER
# =========================

def run_scanner():
    try:
        result = subprocess.run(
            ["python", "scan_today.py"],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        if not output:
            return "No data available."

        return output

    except Exception as e:
        return f"Scanner error:\n{str(e)}"


# =========================
# BOT LOOP
# =========================

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

                    if "signal" in text:
                        send_message("🔍 Scanning...")
                        output = run_scanner()
                        send_message(output)

                    elif "recap" in text:
                        send_message("📊 Generating recap...")
                        result = subprocess.run(
                            ["python", "market_recap.py"],
                            capture_output=True,
                            text=True
                        )
                        send_message(result.stdout)

        time.sleep(2)


if __name__ == "__main__":
    main()