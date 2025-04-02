import asyncio
import logging
import os
import subprocess
import sys
import signal
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router

load_dotenv()

token = os.getenv("BOT_API_TOKEN")
bot = Bot(token)
dp = Dispatcher()

# Подключаем роутеры
dp.include_routers(
    mod_router,
    rght_router,
    base_router,
    txt_router
)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    pyrogram_process = subprocess.Popen(["uvicorn", "bot.utils.pyro_tools:server", "--host", "127.0.0.1", "--port", "8000"])

    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()
        pyrogram_process.send_signal(signal.SIGTERM)  # Отправляем сигнал для остановки Pyrogram-бота
        pyrogram_process.wait()  # Ждём завершения процесса Pyrogram

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")