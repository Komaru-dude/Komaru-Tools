import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from db import get_user_data, update_user_id
from dotenv import load_dotenv
import os

# Загружаем переменные из dotenv
load_dotenv()

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Токен бота
token = os.getenv("BOT_API_TOKEN")
# Объект бота
bot = Bot(token, ParseMode=ParseMode.MARKDOWN_V2)
# Диспетчер
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("iдi нахуй")

@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    # Достаём информацию о пользователе
    user = message.from_user
    first_name = user.first_name
    user_id = user.id
    
    # Ссылка на профиль по ID
    profile_link = f"https://t.me/{user_id}"

    # Формируем кликабельное имя пользователя
    clickable_name = f"<a href='{profile_link}'>{first_name}</a>"

    # Получаем данные из db
    user_data = get_user_data(user_id)
    if not user_id == user_data[0]:
        update_user_id(user_data[0], user_id)
    
    # Отправляем сообщение с кликабельным именем и ссылкой на профиль по ID
    await message.reply(f"Информация о пользователе {clickable_name}\nПреды/муты/баны: {user_data[1]}/{user_data[2]}/{user_data[3]} \n\nАйди: {user_id}", parse_mode=ParseMode.HTML)

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())