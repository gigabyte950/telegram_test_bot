# database.py - работа с базой данных SQLite

import sqlite3
from datetime import datetime

# Название файла базы данных
DB_NAME = "users.db"

def init_db():
    """Создаёт таблицу в базе данных, если её ещё нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def save_user(telegram_id: int, full_name: str, phone: str) -> bool:
    """
    Сохраняет пользователя в базу данных.
    Возвращает True, если пользователь новый, False - если обновлён существующий
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Пытаемся вставить нового пользователя
        cursor.execute("""
            INSERT INTO users (telegram_id, full_name, phone) 
            VALUES (?, ?, ?)
        """, (telegram_id, full_name, phone))
        conn.commit()
        is_new = True
    except sqlite3.IntegrityError:
        # Пользователь уже существует - обновляем данные
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, phone = ?, created_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        """, (full_name, phone, telegram_id))
        conn.commit()
        is_new = False
    
    conn.close()
    return is_new

def get_user(telegram_id: int):
    """Возвращает данные пользователя по его Telegram ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT full_name, phone, created_at FROM users 
        WHERE telegram_id = ?
    """, (telegram_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "full_name": result[0],
            "phone": result[1],
            "created_at": result[2]
        }
    return None

def get_all_users():
    """Возвращает список всех пользователей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT telegram_id, full_name, phone, created_at FROM users 
        ORDER BY created_at DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    users = []
    for row in results:
        users.append({
            "telegram_id": row[0],
            "full_name": row[1],
            "phone": row[2],
            "created_at": row[3]
        })
    
    return users

def user_exists(telegram_id: int) -> bool:
    """Проверяет, существует ли пользователь в базе"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None