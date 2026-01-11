import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# OpenWeatherMap API Key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Используем /tmp для бесплатного плана Render
DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/bot_database.db")

# Проверка наличия обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Добавьте его в .env файл")

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY не установлен! Добавьте его в .env файл")
