from bot import db
from aiogram import Router, types, Bot
from aiogram.filters import Command
from datetime import datetime, timedelta
import os

mod_router = Router()
ADMIN_ID = os.getenv("ADMIN_ID")

# Функция для парсинга времени
def parse_time(time_str):
    """Парсит время из строки формата 3h, 3m или 3d"""
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

@mod_router.message(Command("warn"))
async def warn_cmd(message: types.Message, bot: Bot):
    # Проверяем, есть ли у пользователя разрешение на "блокировку пользователей"
    user_id = message.from_user.id
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    # Проверяем, ответил ли пользователь на сообщение
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        reason = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else "Без причины"
        if not db.user_exists(target_user_id):
            db.add_user(target_user_id)
        db.update_user_warns(target_user_id, reason)
        await message.reply(f"Пользователь с ID {target_user_id} был предупреждён.\n"
                            f"Причина: {reason}")
        await message.delete()
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
                    await message.reply(f"Пользователь с ID {target_user_id} был предупреждён.\n"
                                         f"Причина: {reason}")
                    user_data = db.get_user_data(target_user_id)
                    warns = user_data[2]
                    warn_limit = user_data[10]
                    if warns >= warn_limit:
                        until_date = datetime.now() + timedelta(hours=2)
                        await bot.restrict_chat_member(message.chat.id, target_user_id, types.ChatPermissions(can_send_messages=False, can_send_other_messages=False), until_date=until_date)
                        db.update_user_mutes(target_user_id, "Превышение лимита предупреждений")
                        db.update_user_warn_limit(target_user_id, 3)
                        await message.reply(f"Пользователь с ID {target_user_id} был замьючен на 2 часа за превышение лимита предупреждений.")
                else:
                    await message.reply(f"Пользователь с юзернеймом @{username} не найден.")
            elif user_input.isdigit():  # Если введён ID
                target_user_id = int(user_input)
                try:
                    if not db.user_exists(target_user_id):
                        db.add_user(target_user_id)
                    db.update_user_warns(target_user_id, reason)
                    await message.reply(f"Пользователь с ID {target_user_id} был предупреждён.\n"
                                         f"Причина: {reason}")
                    user_data = db.get_user_data(target_user_id)
                    warns = user_data[2]
                    warn_limit = user_data[10]
                    if warns >= warn_limit:
                        until_date = datetime.now() + timedelta(hours=2)
                        await bot.restrict_chat_member(message.chat.id, target_user_id, types.ChatPermissions(can_send_messages=False, can_send_other_messages=False), until_date=until_date)
                        db.update_user_mutes(target_user_id, "Превышение лимита предупреждений")
                        db.update_user_warn_limit(target_user_id, 3)
                        await message.reply(f"Пользователь с ID {target_user_id} был замьючен на 2 часа за превышение лимита предупреждений.")
                except Exception as e:
                    await message.reply(f"Не удалось найти пользователя с ID {target_user_id}.")
                    await bot.send_message(chat_id=ADMIN_ID, 
                                           text=f"Во время обработки команды /warn произошла ошибка: {e}")
            else:
                await message.reply("Некорректный формат. Используйте /warn @username или /warn ID причина.")
        else:
            await message.reply("Синтаксис команды некорректный.\n"
                                 "Используйте /warn @username причина или /warn ID причина.")

@mod_router.message(Command("mute"))
async def cmd_mute(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    # Проверка прав пользователя
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Разбиваем текст команды
    parts = message.text.split(' ', 3)  # Ожидаем до 4 частей: /mute цель время причина

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        duration = parse_time(parts[1]) if len(parts) > 1 and parse_time(parts[1]) else None
        reason = parts[2] if len(parts) > 2 else "Без причины"
        until_date = datetime.now() + duration if duration else None
    else:
        if len(parts) < 2:
            await message.reply("Ошибка: необходимо указать username, ID или ответить на сообщение цели.")
            return

        user_input = parts[1]

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
            await message.reply("Некорректный формат. Используйте /mute <цель> <время> <причина>.")
            return

        # Проверяем время и причину
        duration = parse_time(parts[2]) if len(parts) > 2 and parse_time(parts[2]) else None
        reason = parts[3] if len(parts) > 3 else "Без причины"
        until_date = datetime.now() + duration if duration else None

    # Применение мута
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            target_user_id,
            types.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        db.update_user_mutes(target_user_id, reason)
        time_str = f"до {until_date}" if until_date else "навсегда"
        await message.reply(f"Пользователь с ID {target_user_id} был замьючен на {time_str}.\n" 
                            f"Причина: {reason}")
    except Exception as e:
        await message.reply(f"Не удалось замьютить пользователя.")
        await bot.send_message(chat_id=ADMIN_ID, 
                                text=f"Во время обработки команды /mute произошла ошибка: {e}")

@mod_router.message(Command('ban'))
async def cmd_ban(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    # Проверка прав пользователя
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Разбиваем текст команды
    parts = message.text.split(' ', 3)  # Ожидаем до 4 частей: /ban цель время причина

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        ban_duration = parse_time(parts[1]) if len(parts) > 1 and parse_time(parts[1]) else None
        reason = parts[2] if len(parts) > 2 else "Без причины"
        until_date = datetime.now() + ban_duration if ban_duration else None
    else:
        if len(parts) < 2:
            await message.reply("Ошибка: необходимо указать username, ID или ответить на сообщение цели.")
            return

        user_input = parts[1]

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
            await message.reply("Некорректный формат. Используйте /ban <цель> <время> <причина>.")
            return

        # Проверяем время и причину
        ban_duration = parse_time(parts[2]) if len(parts) > 2 and parse_time(parts[2]) else None
        reason = parts[3] if len(parts) > 3 else "Без причины"
        until_date = datetime.now() + ban_duration if ban_duration else None

    # Выполняем бан
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user_id, until_date=until_date)
        ban_time_str = f"до {until_date}" if until_date else "навсегда"
        await message.reply(f"Пользователь {target_user_id} был забанен {ban_time_str}.\nПричина: {reason}")
    except Exception as e:
        await message.reply(f"Не удалось забанить пользователя.")
        await bot.send_message(chat_id=ADMIN_ID, 
                                text=f"Во время обработки команды /ban произошла ошибка: {e}")

@mod_router.message(Command('unmute'))
async def cmd_unmute(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    text = message.text
    parts = text.split(maxsplit=1)
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if len(parts) < 2:
        await message.reply("Не указано имя пользователя/ID")
        return
    
    target_input = parts[1]

    if target_input.startswith("@"):
        target_id = db.get_user_id_by_username(target_input[1:])
    elif text.isdigit():
        target_id = int(target_input)
    else:
        await message.reply("Некорректный формат. Используйте /unmute <username/ID>.")
        return
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            target_id, 
            types.ChatPermissions(can_send_messages=True, can_send_other_messages=True), 
            until_date=None)
        await message.reply(f"Пользователь {target_id} размьючен.")
    except Exception as e:
        await message.reply(f"Не удалось снять мьют.")
        await bot.send_message(chat_id=ADMIN_ID, 
                                text=f"Во время обработки команды /unmute произошла ошибка: {e}")

@mod_router.message(Command('unban'))
async def cmd_unmute(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    text = message.text
    parts = text.split(maxsplit=1)
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if len(parts) < 2:
        await message.reply("Не указано имя пользователя/ID")
        return
    
    target_input = parts[1]

    if target_input.startswith("@"):
        try:
            target_id = db.get_user_id_by_username(target_input[1:])
        except Exception as e:
            message.reply("Возникла ошибка при получении ID пользователя.")

    elif text.isdigit():
        target_id = int(target_input)
    else:
        await message.reply("Некорректный формат. Используйте /unban <username/ID>.")
        return
    try:
        await bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
        await message.reply(f"Пользователь {target_id} разбанен.")
    except Exception as e:
        await message.reply(f"Не удалось снять бан.")
        await bot.send_message(chat_id=ADMIN_ID, 
                                text=f"Во время обработки команды /unban произошла ошибка: {e}")

@mod_router.message(Command("history"))
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
        history_text += f"{i}. {punishment_type.capitalize()} - Причина: {reason}.\n"
    
    warns_count = len(history)
    response = (
        f"Всего наказаний: {warns_count}\n"
        f"История наказаний:\n{history_text}"
    )
    await message.reply(response)


