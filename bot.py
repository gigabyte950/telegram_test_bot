# bot.py - основная логика Telegram бота (совместимая с aiogram 3.28.2)

import asyncio
import logging
import csv
import io
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

from config import BOT_TOKEN, ADMIN_ID
import database as db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера (ЭТИ ОБЪЕКТЫ ТЕПЕРЬ МОЖНО ИМПОРТИРОВАТЬ)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния для анкетирования
class AnketaForm(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()

# ---------- КЛАВИАТУРЫ ----------
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="fill_anketa")],
        [InlineKeyboardButton(text="📊 Мои данные", callback_data="my_data")]
    ])
    return keyboard

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton(text="📎 Выгрузить CSV", callback_data="admin_export")]
    ])
    return keyboard

# ---------- ОБРАБОТЧИКИ (ОНИ НЕ ИЗМЕНИЛИСЬ) ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_text = f"""
👋 Привет, {user_name}!

Я бот для сбора данных пользователей. Я могу:

📝 Запомнить твоё ФИО и номер телефона
📊 Показать твои сохранённые данные

Просто нажми на кнопку ниже, чтобы начать!
"""
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к этой команде!")
        return
    
    admin_text = """
🔐 **Админ-панель**

Здесь вы можете:
• Посмотреть всех пользователей
• Выгрузить данные в CSV-файл
"""
    await message.answer(admin_text, reply_markup=get_admin_keyboard())

@dp.callback_query(F.data == "fill_anketa")
async def start_anketa(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if db.user_exists(callback.from_user.id):
        user_data = db.get_user(callback.from_user.id)
        await callback.message.answer(
            f"📋 Вы уже заполняли анкету!\n\n"
            f"Ваши данные:\n"
            f"👤 ФИО: {user_data['full_name']}\n"
            f"📞 Телефон: {user_data['phone']}\n\n"
            f"Если хотите обновить данные — заполните анкету заново."
        )
    
    await callback.message.answer("✏️ Введите ваше ФИО (полностью):")
    await state.set_state(AnketaForm.waiting_for_full_name)

@dp.message(AnketaForm.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("❌ ФИО слишком короткое. Введите полное имя (минимум 3 символа):")
        return
    
    await state.update_data(full_name=message.text.strip())
    await message.answer("📞 Введите ваш номер телефона (в любом формате, только цифры):")
    await state.set_state(AnketaForm.waiting_for_phone)

@dp.message(AnketaForm.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    digits_only = ''.join(filter(str.isdigit, phone))
    if len(digits_only) < 10:
        await message.answer("❌ Номер телефона слишком короткий. Введите полный номер (минимум 10 цифр):")
        return
    
    user_data = await state.get_data()
    full_name = user_data['full_name']
    
    is_new = db.save_user(message.from_user.id, full_name, phone)
    
    if is_new:
        await message.answer(
            f"✅ Спасибо! Ваши данные сохранены!\n\n"
            f"📝 ФИО: {full_name}\n"
            f"📞 Телефон: {phone}"
        )
    else:
        await message.answer(
            f"🔄 Данные обновлены!\n\n"
            f"📝 ФИО: {full_name}\n"
            f"📞 Телефон: {phone}"
        )
    
    await state.clear()

@dp.callback_query(F.data == "my_data")
async def show_my_data(callback: types.CallbackQuery):
    await callback.answer()
    user_data = db.get_user(callback.from_user.id)
    
    if user_data:
        await callback.message.answer(
            f"📊 **Ваши данные:**\n\n"
            f"👤 ФИО: {user_data['full_name']}\n"
            f"📞 Телефон: {user_data['phone']}\n"
            f"📅 Дата заполнения: {user_data['created_at']}"
        )
    else:
        await callback.message.answer(
            "❌ Вы ещё не заполняли анкету.\n"
            "Нажмите кнопку 'Заполнить анкету'."
        )

@dp.callback_query(F.data == "admin_users")
async def admin_show_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return
    
    await callback.answer()
    users = db.get_all_users()
    
    if not users:
        await callback.message.answer("📭 Пока нет ни одного пользователя.")
        return
    
    text = "👥 **Список пользователей:**\n\n"
    for i, user in enumerate(users, 1):
        text += f"{i}. {user['full_name']} — {user['phone']}\n"
        text += f"   📅 {user['created_at']}\n\n"
    
    if len(text) > 4000:
        text = text[:3950] + "\n\n... (список обрезан)"
    
    await callback.message.answer(text)

@dp.callback_query(F.data == "admin_export")
async def admin_export_csv(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!", show_alert=True)
        return
    
    await callback.answer()
    users = db.get_all_users()
    
    if not users:
        await callback.message.answer("📭 Нет данных для выгрузки.")
        return
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Telegram ID", "ФИО", "Телефон", "Дата заполнения"])
    
    for i, user in enumerate(users, 1):
        writer.writerow([i, user['telegram_id'], user['full_name'], user['phone'], user['created_at']])
    
    output.seek(0)
    file_bytes = output.getvalue().encode('utf-8-sig')
    file = BufferedInputFile(file_bytes, filename="users.csv")
    
    await callback.message.answer_document(
        file,
        caption=f"📎 Выгрузка пользователей от {datetime.now().strftime('%Y-%m-%d')}"
    )

# ========== ИСПРАВЛЕНИЕ ЗДЕСЬ ==========
# Удаляем ВЕСЬ код, который запускал бота (asyncio.run(main()) и run_bot()).
# Теперь бот будет запускаться только из app.py через вебхуки.
# Объекты bot, dp и все обработчики остаются для импорта.

print("✅ Бот успешно импортирован. Обработчики загружены.")