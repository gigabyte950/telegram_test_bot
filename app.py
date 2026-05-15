import os
import logging
import asyncio
import concurrent.futures
from flask import Flask, request, jsonify
from bot import bot, dp
from aiogram.types import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    BASE_WEBHOOK_URL = 'https://telegram-test-bot-3u0f.onrender.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'

# Создаём один постоянный event loop в фоновом потоке
loop = asyncio.new_event_loop()

def start_background_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Запускаем фоновый поток с event loop
import threading
threading.Thread(target=start_background_loop, daemon=True).start()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Мгновенная обработка вебхука без ожидания"""
    try:
        update_data = request.get_json()
        
        # Отправляем задачу в фоновый event loop
        async def process():
            update = Update.model_validate(update_data, context={"bot": bot})
            await dp.feed_update(bot, update)
        
        # Не ждём результат! Ставим в очередь и сразу отвечаем
        asyncio.run_coroutine_threadsafe(process(), loop)
        
        # Мгновенный ответ Telegram, чтобы не было таймаута
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Ошибка при получении вебхука: {e}")
        return jsonify({"status": "ok"}), 200  # Всегда отвечаем 200

def set_webhook():
    """Установка вебхука при запуске"""
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")
    
    async def setup():
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url)
        logger.info("✅ Вебхук установлен")
    
    # Запускаем в нашем фоновом event loop
    future = asyncio.run_coroutine_threadsafe(setup(), loop)
    future.result(timeout=30)

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
