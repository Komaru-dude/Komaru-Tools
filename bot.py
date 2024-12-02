import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from db import get_user_data, update_user_id, update_user_warns
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
    await message.reply(f"Информация о пользователе: {clickable_name}\nПреды/муты/баны: {user_data[1]} из {user_data[9]}/{user_data[2]}/{user_data[3]} \n\nАйди: {user_id}\nКол-во сообщений: {user_data[7]}\nРепутация: {user_data[4]}\nПрефикс: {user_data[6]}", parse_mode=ParseMode.HTML)

# Обработчик команды /warn
@dp.message(Command("warn"))
async def warn_cmd(message: types.Message):
    # Разделяем команду и аргументы
    parts = message.text.split(' ', 2)
    
    # Проверяем, правильно ли введены аргументы
    if len(parts) > 1:
        mention_or_id = parts[1]  # @username или ID пользователя
        reason = parts[2] if len(parts) > 2 else "Без причины"
        
        # Если упоминание в формате @username
        if mention_or_id.startswith('@'):
            username = mention_or_id[1:]  # Убираем '@' для получения только имени пользователя
            
            try:
                # Получаем ID пользователя по юзернейму
                user = await bot.get_chat_member(message.chat.id, username)
                user_id = user.user.id  # Получаем ID пользователя
                # Обновляем количество предупреждений
                update_user_warns(user_id)
                await message.reply(f"Пользователь {username} был предупрежден. Причина: {reason}")
            except Exception as e:
                await message.reply("Не удалось найти пользователя по данному имени.")
                logging.error(f"Ошибка при поиске пользователя: {e}")
        
        # Если введен ID пользователя
        elif mention_or_id.isdigit():
            user_id = int(mention_or_id)
            # Обновляем количество предупреждений
            update_user_warns(user_id)
            await message.reply(f"Пользователь с ID {user_id} был предупрежден. Причина: {reason}")
        
        else:
            await message.reply("Некорректный формат ввода. Используйте @username или ID пользователя.")
    else:
        await message.reply("Синтаксис команды некорректный. При ошибке сообщите разработчику.")

@dp.message(F.new_chat_members)
async def somebody_added(message: types.Message):
    for user in message.new_chat_members:
        xiao_hello_image = FSInputFile("xiao.jpg")
        await message.reply_photo(
            xiao_hello_image,
            caption=f"Гойда {user.full_name}, добро пожаловать в кочон подвал.\n\nПеред тем как начать общение ТАПКИ БЛЯ, чтобы не получить пизды от Сьпрей.\n\nНе забудьте установить зондбэ камчан командой /privetbradok для удобного бла бла бла с брадками.\n\nПриятного качанения в нашем кочон подвале 😘"
        )

@dp.message(Command('privetbradok'))
async def cmd_privebradok(message: types.Message):
    await message.reply("Приве брадок!")

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())