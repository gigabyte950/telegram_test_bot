import os
import logging
from flask import Flask, request, jsonify
import requests
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
BASE_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Клавиатуры
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="fill")]
    ])

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Привет! Нажми кнопку:", reply_markup=main_keyboard())

@dp.callback_query(F.data == "fill")
async def fill(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Введите ваше ФИО:")

app = Flask(__name__)

@app.route('/health')
def health():
    return 'ok'

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = types.Update(**request.get_json())
    asyncio.run(dp.feed_update(bot, update))
    return 'ok'

if __name__ == '__main__':
    webhook_url = f"{BASE_URL}/webhook/{BOT_TOKEN}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", json={"url": webhook_url})
    logger.info(f"Webhook set to {webhook_url}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
