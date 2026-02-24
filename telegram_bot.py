from flask import Flask, request
import requests
import subprocess
import os

# ==============================
# ENV VARIABLES (Railway)
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# ==============================
# TELEGRAM SEND FUNCTION
# ==============================

def send_message(text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram send error:", e)


# ==============================
# RUN LONG SCANNER
# ==============================

def run_scanner():
    try:
        result = subprocess.run(
            ["python3", "scan_today.py"],
            capture_output=True,
            text=True
        )

        print("========== SCANNER DEBUG ==========")
        print("Return Code:", result.returncode)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print("===================================")

        if result.returncode != 0:
            return f"Scanner crashed:\n{result.stderr}"

        output = result.stdout.strip()

        if not output:
            return "Scanner ran but returned empty output."

        return output

    except Exception as e:
        return f"Scanner exception:\n{str(e)}"


# ==============================
# RUN MARKET RECAP
# ==============================

def run_recap():
    try:
        result = subprocess.run(
            ["python3", "market_recap.py"],  # IMPORTANT: python3
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        if not output:
            return "No recap data available."

        return output

    except Exception as e:
        return f"Recap error:\n{str(e)}"


# ==============================
# WEBHOOK ROUTE
# ==============================

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if data and "message" in data:
            text = data["message"].get("text", "").lower()

            print("Received:", text)

            if "signal" in text:
                send_message("🔍 Scanning for high-probability LONG setups...")
                output = run_scanner()
                send_message(output)

            elif "recap" in text:
                send_message("📊 Generating market recap...")
                output = run_recap()
                send_message(output)

        return "ok"

    except Exception as e:
        print("Webhook error:", e)
        return "error", 500


# ==============================
# START SERVER (Railway)
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)