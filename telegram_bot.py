from flask import Flask, request
import requests
import subprocess
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

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
            return "No high-quality long setup today."
        return output
    except Exception as e:
        return f"Scanner error:\n{str(e)}"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if data and "message" in data:
        text = data["message"].get("text", "").lower()

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

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)