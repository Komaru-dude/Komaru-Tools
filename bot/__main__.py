import asyncio, logging, os, threading
from aiogram import Bot, Dispatcher
from pyrogram import Client
from dotenv import load_dotenv
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router

load_dotenv()
token = os.getenv("BOT_API_TOKEN")

async def aio_main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_routers(mod_router, rght_router, base_router, txt_router)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()

def run_aio():
    asyncio.run(aio_main())

async def pyro_main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    if not os.path.exists("my_bot.session"):
        app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=token)
    else:
        app = Client("my_bot")
    await app.start()
    await asyncio.Event().wait()
    await app.stop()

async def main():
    aio_thread = threading.Thread(target=run_aio, daemon=True)
    aio_thread.start()
    await pyro_main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")