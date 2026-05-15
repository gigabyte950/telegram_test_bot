# app.py - обёртка для запуска на хостинге Render
# Этот файл нужен, чтобы сервер не отключал вашего бота

import asyncio
import os
import threading
from flask import Flask, jsonify

# Импортируем настройки и функцию запуска бота
from config import BOT_TOKEN
import bot

# Создаём Flask-приложение для health-check
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health_check():
    """Эндпоинт для проверки, что бот жив"""
    return jsonify({
        "status": "ok",
        "message": "Bot is running!",
        "bot_token_configured": BOT_TOKEN != "YOUR_BOT_TOKEN_HERE"
    })

@app.route('/ping')
def ping():
    """Простой ping для мониторинга"""
    return "pong"

def run_bot():
    """Запускает бота в отдельном потоке"""
    try:
        bot.run_bot()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

# Запускаем бота при старте приложения
if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    print("✅ Flask сервер запущен, бот работает в фоне")
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)