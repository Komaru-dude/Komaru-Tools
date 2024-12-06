import asyncio, logging, os, db, secrets
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
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
    user_id = message.from_user.id
    username = message.from_user.username
    if not db.user_exists(user_id):
        db.add_user(user_id)
    if not db.user_have_username(user_id):
        db.add_username(user_id, username)
    await message.reply(f"Гойда @{username}")

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
    await message.reply(f"Информация о пользователе: {clickable_name}\nПреды/муты/баны: {user_data[2]} из {user_data[10]}/{user_data[4]}/{user_data[3]} \n\nЮзернейм: {user_data[1]}\nАйди: {user_id}\nРанг: {user_data[6]}\nКол-во сообщений: {user_data[8]}\nРепутация: {user_data[5]}\nПрефикс: {user_data[7]}", parse_mode=ParseMode.HTML)

@dp.message(Command("warn"))
async def warn_cmd(message: types.Message):
    # Проверяем, есть ли у пользователя разрешение на "блокировку пользователей"
    user_id = message.from_user.id
    if not db.has_permission(user_id):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    # Проверяем, ответил ли пользователь на сообщение
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        reason = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else "Без причины"
        if not db.user_exists(target_user_id):
            db.add_user(target_user_id)
        db.update_user_warns(target_user_id, reason)
        await message.reply(f"Пользователь с ID {target_user_id} был предупреждён. Причина: {reason}")
    else:
        # Разделяем команду и аргументы
        parts = message.text.split(' ', 2)
        
        # Проверяем, правильно ли введены аргументы
        if len(parts) > 1:
            user_input = parts[1]  # Введён юзернейм или ID
            reason = parts[2] if len(parts) > 2 else "Без причины"
            
            if user_input.startswith('@'):  # Если введён юзернейм
                username = user_input[1:]  # Убираем "@" в начале
                # Получаем user_id из базы данных по юзернейму
                target_user_id = db.get_user_id_by_username(username)
                if target_user_id:
                    if not db.user_exists(target_user_id):
                        db.add_user(target_user_id)
                    db.update_user_warns(target_user_id, reason)
                    await message.reply(f"Пользователь с ID {target_user_id} был предупреждён. Причина: {reason}")
                else:
                    await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
            elif user_input.isdigit():  # Если введён ID
                target_user_id = int(user_input)
                try:
                    if not db.user_exists(target_user_id):
                        db.add_user(target_user_id)
                    db.update_user_warns(target_user_id, reason)
                    await message.reply(f"Пользователь с ID {target_user_id} был предупреждён. Причина: {reason}")
                except Exception as e:
                    await message.reply(f"Не удалось найти пользователя с ID {target_user_id}. Ошибка: {str(e)}")
            else:
                await message.reply("Некорректный формат. Используйте /warn @username или /warn ID причина.")
        else:
            await message.reply("Синтаксис команды некорректный. Используйте /warn @username причина или /warn ID причина.")

@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    user_id = message.from_user.id

    # Проверка прав пользователя
    if not db.has_permission(user_id):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Проверка пользователя в базе данных
    if not db.user_exists(target_user_id):
        db.add_user(target_user_id)

    def parse_time(time_str):
        """Парсит время из строки формата 3h, 3m, 3d"""
        try:
            unit = time_str[-1]
            amount = int(time_str[:-1])
            if unit == 'h':
                return timedelta(hours=amount)
            elif unit == 'm':
                return timedelta(minutes=amount)
            elif unit == 'd':
                return timedelta(days=amount)
            else:
                return None
        except (ValueError, IndexError):
            return None

    # Разбиваем текст команды
    parts = message.text.split(' ', 3)

    # Проверка на наличие времени
    if len(parts) < 2 or not parse_time(parts[1]):
        await message.reply("Ошибка: необходимо указать время. Используйте формат 3h, 3m или 3d.")
        return

    time_str = parts[1]
    mute_duration = parse_time(time_str)
    until_date = datetime.now() + mute_duration

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        reason = parts[2] if len(parts) > 2 else "Без причины"

    else:
        if len(parts) < 3:
            await message.reply("Ошибка: необходимо указать username или ID после времени.")
            return

        user_input = parts[2]
        reason = parts[3] if len(parts) > 3 else "Без причины"

        # Если указан username
        if user_input.startswith('@'):
            username = user_input[1:]
            target_user_id = db.get_user_id_by_username(username)
            if not target_user_id:
                await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
                return
        elif user_input.isdigit():
            target_user_id = int(user_input)
        else:
            await message.reply("Некорректный формат. Используйте /mute <время> @username/ID причина.")
            return

    # Применение мута
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            target_user_id,
            types.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        db.update_user_mutes(target_user_id, reason)
        await message.reply(f"Пользователь с ID {target_user_id} был замьючен на {time_str}. Причина: {reason}")
    except:
        await message.reply(f"Не удалось замьютить пользователя.")

@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    user_id = message.from_user.id

    # Проверка прав пользователя
    if not db.has_permission(user_id):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Разбиваем текст команды
    parts = message.text.split(' ', 3)

    # Парсинг времени
    def parse_time(time_str):
        """Парсит время из строки формата 3h, 3m, 3d"""
        try:
            unit = time_str[-1]
            amount = int(time_str[:-1])
            if unit == 'h':
                return timedelta(hours=amount)
            elif unit == 'm':
                return timedelta(minutes=amount)
            elif unit == 'd':
                return timedelta(days=amount)
            else:
                return None
        except (ValueError, IndexError):
            return None

    # Проверка времени
    if len(parts) > 1:
        time_str = parts[1]
        ban_duration = parse_time(time_str)
        if ban_duration:
            until_date = datetime.now() + ban_duration
        else:
            await message.reply("Ошибка: неверный формат времени. Используйте 3h, 3m или 3d.")
            return
    else:
        # Если время не указано — бан навсегда
        until_date = None

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        reason = parts[2] if len(parts) > 2 else "Без причины"
    else:
        if len(parts) < 2:
            await message.reply("Ошибка: необходимо указать username, ID или ответить на сообщение цели.")
            return

        user_input = parts[1]
        reason = parts[2] if len(parts) > 2 else "Без причины"

        # Если указан username
        if user_input.startswith('@'):
            username = user_input[1:]
            target_user_id = db.get_user_id_by_username(username)
            if not target_user_id:
                await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
                return
        elif user_input.isdigit():
            target_user_id = int(user_input)
        else:
            await message.reply("Некорректный формат. Используйте /ban <время> @username/ID причина.")
            return

    # Применение бана
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user_id, until_date=until_date)
        db.update_user_bans(target_user_id, reason)
        if until_date:
            duration = f"на {ban_duration.total_seconds() // 60} минут"
        else:
            duration = "навсегда"
        await message.reply(f"Пользователь с ID {target_user_id} был забанен {duration}. Причина: {reason}")
    except Exception as e:
        await message.reply(f"Не удалось забанить пользователя. Ошибка: {e}")

@dp.message(F.new_chat_members)
async def somebody_added(message: types.Message):
    for user in message.new_chat_members:
        chat_name = message.chat.title
        user_id = user.id
        if not db.user_exists(user_id):
            db.add_user(user_id)
        xiao_hello_image = FSInputFile("xiao.jpg")
        await message.reply_photo(
            xiao_hello_image,
            caption=f"Гойда {user.full_name}, добро пожаловать в {chat_name}.\n\nПеред тем как начать общение ТАПКИ БЛЯ, чтобы не получить пизды от Сьпрей.\n\nНе забудьте установить зондбэ камчан командой /privetbradok для удобного бла бла бла с брадками.\n\nПриятного качанения в нашем кочон подвале 😘"
        )

# Состояния /setrank
class SetRankState(StatesGroup):
    waiting_for_token = State()
    waiting_for_user_id = State()
    waiting_for_rank = State()

TOKENS = {}

@dp.message(Command('setrank'))
async def cmd_setrank(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        db.add_user(user_id)
    chat_type = message.chat.type

    if chat_type != "private":
        await message.reply("В целях безопасности данную команду разрешено выполнять только в личных сообщениях.")
        return

    # Генерация токена
    lenght = 8
    token = secrets.token_hex(lenght)
    TOKENS[user_id] = token

    print(f"Токен для смены ранга: {token}, запросил {user_id}")
    await message.answer("Введите токен из командной строки для продолжения.")
    await state.set_state(SetRankState.waiting_for_token)

@dp.message(SetRankState.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    token = message.text

    # Проверка токена
    if TOKENS.get(user_id) != token:
        await message.answer("Неверный токен. Попробуйте снова.")
        return

    await message.answer("Токен принят. Введите ID пользователя.")
    await state.set_state(SetRankState.waiting_for_user_id)

@dp.message(SetRankState.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)  # Проверка, что это число
        await state.update_data(user_id=user_id)
        await message.answer("Введите новый ранг для пользователя.")
        await state.set_state(SetRankState.waiting_for_rank)
    except ValueError:
        await message.answer("Некорректный ID. Введите числовой ID.")

@dp.message(SetRankState.waiting_for_rank)
async def process_rank(message: types.Message, state: FSMContext):
    rank = message.text

    # Получение данных из FSM
    data = await state.get_data()
    user_id = data.get("user_id")

    # Здесь нужно выполнить логику смены ранга
    print(f"Смена ранга: Пользователь {user_id} получает ранг '{rank}'.")
    db.set_rank(user_id, rank)
    await message.answer(f"Ранг '{rank}' успешно установлен для пользователя с ID {user_id}.")
    await state.clear()

@dp.message(Command('privetbradok'))
async def cmd_privebradok(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    if not db.user_exists(user_id):
        db.add_user(user_id)
    if not db.user_have_username(user_id):
        db.add_username(user_id, username)
    await message.reply("Приве брадок!")

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        db.add_user(user_id)
    history = db.get_history(user_id)
    
    if not history:  # Если истории нет
        await message.reply("У вас пока нет наказаний.")
        return
    
    # Формируем текст ответа
    history_text = ""
    for i, entry in enumerate(history, start=1):
        punishment_type = entry["type"]
        reason = entry.get("reason", "Без причины")
        history_text += f"{i}. {punishment_type.capitalize()} - Причина: {reason}.\n"
    
    warns_count = len(history)
    response = (
        f"Всего наказаний: {warns_count}\n"
        f"История наказаний:\n{history_text}"
    )
    await message.reply(response)

@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    user = message.from_user
    user_id = user.id
    if not db.user_exists(user_id):
        db.add_user(user_id)
    komaru_rules_video = FSInputFile("rules.mp4")
    await message.reply_video(
        komaru_rules_video,
        caption=f"Привет {user.full_name}\nВот краткий список правил чата:\n\nНе твори хуйни\n\nСписок команд:\n\n/info - Посмотреть информацию о себе\n/privetbradok - Приве брадок\n\nЫгыгыгыг"
    )

@dp.message(F.text)
async def message_handler(message: types.Message): 
    user_id = message.from_user.id
    text = message.text
    username = message.from_user.username
    if not db.user_exists(user_id):
        db.add_user(user_id)
    if not db.user_have_username(user_id):
        db.add_username(user_id, username)
    db.update_count_messges(user_id)
    mute_user = check_ban_words(text)
    if mute_user:
        print(f"Найдено запрещённое слово в сообщении пользователя {user_id}")
        duration = 7200
        new_time = datetime.now() + timedelta(seconds=duration)
        timestamp = new_time.timestamp()
        try:
            if not db.user_exists(user_id):
                db.add_user(user_id)
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