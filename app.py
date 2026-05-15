import os
import logging
import asyncio
import concurrent.futures
from flask import Flask, request, jsonify
from bot import bot, dp
from aiogram.types import Update
from aiogram import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных окружения!")

WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    BASE_WEBHOOK_URL = 'https://telegram-test-bot-3u0f.onrender.com'

# Создаём постоянный event loop для всего приложения
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Обрабатывает входящие обновления от Telegram"""
    try:
        update_data = request.get_json()
        
        # Создаём задачу в существующем event loop
        async def process_update():
            update = Update.model_validate(update_data, context={"bot": bot})
            await dp.feed_update(bot, update)
        
        # Запускаем асинхронную обработку в существующем event loop
        future = asyncio.run_coroutine_threadsafe(process_update(), loop)
        future.result(timeout=30)  # Ждём результат не более 30 секунд
        
        return jsonify({"status": "ok"}), 200
    except concurrent.futures.TimeoutError:
        logger.error("Ошибка: превышено время ожидания обработки обновления")
        return jsonify({"status": "timeout"}), 500
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "failed"}), 500

def set_webhook():
    """Устанавливает вебхук для бота"""
    if not BOT_TOKEN or not BASE_WEBHOOK_URL:
        logger.error("Не удалось установить вебхук")
        return

    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")

    async def setup():
        await bot.delete_webhook()
        logger.info("Старый вебхук удалён")
        await bot.set_webhook(webhook_url)
        logger.info("✅ Новый вебхук установлен")
        info = await bot.get_webhook_info()
        logger.info(f"Статус вебхука: {info.url}")
    
    loop.run_until_complete(setup())

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск Flask на порту {port}")
    
    # Запускаем задачу поддержания event loop в фоне
    def run_loop():
        loop.run_forever()
    
    import threading
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    
    app.run(host='0.0.0.0', port=port)
