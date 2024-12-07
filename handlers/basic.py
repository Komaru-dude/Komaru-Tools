import db, time
from aiogram import types, Router
from aiogram.types import FSInputFile, Message
from aiogram.filters import Command

base_router = Router()
start_time = time.time()

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

@base_router.message(Command("status"))
async def cmd_status(message: types.Message):
    ping_start_time = time.monotonic()
    sent_message = await message.reply("⏳")
    end_time = time.monotonic()
    ping = (end_time - ping_start_time) * 1000  # В миллисекундах
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    # Форматируем аптайм
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"
    await sent_message.edit_text(f"Пинг: {int(ping)} мс\nБот работает: {uptime_str}")