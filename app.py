from flask import Flask, request, jsonify
import os
import openai
import requests

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

@app.route("/", methods=["GET"])
def home():
    return "Evyk core is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", {}).get("text", "")
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    if not chat_id or not message:
        return jsonify({"status": "ignored"})

    # Пример простого ответа
    reply = generate_evyk_reply(message)

    # Отправка ответа в Telegram
    requests.post(TELEGRAM_API_URL, json={
        "chat_id": chat_id,
        "text": reply
    })

    return jsonify({"status": "ok"})

def generate_evyk_reply(message):
    # Пока без OpenAI — просто шаблон
    return f"Ты написал: {message}\nЯ — Эвик, мэр City_108. Здесь мы живём по принципам вечных ценностей."

if __name__ == "__main__":
    app.run(debug=True)
