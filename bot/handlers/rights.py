from aiogram import types, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import secrets
from bot import db
import os
from dotenv import load_dotenv

load_dotenv()
rght_router = Router()
ADMIN_ID = os.getenv("ADMIN_ID")

@rght_router.message(Command('cancel'))
async def cmd_cancel(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.clear()
        await message.reply("Действие отменено.")
    else:
        await message.reply("Нет активного действия для отмены.")

# Состояния /setrank
class SetRankState(StatesGroup):
    waiting_for_token = State()
    waiting_for_rank = State()

TOKENS = {}

@rght_router.message(Command('setrank'))
async def cmd_setrank(message: types.Message, state: FSMContext, bot: Bot):
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

    await bot.send_message(chat_id=ADMIN_ID, text=f"Токен для смены ранга: {token}, запросил {user_id}")
    await message.answer("Введите токен для продолжения.")
    await state.set_state(SetRankState.waiting_for_token)

@rght_router.message(SetRankState.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    token = message.text

    # Проверка токена
    if TOKENS.get(user_id) != token:
        await message.answer("Неверный токен. Попробуйте снова.")
        return

    await message.answer("Токен принят. Введите ID пользователя.")
    await state.set_state(SetRankState.waiting_for_rank)

@rght_router.message(SetRankState.waiting_for_rank)
async def process_rank(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)  # Проверка, что это число
        await state.update_data(user_id=user_id)
    except ValueError:
        await message.answer("Некорректный ID. Введите числовой ID.")
    # Список доступных рангов
    ranks = ["Владелец", "Администратор", "Модератор", "Участник", "Замьючен", "Заблокирован"]
    
    # Создание кнопок для каждого ранга
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=rank, callback_data=rank) for rank in ranks]
    ])
    await message.answer("Выберите новый ранг для пользователя:", reply_markup=keyboard)
    await state.set_state(SetRankState.waiting_for_rank)  # Ожидаем выбор пользователя

@rght_router.callback_query(SetRankState.waiting_for_rank)
async def handle_rank_choice(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    rank = callback_query.data  # Получаем выбранный ранг

    # Получаем данные из FSM
    data = await state.get_data()
    user_id = data.get("user_id")

    # Логика смены ранга
    await bot.send_message(ADMIN_ID, text=f"Смена ранга: Пользователь {user_id} получает ранг '{rank}'.")
    db.set_rank(user_id, rank)
    
    # Отправляем подтверждение
    await callback_query.answer(f"Ранг '{rank}' успешно установлен для пользователя с ID {user_id}.")
    await state.clear()

@rght_router.message(Command('setprefix'))
async def cmd_setprefix(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    # Проверка прав пользователя
    if not db.has_permission(user_id, 3):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Проверка прав бота
    bot_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
    if not bot_member.can_promote_members:
        await message.reply("У бота нет прав для назначения администраторов. Добавьте соответствующие права.")
        return
    if bot_member.status != "administrator":
        await message.reply("Бот не является администратором чата.")
        return

    # Разбиваем текст команды
    parts = message.text.split(' ', 2)  # Делаем split на максимум 3 части: /setprefix <target> <prefix>

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        if len(parts) < 2:
            await message.reply("Ошибка: необходимо указать префикс для установки.")
            return
        prefix = parts[1]
    else:
        if len(parts) < 3:
            await message.reply("Ошибка: необходимо указать цель и префикс. Формат: /setprefix <target> <prefix>")
            return

        user_input = parts[1]
        prefix = parts[2]  # Префикс берется как последний аргумент

        if user_input.startswith('@'): # Если указан username
            username = user_input[1:]
            target_user_id = db.get_user_id_by_username(username)
            if not target_user_id:
                await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
                return
        elif user_input.isdigit(): # Если указан ID
            target_user_id = int(user_input)
        else:
            await message.reply("Некорректный формат. Используйте /setprefix <target> <prefix>.")
            return

    # Логика установки префикса
    try:
        await bot.promote_chat_member(message.chat.id, target_user_id)
        await bot.set_chat_administrator_custom_title(chat_id=message.chat.id, user_id=target_user_id, custom_title=prefix)
        db.set_prefix(target_user_id, prefix)
        await message.reply(f"Префикс '{prefix}' успешно установлен для пользователя ID: {target_user_id}.")
    except Exception as e:
        await message.reply(f"Ошибка при установке префикса: {e}")

@rght_router.message(Command("setdb"))
async def cmd_setdb(message: types.Message):
    user_id = message.from_user.id
    if not db.has_permission(user_id, 4):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    # Разбиваем текст команды
    parts = message.text.split(' ', 3)

    if len(parts) < 4:
        await message.reply("Необходимо указать ID, параметр, значение.\nФормат: /setdb <ID> <parameter> <value>")
        return
    
    user_input = parts[1]
    param = parts[2]
    value = parts[3]

    # Обрабатываем целевой ID или username
    if user_input.startswith('@'):  # Если указан username
        username = user_input[1:]
        target_user_id = db.get_user_id_by_username(username)
        if not target_user_id:
            await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
            return
    elif user_input.isdigit():  # Если указан ID
        target_user_id = int(user_input)
    else:
        await message.reply("Некорректный формат. Используйте /setdb <ID> <parameter> <value>.")
        return
    
    # Логика изменения значения
    try:
        db.set_param(user_id=target_user_id, param=param, value=value)
        await message.reply(f"Параметр '{param}' установлен на '{value}' для пользователя с ID {target_user_id}.")
    except Exception as e:
        await message.reply(f"Ошибка при установке параметра: {e}")