import asyncio
import logging
import os
import subprocess
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
from dotenv import load_dotenv
from pathlib import Path
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router

load_dotenv()

API_TOKEN = os.getenv('BOT_API_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')

if not API_TOKEN:
    raise ValueError("API_TOKEN не задан в .env файле")
if not OWNER_ID:
    raise ValueError("OWNER_ID не задан в .env файле")
if not OWNER_ID.isdigit():
    raise ValueError("OWNER_ID задан некорректно")

bot = Bot(API_TOKEN)
dp = Dispatcher()

dp.include_routers(
    mod_router,
    rght_router,
    base_router,
    txt_router
)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    uvicorn_exec = Path(sys.prefix) / 'Scripts' / 'uvicorn.exe' if sys.platform == 'win32' else Path(sys.prefix) / 'bin' / 'uvicorn'
    pyrogram_process = subprocess.Popen(
        [uvicorn_exec, "bot.utils.pyro_tools:server", "--host", "127.0.0.1", "--port", "8001"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )

    try:
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        if pyrogram_process.poll() is None:
            if sys.platform == 'win32':
                pyrogram_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                pyrogram_process.send_signal(signal.SIGTERM)
            try:
                pyrogram_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pyrogram_process.kill()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")