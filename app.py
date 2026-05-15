import os
import logging
from flask import Flask, request, jsonify
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ИНИЦИАЛИЗАЦИЯ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_URL:
    BASE_URL = 'https://telegram-test-bot-6m72.onrender.com'

app = Flask(__name__)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ TELEGRAM API (СИНХРОННЫЕ) ---
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка send_message: {e}")
        return None

def answer_callback(callback_id, text=None, show_alert=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {'callback_query_id': callback_id}
    if text:
        payload['text'] = text
        payload['show_alert'] = show_alert
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Ошибка answer_callback: {e}")

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 Заполнить анкету", "callback_data": "fill_anketa"}],
            [{"text": "📊 Мои данные", "callback_data": "my_data"}]
        ]
    }

def get_admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "👥 Список пользователей", "callback_data": "admin_users"}],
            [{"text": "📎 Выгрузить CSV", "callback_data": "admin_export"}]
        ]
    }

# --- ОБРАБОТЧИКИ ЗАПРОСОВ (СИНХРОННЫЕ) ---
def process_start(chat_id):
    text = "👋 Привет! Я бот для сбора данных. Нажми на кнопку:"
    send_message(chat_id, text, reply_markup=get_main_keyboard())

def process_fill_anketa(callback_id, chat_id, message_id):
    answer_callback(callback_id)
    send_message(chat_id, "✏️ Введите ваше ФИО (полностью):")
    # Здесь нужно сохранить состояние, что пользователь в процессе заполнения.
    # Для простоты пока просто ответим. Позже добавим словарь состояний.

def process_my_data(callback_id, chat_id):
    answer_callback(callback_id, "Ваши данные: ...", show_alert=False)
    # Заглушка

def process_admin_users(callback_id, chat_id):
    answer_callback(callback_id)
    send_message(chat_id, "👥 Список пользователей: (пока пуст)")

def process_admin_export(callback_id, chat_id):
    answer_callback(callback_id)
    send_message(chat_id, "📎 Экспорт CSV: (функция в разработке)")

# --- МАРШРУТИЗАТОР (СЕРДЦЕ БОТА) ---
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        logger.info(f"Получен update: {update}")

        # Обработка сообщений
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text')
            if text == '/start':
                process_start(chat_id)
            # Здесь будет обработка текста от пользователя (ФИО, телефон)

        # Обработка нажатий на кнопки
        elif 'callback_query' in update:
            callback = update['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            data = callback['data']

            if data == 'fill_anketa':
                process_fill_anketa(callback_id, chat_id, message_id)
            elif data == 'my_data':
                process_my_data(callback_id, chat_id)
            elif data == 'admin_users':
                process_admin_users(callback_id, chat_id)
            elif data == 'admin_export':
                process_admin_export(callback_id, chat_id)
            else:
                answer_callback(callback_id, "Неизвестная команда", show_alert=True)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}")
        return jsonify({"status": "error"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Установка вебхука
    webhook_url = f"{BASE_URL}/webhook/{BOT_TOKEN}"
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )
    logger.info(f"Webhook set to {webhook_url}, response: {response.json()}")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
