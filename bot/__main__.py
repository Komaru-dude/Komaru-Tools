import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router

# Запуск процесса поллинга новых апдейтов
async def main():
    # Загружаем переменные из dotenv
    load_dotenv()
    # Включаем логирование
    logging.basicConfig(level=logging.INFO)
    # Токен бота
    token = os.getenv("BOT_API_TOKEN")
    # Объект бота
    bot = Bot(token, ParseMode=ParseMode.MARKDOWN_V2)
    # Диспетчер
    dp = Dispatcher()
    # Включаем роутеры
    dp.include_routers(mod_router, rght_router, base_router)
    dp.include_router(txt_router)
    # Наконец, запуск
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())