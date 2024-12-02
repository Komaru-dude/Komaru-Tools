import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
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
    last_name = f" {user.last_name}" if user.last_name else ""
    user_id = user.id
    user_name = first_name + last_name
    
    # Ссылка на профиль по ID
    profile_link = f"https://t.me/{user_id}"

    # Формируем кликабельное имя пользователя
    clickable_name = f"<a href='{profile_link}'>{user_name}</a>"
    
    # Отправляем сообщение с кликабельным именем и ссылкой на профиль по ID
    await message.reply(f"Информация о пользователе {clickable_name}", parse_mode=ParseMode.HTML)

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())