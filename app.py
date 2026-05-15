import os
import logging
from flask import Flask, request, jsonify
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL')
if not BASE_URL:
    BASE_URL = 'https://telegram-test-bot-6m72.onrender.com'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния
class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Клавиатуры
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="fill")]
    ])

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("👋 Привет! Нажми кнопку, чтобы заполнить анкету:", reply_markup=main_keyboard())

@dp.callback_query(lambda c: c.data == "fill")
async def fill_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("✏️ Введите ваше ФИО:")
    await state.set_state(Form.waiting_for_name)

@dp.message(Form.waiting_for_name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📞 Введите ваш номер телефона:")
    await state.set_state(Form.waiting_for_phone)

@dp.message(Form.waiting_for_phone)
async def get_phone(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await msg.answer(f"✅ Спасибо! Ваши данные сохранены:\nФИО: {data['name']}\nТелефон: {msg.text}")
    await state.clear()

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        update_data = request.get_json()
        update = Update.model_validate(update_data, context={"bot": bot})
        asyncio.run(dp.feed_update(bot, update))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    webhook_url = f"{BASE_URL}/webhook/{BOT_TOKEN}"
    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": webhook_url})
    logger.info(f"Webhook set to {webhook_url}, response: {response.json()}")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
