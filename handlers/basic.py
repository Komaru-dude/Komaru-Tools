import db
from aiogram import types, Router
from aiogram.types import FSInputFile, Message
from aiogram.filters import Command

base_router = Router()

@base_router.message(Command("rules"))
async def cmd_rules(message: Message):
    komaru_rules_video = FSInputFile("rules.mp4")
    # Отправляем видео с правилами чата
    caption = (
        f"Привет, {message.from_user.full_name}\n"
        "Вот краткий список правил чата:\n\n"
        "Не твори хуйни\n\n"
        "Список команд:\n\n"
        "/info - Посмотреть информацию о себе\n"
        "/privetbradok - Приве брадок\n\n"
        "Ыгыгыгыг"
    )
    await message.reply_video(komaru_rules_video, caption=caption)

@base_router.message(Command('privetbradok'))
async def cmd_privebradok(message: types.Message):
    await message.reply("Приве брадок!")

@base_router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    if not db.user_exists(user_id):
        db.add_user(user_id)
    if not db.user_have_username(user_id):
        db.add_username(user_id, username)
    await message.reply(f"Гойда @{username}")
