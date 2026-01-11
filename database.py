import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH


def get_connection():
    """Получить соединение с базой данных"""
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    """Инициализация базы данных - создание таблиц"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            weight REAL,
            height REAL,
            age INTEGER,
            gender TEXT DEFAULT 'male',
            activity_minutes INTEGER DEFAULT 0,
            city TEXT,
            calorie_goal REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица логов воды
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_ml INTEGER,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица логов еды
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_name TEXT,
            calories REAL,
            grams REAL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица логов тренировок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            workout_type TEXT,
            duration_minutes INTEGER,
            calories_burned REAL,
            water_extra_ml INTEGER,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()


# ==================== ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ ====================

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Получить данные пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['user_id', 'weight', 'height', 'age', 'gender', 
                   'activity_minutes', 'city', 'calorie_goal', 'created_at', 'updated_at']
        return dict(zip(columns, row))
    return None


def create_or_update_user(user_id: int, **kwargs) -> None:
    """Создать или обновить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем существует ли пользователь
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Обновляем существующего пользователя
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        set_clause += ', updated_at = ?'
        values = list(kwargs.values()) + [datetime.now(), user_id]
        cursor.execute(f'UPDATE users SET {set_clause} WHERE user_id = ?', values)
    else:
        # Создаём нового пользователя
        columns = ['user_id'] + list(kwargs.keys())
        placeholders = ', '.join(['?' for _ in columns])
        values = [user_id] + list(kwargs.values())
        cursor.execute(f'INSERT INTO users ({", ".join(columns)}) VALUES ({placeholders})', values)
    
    conn.commit()
    conn.close()


# ==================== ОПЕРАЦИИ С ВОДОЙ ====================

def log_water(user_id: int, amount_ml: int) -> None:
    """Записать потребление воды"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO water_logs (user_id, amount_ml) VALUES (?, ?)',
        (user_id, amount_ml)
    )
    conn.commit()
    conn.close()


def get_today_water(user_id: int) -> int:
    """Получить количество воды, выпитой сегодня"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(amount_ml), 0) 
        FROM water_logs 
        WHERE user_id = ? AND DATE(logged_at) = ?
    ''', (user_id, today))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_water_history(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """Получить историю потребления воды за последние N дней"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(logged_at) as day, SUM(amount_ml) as total
        FROM water_logs
        WHERE user_id = ? AND logged_at >= date('now', ?)
        GROUP BY DATE(logged_at)
        ORDER BY day
    ''', (user_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [{'date': row[0], 'amount': row[1]} for row in rows]


# ==================== ОПЕРАЦИИ С ЕДОЙ ====================

def log_food(user_id: int, food_name: str, calories: float, grams: float) -> None:
    """Записать потребление еды"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO food_logs (user_id, food_name, calories, grams) VALUES (?, ?, ?, ?)',
        (user_id, food_name, calories, grams)
    )
    conn.commit()
    conn.close()


def get_today_calories_consumed(user_id: int) -> float:
    """Получить количество калорий, потреблённых сегодня"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(calories), 0) 
        FROM food_logs 
        WHERE user_id = ? AND DATE(logged_at) = ?
    ''', (user_id, today))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_food_history(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """Получить историю потребления калорий за последние N дней"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(logged_at) as day, SUM(calories) as total
        FROM food_logs
        WHERE user_id = ? AND logged_at >= date('now', ?)
        GROUP BY DATE(logged_at)
        ORDER BY day
    ''', (user_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [{'date': row[0], 'calories': row[1]} for row in rows]


# ==================== ОПЕРАЦИИ С ТРЕНИРОВКАМИ ====================

def log_workout(user_id: int, workout_type: str, duration: int, 
                calories_burned: float, water_extra: int) -> None:
    """Записать тренировку"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO workout_logs 
        (user_id, workout_type, duration_minutes, calories_burned, water_extra_ml) 
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, workout_type, duration, calories_burned, water_extra))
    conn.commit()
    conn.close()


def get_today_calories_burned(user_id: int) -> float:
    """Получить количество сожжённых калорий за сегодня"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(calories_burned), 0) 
        FROM workout_logs 
        WHERE user_id = ? AND DATE(logged_at) = ?
    ''', (user_id, today))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_today_extra_water(user_id: int) -> int:
    """Получить дополнительную норму воды от тренировок за сегодня"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(water_extra_ml), 0) 
        FROM workout_logs 
        WHERE user_id = ? AND DATE(logged_at) = ?
    ''', (user_id, today))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_workout_history(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """Получить историю тренировок за последние N дней"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(logged_at) as day, SUM(calories_burned) as total
        FROM workout_logs
        WHERE user_id = ? AND logged_at >= date('now', ?)
        GROUP BY DATE(logged_at)
        ORDER BY day
    ''', (user_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [{'date': row[0], 'calories': row[1]} for row in rows]


# Инициализация БД при импорте
init_db()


