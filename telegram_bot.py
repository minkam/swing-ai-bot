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
            return "No high-quality long setup today."

        return output

    except Exception as e:
        return f"Scanner exception:\n{str(e)}"

# ==============================
# RUN MARKET RECAP
# ==============================

def run_recap():
    try:
        result = subprocess.run(
            ["python3", "market_recap.py"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return f"Recap crashed:\n{result.stderr}"

        output = result.stdout.strip()

        if not output:
            return "No recap data available."

        return output

    except Exception as e:
        return f"Recap exception:\n{str(e)}"

# ==============================
# WEBHOOK ROUTE
# ==============================

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return "ok"

        text = data["message"].get("text", "").strip().lower()
        print("Received:", text)

        # Normalize command (remove leading slash)
        if text.startswith("/"):
            text = text[1:]

        if text == "signal":
            output = run_scanner()
            final_message = "🔍 Swing Scan Result:\n\n" + output
            send_message(final_message)

        elif text == "recap":
            output = run_recap()
            final_message = "📊 Market Recap:\n\n" + output
            send_message(final_message)

        elif text == "start":
            send_message("Bot is live. Type 'signal' or 'recap'.")

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
