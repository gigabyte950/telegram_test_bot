import os
import logging
import asyncio
from flask import Flask, request, jsonify
from bot import bot, dp
from aiogram.types import Update
from aiogram import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    BASE_WEBHOOK_URL = 'https://telegram-test-bot-3u0f.onrender.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'

# Создаём один event loop для всего приложения
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Быстрая обработка всех обновлений от Telegram"""
    try:
        # Получаем данные
        update_data = request.get_json()
        
        # Запускаем обработку асинхронно
        async def process():
            update = Update.model_validate(update_data, context={"bot": bot})
            await dp.feed_update(bot, update)
        
        # Ждём завершения обработки (не больше 10 секунд)
        future = asyncio.run_coroutine_threadsafe(process(), loop)
        future.result(timeout=10)  # Важно: не больше 10 секунд для callback-запросов
        
        return jsonify({"status": "ok"}), 200
        
    except asyncio.TimeoutError:
        logger.error("Ошибка: обработка заняла больше 10 секунд")
        return jsonify({"status": "timeout"}), 200  # Возвращаем 200, чтобы Telegram не повторял
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error"}), 200  # Всегда возвращаем 200

def set_webhook():
    """Установка вебхука при запуске"""
    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")
    
    async def setup():
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url, timeout=30)
        logger.info("✅ Вебхук установлен")
    
    loop.run_until_complete(setup())

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
