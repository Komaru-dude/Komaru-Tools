import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from dotenv import load_dotenv
import os

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Токен бота
pre_token = os.getenv('BOT_API_TOKEN')
token = str(pre_token)
# Объект бота
bot = Bot(token)
# Диспетчер
dp = Dispatcher()
# Загружаем переменные из dotenv
load_dotenv()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("iдi нахуй")

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())