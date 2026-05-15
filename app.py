import os
import logging
from flask import Flask, request, jsonify
import requests
import asyncio
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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Обработка входящих обновлений"""
    try:
        update_data = request.get_json()
        logger.info(f"Получен запрос: {str(update_data)[:100]}...")
        
        async def process():
            update = Update.model_validate(update_data, context={"bot": bot})
            await dp.feed_update(bot, update)
        
        asyncio.run(process())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "ok"}), 200

def set_webhook():
    """Установка вебхука"""
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")
    
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )
    logger.info(f"Результат: {response.json()}")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)
