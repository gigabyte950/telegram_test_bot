import os
import logging
from flask import Flask, request, jsonify
import requests
from config import BOT_TOKEN, ADMIN_ID
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BASE_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegram-test-bot-6m72.onrender.com')

# Инициализация базы данных
db.init_db()

# --- Функции для работы с Telegram API ---
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"send_message error: {e}")

def answer_callback(callback_id, text=None, show_alert=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {'callback_query_id': callback_id}
    if text:
        payload['text'] = text
        payload['show_alert'] = show_alert
    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"answer_callback error: {e}")

# --- Клавиатуры ---
def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 Заполнить анкету", "callback_data": "fill"}],
            [{"text": "📊 Мои данные", "callback_data": "my_data"}]
        ]
    }

def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "👥 Список пользователей", "callback_data": "admin_users"}],
            [{"text": "📎 Выгрузить CSV", "callback_data": "admin_export"}]
        ]
    }

# --- Обработчики ---
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        logger.info(f"Update received: {update}")

        # Обработка команды /start
        if 'message' in update and update['message'].get('text') == '/start':
            chat_id = update['message']['chat']['id']
            send_message(chat_id, "👋 Привет! Нажми на кнопку:", reply_markup=main_keyboard())

        # Обработка команды /admin
        elif 'message' in update and update['message'].get('text') == '/admin':
            chat_id = update['message']['chat']['id']
            if chat_id == ADMIN_ID:
                send_message(chat_id, "🔐 Админ-панель:", reply_markup=admin_keyboard())
            else:
                send_message(chat_id, "⛔ Нет доступа")

        # Обработка нажатий на кнопки
        elif 'callback_query' in update:
            callback = update['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            message_id = callback['message']['message_id']

            if data == 'fill':
                answer_callback(callback_id)
                send_message(chat_id, "✏️ Введите ваше ФИО:")
                # TODO: сохранить состояние пользователя (что он в процессе заполнения)

            elif data == 'my_data':
                user = db.get_user(chat_id)
                if user:
                    answer_callback(callback_id, f"Ваши данные: {user[0]}, {user[1]}")
                else:
                    answer_callback(callback_id, "Вы ещё не заполняли анкету")

            elif data == 'admin_users' and chat_id == ADMIN_ID:
                answer_callback(callback_id)
                users = db.get_all_users()
                if users:
                    text = "👥 Список пользователей:\n"
                    for u in users:
                        text += f"- {u[1]} ({u[2]})\n"
                    send_message(chat_id, text)
                else:
                    send_message(chat_id, "Пока нет пользователей")

            elif data == 'admin_export' and chat_id == ADMIN_ID:
                answer_callback(callback_id)
                send_message(chat_id, "📎 Выгрузка CSV будет позже")

            else:
                answer_callback(callback_id, "Неизвестная команда", show_alert=True)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    webhook_url = f"{BASE_URL}/webhook/{BOT_TOKEN}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": webhook_url})
    logger.info(f"Webhook set to {webhook_url}")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
