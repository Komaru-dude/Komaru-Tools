import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from .handlers.moderations import mod_router
from .handlers.rights import rght_router
from .handlers.basic import base_router
from .handlers.text import txt_router
from . import API_TOKEN

# Функция отправки сообщения после перезапуска
async def send_restart_message(bot: Bot):
    chat_id = os.getenv("RESTART_CHAT_ID")
    
    if chat_id and chat_id.isdigit():
        await bot.send_message(chat_id, "✅ Бот успешно перезапущен!")
        
        # Удаляем RESTART_CHAT_ID из .env
        with open(".env", "r") as f:
            lines = f.readlines()
        
        with open(".env", "w") as f:
            for line in lines:
                if not line.startswith("RESTART_CHAT_ID"):
                    f.write(line)

# Запуск процесса поллинга новых апдейтов
async def main():
    # Включаем логирование
    logging.basicConfig(level=logging.INFO)
    # Токен бота
    token = API_TOKEN
    # Объект бота
    bot = Bot(token, ParseMode=ParseMode.MARKDOWN_V2)
    # Диспетчер
    dp = Dispatcher()
    # Регистрируем хэндлеры
    dp.include_routers(mod_router,
                       rght_router,
                       base_router,
                       txt_router
    )
    # Отправляем сообщение о перезапуске
    await send_restart_message(bot)
    # Наконец, запуск
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())