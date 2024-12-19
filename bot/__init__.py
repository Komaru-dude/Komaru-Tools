import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Переменные окружения
API_TOKEN = os.getenv('BOT_API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# Проверка обязательных переменных
if not API_TOKEN:
    raise ValueError("API_TOKEN не задан в .env файле")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не задан в .env файле")
if not ADMIN_ID.isdigit():
    raise ValueError("ADMIN_ID задан некорректно")
