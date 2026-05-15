import asyncio
import os
import logging
from flask import Flask, request, jsonify
from aiogram.types import Update
# Импортируем бота и диспетчер из bot.py
from bot import bot, dp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Получаем токен и URL для вебхука
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных окружения!")

# Формируем путь для вебхука (с токеном для безопасности)
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'

# Render сам предоставляет внешний URL через переменную окружения RENDER_EXTERNAL_URL
BASE_WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_WEBHOOK_URL:
    # Для локального тестирования (на Render эта переменная всегда есть)
    logger.warning("RENDER_EXTERNAL_URL не задан")
    BASE_WEBHOOK_URL = 'https://telegram-test-bot-3u0f.onrender.com'  # Ваш URL

@app.route('/health', methods=['GET'])
def health_check():
    """Эндпоинт для проверки здоровья бота"""
    return jsonify({"status": "ok", "message": "Bot is running"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook():
    """Принимает обновления от Telegram"""
    try:
        update_data = await request.get_json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return jsonify({"status": "failed"}), 500

def set_webhook():
    """Устанавливает вебхук для бота (предварительно удаляя старый)"""
    if not BOT_TOKEN or not BASE_WEBHOOK_URL:
        logger.error("Не удалось установить вебхук: отсутствует BOT_TOKEN или BASE_WEBHOOK_URL")
        return

    webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
    logger.info(f"Установка вебхука на: {webhook_url}")

    # Создаём новый event loop для асинхронных операций
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # ШАГ 1: Удаляем старый вебхук (если был)
        logger.info("Удаляем старый вебхук...")
        loop.run_until_complete(bot.delete_webhook())
        logger.info("Старый вебхук удалён.")
        
        # ШАГ 2: Устанавливаем новый вебхук
        logger.info(f"Устанавливаем новый вебхук на {webhook_url}...")
        loop.run_until_complete(bot.set_webhook(webhook_url))
        logger.info("✅ Вебхук успешно установлен!")
        
        # Небольшая проверка: получаем информацию о вебхуке
        webhook_info = loop.run_until_complete(bot.get_webhook_info())
        logger.info(f"Информация о вебхуке: url={webhook_info.url}, ok={webhook_info.url is not None}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке вебхука: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    # Настраиваем вебхук перед запуском Flask
    set_webhook()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск Flask сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port)
