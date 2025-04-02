import os
from dotenv import load_dotenv

# Загрузка переменных из .env
if not load_dotenv():
    raise RuntimeError(".env файл не найден, создайте его прежде чем начать")

# Переменные окружения
API_TOKEN = os.getenv('BOT_API_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')

# Проверка обязательных переменных
if not API_TOKEN:
    raise ValueError("API_TOKEN не задан в .env файле")
if not OWNER_ID:
    raise ValueError("OWNER_ID не задан в .env файле")
if not OWNER_ID.isdigit():
    raise ValueError("OWNER_ID задан некорректно")
