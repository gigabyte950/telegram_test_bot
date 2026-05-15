import os
import logging
import json
import asyncio
from flask import Flask, request, jsonify
from bot import bot, dp
from aiogram.types import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Получаем токен для вебхука
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных окружения!")

WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    BASE_WEBHOOK_URL = 'https://telegram-test-bot-3u0f.onrender.com'

@app.route('/health', methods=['GET'])
def health_check():
    """Эндпоинт для проверки здоровья бота"""
    return jsonify({"status": "ok", "message": "Bot is running"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Обрабатывает входящие обновления от Telegram (синхронная версия)"""
    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        
        # Создаём event loop для асинхронной обработки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Создаём объект Update и передаём его диспетчеру
            update = Update.model_validate(update_data, context={"bot": bot})
            loop.run_until_complete(dp.feed_update(bot, update))
        finally:
            loop.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return jsonify({"status": "failed"}), 500

def set_webhook():
    """Устанавливает вебхук для бота"""
    if not BOT_TOKEN or not BASE_WEBHOOK_URL:
        logger.error("Не удалось установить вебхук")
        return

    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Удаляем старый вебхук
        loop.run_until_complete(bot.delete_webhook())
        logger.info("Старый вебхук удалён")
        
        # Устанавливаем новый
        loop.run_until_complete(bot.set_webhook(webhook_url))
        logger.info("✅ Новый вебхук установлен")
        
        # Проверяем
        info = loop.run_until_complete(bot.get_webhook_info())
        logger.info(f"Статус вебхука: {info.url}")
    except Exception as e:
        logger.error(f"Ошибка при настройке вебхука: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)
