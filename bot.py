import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils import deep_linking
from dotenv import load_dotenv
from database import create_db, add_user, set_user_rank, get_user_rank, update_user_warns, update_user_bans, update_user_mutes

# Загрузка переменных окружения из файла .env
load_dotenv()

API_TOKEN = os.getenv('BOT_API_TOKEN')
ADMIN_ID = 1567704438  # Администратор ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Используем встроенное хранилище
dp = Dispatcher(storage=storage)

# Создание базы данных
create_db()

# Приветствие новых пользователей и добавление их в базу данных
@dp.message(content_types=['new_chat_members'])
async def on_user_joined(message: types.Message):
    for new_member in message.new_chat_members:
        await message.reply(f"Добро пожаловать, {new_member.full_name}!")
        add_user(new_member.id)

# Команда для установки статуса пользователя
@dp.message(Command('setrank'))
async def set_rank(message: types.Message):
    if message.from_user.id == ADMIN_ID:  # Проверка на администратора
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply("Использование: /setrank <user_id> <rank>")
            return

        user_id, rank = int(parts[1]), parts[2]
        if rank not in ['Участник', 'Модератор', 'Администратор', 'Владелец']:
            await message.reply("Недопустимый статус. Используйте: Участник, Модератор, Администратор, Владелец.")
            return

        set_user_rank(user_id, rank)
        await message.reply(f"Статус пользователя {user_id} установлен на {rank}.")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")

# Проверка статуса пользователя
def has_permission(user_id, required_ranks):
    user_rank = get_user_rank(user_id)
    return user_rank in required_ranks

# Команды для предупреждений, банов и мутов
@dp.message(Command('warn'))
async def warn_user(message: types.Message):
    if has_permission(message.from_user.id, ['Модератор', 'Администратор', 'Владелец']):
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            warns = update_user_warns(user_id)
            await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} получил предупреждение. Количество предупреждений: {warns}")
            if warns >= 3:
                await message.chat.kick(user_id)
                await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} был забанен за 3 предупреждения.")
                update_user_bans(user_id)
        else:
            await message.reply("Эту команду можно использовать только в ответ на сообщение пользователя.")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")

@dp.message(Command('ban'))
async def ban_user(message: types.Message):
    if has_permission(message.from_user.id, ['Администратор', 'Владелец']):
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            await message.chat.kick(user_id)
            update_user_bans(user_id)
            await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} был забанен.")
        else:
            await message.reply("Эту команду можно использовать только в ответ на сообщение пользователя.")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")

@dp.message(Command('mute'))
async def mute_user(message: types.Message):
    if has_permission(message.from_user.id, ['Модератор', 'Администратор', 'Владелец']):
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            await bot.restrict_chat_member(message.chat.id, user_id, permissions=types.ChatPermissions(can_send_messages=False))
            update_user_mutes(user_id)
            await message.reply(f"Пользователь {message.reply_to_message.from_user.full_name} был замьючен.")
        else:
            await message.reply("Эту команду можно использовать только в ответ на сообщение пользователя.")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")

if __name__ == '__main__':
    # Запуск бота
    from aiogram import Dispatcher, Bot
    from aiogram.utils import executor

    dp = Dispatcher()
    executor.start_polling(dp, skip_updates=True)
