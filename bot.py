import asyncio, logging, os, db, secrets
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
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
    await message.reply("iдi нахуй")

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
    # Проверяем, есть ли у пользователя разрешение на "блокировку пользователей"
    user_id = message.from_user.id
    if not db.has_permission(user_id):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    # Проверяем, ответил ли пользователь на сообщение
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else "Без причины"
        db.update_user_warns(user_id, reason)
        await message.reply(f"Пользователь с ID {user_id} был предупреждён. Причина {reason}")
    else:
        # Разделяем команду и аргументы
        parts = message.text.split(' ', 2)
        
        # Проверяем, правильно ли введены аргументы
        if len(parts) > 1:
            user_id = parts[1]  # ID пользователя
            reason = parts[2] if len(parts) > 2 else "Без причины"
            
            if user_id.isdigit():
                user_id = int(user_id)
                try:
                    # Обновляем количество предупреждений
                    db.update_user_warns(user_id, reason)
                    await message.reply(f"Пользователь с ID {user_id} был предупрежден. Причина: {reason}")
                except Exception as e:
                    await message.reply(f"Не удалось найти пользователя с ID {user_id}. Ошибка: {str(e)}")
            else:
                await message.reply("Некорректный формат ID пользователя. Используйте ID пользователя.")
        else:
            await message.reply("Синтаксис команды некорректный. Используйте /warn ID причина или ответьте на сообщение пользователя с /warn причина.")

@dp.message(F.new_chat_members)
async def somebody_added(message: types.Message):
    for user in message.new_chat_members:
        chat_name = message.chat.title
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
    db.set_rank(rank)
    await message.answer(f"Ранг '{rank}' успешно установлен для пользователя с ID {user_id}.")
    await state.clear()

@dp.message(Command('privetbradok'))
async def cmd_privebradok(message: types.Message):
    await message.reply("Приве брадок!")

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = db.get_history(user_id)
    
    if not history:  # Если истории нет
        await message.reply("У вас пока нет наказаний.")
        return
    
    # Формируем текст ответа
    history_text = ""
    for i, entry in enumerate(history, start=1):
        punishment_type = entry["type"]
        reason = entry.get("reason", "Без причины")
        
        # Если это мут или бан, добавляем информацию о времени действия
        if punishment_type in ["mute", "ban"]:
            end_time = entry.get("end_time", None)
            if end_time:
                end_time_str = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
                history_text += f"{i}. {punishment_type.capitalize()} - Причина: {reason}, Время окончания: {end_time_str}\n"
            else:
                history_text += f"{i}. {punishment_type.capitalize()} - Причина: {reason}, Время действия не указано\n"
        else:
            history_text += f"{i}. {punishment_type.capitalize()} - Причина: {reason}\n"
    
    warns_count = len(history)
    response = (
        f"Всего наказаний: {warns_count}\n"
        f"История наказаний:\n{history_text}"
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