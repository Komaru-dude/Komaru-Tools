import re, os, random
from aiogram import types, F, Router, Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta
from bot import db
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
txt_router = Router()
OWNER_ID = os.getenv("OWNER_ID")

@txt_router.message(F.new_chat_members)
async def somebody_added(message: types.Message):
    for user in message.new_chat_members:
        chat_name = message.chat.title
        user_id = user.id
        username = user.username
        first_name = user.first_name
        if not db.user_exists(user_id):
            db.add_user(user_id)
        if not db.user_have_username(user_id):
            db.add_username(user_id, username)
        if not username == db.get_username(user_id):
            db.add_username(user_id, username) 
        if not db.get_first_name_by_id(user_id):
            db.add_first_name(user_id=user_id, first_name=first_name)
        xiao_file_name = Path(__file__).resolve().parent.parent / 'media' / 'xiao.jpg'
        xiao_hello_image = FSInputFile(xiao_file_name)
        await message.reply_photo(
            xiao_hello_image,
            caption=f"Гойда {user.full_name}, добро пожаловать в {chat_name}.\n\n"
            "Перед тем как начать общение прочитай правила (/rules), чтобы не получить пизды от Кончона.\n\n"
            "Не забудьте установить зондбэ камчан командой /privetbradok для удобного бла бла бла с брадками.\n\n"
            "Приятного качанения в нашем кочон подвале 😘"
        )

@txt_router.message(F.text)
async def message_handler(message: types.Message, bot: Bot): 
    user_id = message.from_user.id
    text = message.text
    first_name = message.from_user.first_name
    if message.chat.type == "private":
        return
    if message.chat.type == "channel":
        return
    if not db.user_exists(user_id):
        db.add_user(user_id)
    if not db.get_first_name_by_id(user_id):
        db.add_first_name(user_id=user_id, first_name=first_name)
    db.update_count_messges(user_id)
    mute_user = check_ban_words(text)
    if mute_user:
        await bot.send_message(chat_id=OWNER_ID, text=f"Найдено запрещённое слово в сообщении пользователя {user_id}")
        new_time = datetime.now() + timedelta(hours=2)
        timestamp = new_time.timestamp()
        try:
            if not db.user_exists(user_id):
                db.add_user(user_id)
            await message.reply(f"Пользователь {user_id} ограничен за использование запрещённых слов.")
            await message.delete()
            await bot.restrict_chat_member(message.chat.id, user_id, types.ChatPermissions(can_send_messages=False), until_date=timestamp)
            db.update_user_mutes(user_id=user_id, reason="Использование запрещённых слов")
        except TelegramBadRequest as e:
            message.reply(f"Не удалось ограничить пользователя из-за ошибки телеграмма: {e}")
        except:
            message.reply("Не удалось ограничить пользователя.")
    else:
        raw_data = db.get_user_data(user_id)
        message_count = raw_data[8]
        old_need_msg = raw_data[13]
        if old_need_msg <= message_count:
            new_need_msg = message_count + random.randint(4, 15)
            db.update_need_msg(user_id, new_need_msg)
            db.update_rep(user_id, mode="auto_add")

def check_ban_words(text: str):
    mute_user = False
    ban_words_file = Path(__file__).resolve().parent.parent / 'media' / 'ban_words.txt'

    # Читаем список бан-слов из файла
    with open(ban_words_file, 'r', encoding='utf-8') as f:
        ban_words = f.read().splitlines()  # Читаем строки и убираем символы новой строки

    # Разбиваем текст на слова с использованием регулярных выражений
    words_in_text = re.findall(r'\b\w+\b', text.lower())  # \b обозначает границы слов

    # Проверяем наличие бан-слов среди слов в тексте
    for word in ban_words:
        if word.lower() in words_in_text:
            mute_user = True
            break  # Если хотя бы одно слово найдено, выходим из цикла

    return mute_user