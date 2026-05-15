import asyncio
import os
import logging
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
# Импортируем бота и диспетчер из нашего bot.py
from bot import bot, dp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Получаем токен и URL для вебхука
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных окружения!")
    # Выйти или продолжить, но лучше выйти
    # Для простоты продолжим, но вебхук не установится

WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
# Render сам предоставляет внешний URL через переменную окружения RENDER_EXTERNAL_URL
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    # Для локального тестирования (но на Render она всегда есть)
    BASE_WEBHOOK_URL = 'https://your-app-name.onrender.com' # Замените на ваш URL, если нужно
    logger.warning(f"RENDER_EXTERNAL_URL не задан, использую заглушку: {BASE_WEBHOOK_URL}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Bot is running"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook():
    """Принимает обновления от Telegram."""
    try:
        update_data = await request.get_json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return jsonify({"status": "failed"}), 500

def set_webhook():
    """Устанавливает вебхук для бота."""
    if not BOT_TOKEN or not BASE_WEBHOOK_URL:
        logger.error("Не удалось установить вебхук: отсутствует BOT_TOKEN или BASE_WEBHOOK_URL")
        return

    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")

    # Создаём новый event loop для асинхронной операции
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Используем метод bot.session, чтобы выполнить запрос
        # Можно проще: loop.run_until_complete(bot.set_webhook(webhook_url))
        # Но в aiogram 3.x bot.set_webhook - корутина
        loop.run_until_complete(bot.set_webhook(webhook_url))
        logger.info("Вебхук успешно установлен.")
    except Exception as e:
        logger.error(f"Ошибка при установке вебхука: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    # Устанавливаем вебхук перед запуском Flask
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    # Запускаем Flask
    app.run(host='0.0.0.0', port=port)