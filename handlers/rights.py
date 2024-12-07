from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import db, secrets

rght_router = Router()

@rght_router.message(Command('cancel'))
async def cmd_cancel(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.clear()
        await message.reply("Действие отменено. Состояние сброшено.")
    else:
        await message.reply("Нет активного действия для отмены.")

# Состояния /setrank
class SetRankState(StatesGroup):
    waiting_for_token = State()
    waiting_for_rank = State()

TOKENS = {}

@rght_router.message(Command('setrank'))
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
        await message.answer("ID корректный.")
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
async def handle_rank_choice(callback_query: types.CallbackQuery, state: FSMContext):
    rank = callback_query.data  # Получаем выбранный ранг

    # Получаем данные из FSM
    data = await state.get_data()
    user_id = data.get("user_id")

    # Логика смены ранга
    print(f"Смена ранга: Пользователь {user_id} получает ранг '{rank}'.")
    db.set_rank(user_id, rank)
    
    # Отправляем подтверждение
    await callback_query.answer(f"Ранг '{rank}' успешно установлен для пользователя с ID {user_id}.")
    await state.clear()
