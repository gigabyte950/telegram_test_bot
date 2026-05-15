# config.py - настройки бота

import os

# Токен бота, полученный от @BotFather
# На хостинге используем переменную окружения, на компьютере - значение по умолчанию
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Telegram ID администратора (целое число)
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Проверка: если токен не заменён, выводим предупреждение
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("⚠️ ВНИМАНИЕ: Не забудьте заменить YOUR_BOT_TOKEN_HERE на реальный токен в config.py!")