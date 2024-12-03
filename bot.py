import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
import db
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

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
    profile_link = f"tg://user?id={user_id}"

    # Формируем кликабельное имя пользователя
    clickable_name = f"<a href='{profile_link}'>{first_name}</a>"

    # Получаем данные из db
    user_data = db.get_user_data(user_id)
    if not user_id == user_data[0]:
        db.update_user_id(user_data[0], user_id)
    
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
                # Получаем информацию о пользователе по юзернейму
                user = await bot.get_chat_member(message.chat.id, username)
                user_id = user.user.id  # Получаем ID пользователя
                # Обновляем количество предупреждений
                db.update_user_warns(user_id, reason)
                await message.reply(f"Пользователь @{username} был предупрежден. Причина: {reason}")
            except Exception as e:
                await message.reply(f"Не удалось найти пользователя @{username}. Ошибка: {str(e)}")
                logging.error(f"Ошибка при поиске пользователя: {e}")
        
        # Если введен ID пользователя
        elif mention_or_id.isdigit():
            user_id = int(mention_or_id)
            try:
                # Обновляем количество предупреждений
                db.update_user_warns(user_id, reason)
                await message.reply(f"Пользователь с ID {user_id} был предупрежден. Причина: {reason}")
            except Exception as e:
                await message.reply(f"Не удалось найти пользователя с ID {user_id}. Ошибка: {str(e)}")
        
        else:
            await message.reply("Некорректный формат ввода. Используйте @username или ID пользователя.")
    else:
        await message.reply("Синтаксис команды некорректный. Используйте /warn @username или /warn ID.")

@dp.message(F.new_chat_members)
async def somebody_added(message: types.Message):
    for user in message.new_chat_members:
        chat_name = message.chat.title
        xiao_hello_image = FSInputFile("xiao.jpg")
        await message.reply_photo(
            xiao_hello_image,
            caption=f"Гойда {user.full_name}, добро пожаловать в {chat_name}.\n\nПеред тем как начать общение ТАПКИ БЛЯ, чтобы не получить пизды от Сьпрей.\n\nНе забудьте установить зондбэ камчан командой /privetbradok для удобного бла бла бла с брадками.\n\nПриятного качанения в нашем кочон подвале 😘"
        )

@dp.message(Command('privetbradok'))
async def cmd_privebradok(message: types.Message):
    await message.reply("Приве брадок!")

@dp.message(Command("warns"))
async def cmd_warn_history(message: types.Message):
    print("Начало")
    user_id = message.from_user.id
    print("Вытаскиваем историю")
    history = db.get_warns_history(user_id)
    print("Если истории нет")
    if not history:  # Если истории нет
        await message.reply("У вас пока нет предупреждений.")
        return
    print("Формируем ответ")
    # Формируем текст ответа
    warns_count = len(history)
    history_text = "\n".join([f"{i + 1}. {reason}" for i, reason in enumerate(history)])
    response = (
        f"Всего предупреждений: {warns_count}\n"
        f"История:\n{history_text}"
    )
    print(response)
    await message.reply(response)

@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    user = message.from_user
    komaru_rules_video = FSInputFile("rules.mp4")
    await message.reply_video(
        komaru_rules_video,
        caption=f"Привет {user.full_name}\nВот краткий список правил чата:\n\nНе твори хуйни\n\nСписок команд:\n\n/info - Посмотреть информацию о себе\n/privetbradok - Приве брадок\n\nЫгыгыгыг"
    )



@dp.message(F.text)
async def message_handler(message: types.Message): 
    user_id = message.from_user.id
    text = message.text
    db.update_count_messges(user_id)
    mute_user = check_ban_words(text)
    if mute_user:
        print(f"Найдено запрещённое слово в сообщении пользователя {user_id}")
        duration = 7200
        new_time = datetime.now() + timedelta(seconds=duration)
        timestamp = new_time.timestamp()
        try:
            await bot.restrict_chat_member(message.chat.id, user_id, types.ChatPermissions(can_send_messages=False), until_date=timestamp)
            await message.reply(f"Пользователь {user_id} ограничен за использование запрещённых слов.")
        except:
            message.reply("Не удалось ограничить пользователя, сообщите разработчику")

def check_ban_words(text: str):
    mute_user = False
    ban_words_file = "ban_words.txt"

    # Читаем список бан-слов из файла
    with open(ban_words_file, 'r', encoding='utf-8') as f:
        ban_words = f.read().splitlines()  # Читаем строки и убираем символы новой строки

    # Проверяем, есть ли бан-слова в тексте
    for word in ban_words:
        if word.lower() in text.lower():  # Сравниваем без учета регистра
            mute_user = True
            break  # Если хотя бы одно слово найдено, выходим из цикла

    return mute_user

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())