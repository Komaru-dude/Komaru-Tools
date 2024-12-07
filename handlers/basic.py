import db, time, psutil
from aiogram import types, Router
from aiogram.types import FSInputFile, Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

base_router = Router()
# Списки для хранения данных для /status
cpu_loads = []
memory_loads = []
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

    # Получаем текущую загрузку процессора и памяти
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent

    # Добавляем данные в списки
    cpu_loads.append(cpu_percent)
    memory_loads.append(memory_percent)

    # Убираем старые данные (если прошло больше 5 минут)
    global start_time
    if time() - start_time > 300:  # 5 минут = 300 секунд
        cpu_loads.pop(0)
        memory_loads.pop(0)
        start_time = time()  # сбрасываем таймер

    # Вычисляем среднее значение за последние 5 минут
    avg_cpu_load = sum(cpu_loads) / len(cpu_loads) if cpu_loads else 0
    avg_memory_load = sum(memory_loads) / len(memory_loads) if memory_loads else 0

    # Форматируем аптайм
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"
    await sent_message.edit_text(f"Пинг: {int(ping)} мс\n"
                                 f"Бот работает: {uptime_str}\n"
                                 f"Средняя загруженность ЦПУ (5м): {avg_cpu_load:2f}%\n"
                                 f"Средняя загруженность ОЗУ (5м): {avg_memory_load:2f}%")

@base_router.message(Command("info"))
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
    
    # Формируем текст с информацией о пользователе
    user_info = (
        f"Информация о пользователе: {clickable_name}\n"
        f"Преды/муты/баны: {user_data[2]} из {user_data[10]}/{user_data[4]}/{user_data[3]}\n"
        f"Юзернейм: {user_data[1]}\n"
        f"Айди: {user_id}\n"
        f"Ранг: {user_data[6]}\n"
        f"Кол-во сообщений: {user_data[8]}\n"
        f"Репутация: {user_data[5]}\n"
        f"Демотиваторы: {user_data[9]}"
        f"Префикс: {user_data[7]}"
    )

    # Отправляем сообщение с информацией
    await message.reply(user_info, parse_mode=ParseMode.HTML)