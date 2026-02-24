import requests
import time
import subprocess
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )

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
                        print("Received:", text)

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

        except Exception as e:
            print("Polling error:", e)

        time.sleep(3)

if __name__ == "__main__":
    main()