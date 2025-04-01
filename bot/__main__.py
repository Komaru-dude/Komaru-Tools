import asyncio, logging, os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация бота
    load_dotenv()
    token = os.getenv("BOT_API_TOKEN")
    bot = Bot(token)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_routers(
        mod_router,
        rght_router,
        base_router,
        txt_router
    )
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен")