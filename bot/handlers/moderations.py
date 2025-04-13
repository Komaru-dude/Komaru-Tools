import os, subprocess, requests, re
from bot import db
from aiogram import Router, types, Bot
from aiogram.filters import Command
from datetime import datetime, timedelta
from .. import OWNER_ID

mod_router = Router()
OWNER_ID = os.getenv("OWNER_ID")

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
    user_id = message.from_user.id
    parts = message.text.split(' ', 2)

    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        reason = parts[2] if len(parts) > 2 else "Без причины"
    elif parts[1].startswith("@"):
        user_tag = parts[1]
        reason = parts[2] if len(parts) > 2 else "Без причины"
        try:
            response = requests.get(f"http://127.0.0.1:8000/user/{user_tag}")
            response.raise_for_status()
            user_data = response.json()

            target_user_id = user_data.get("user_id", None)
            if target_user_id is None:
                error_message = user_data.get("error", "Не удалось найти пользователя")
                await message.reply(f"Ошибка: {error_message}")
                return
        except requests.exceptions.RequestException as e:
            await message.reply(f"Ошибка при запросе: {str(e)}")
            return
    elif parts[1].isdigit:
        target_user_id = parts[1]
        reason = parts[2] if len(parts) > 2 else "Без причины"
    else:
        await message.reply("Некорретный формат.\nИспользуйте /warn @username/ID причина.")
        return

    db.update_user_warns(target_user_id, reason)
    user_data = db.get_user_data(target_user_id)
    if user_data:
        warns = int(user_data[1])
        warn_limit = int(user_data[9])
        print(warns, warn_limit)
    else:
        db.add_user(target_user_id)
        warns = 0
        warn_limit = 3

    warns += 1

    if warns > warn_limit:
        warn_limit += 3
        db.update_user_mutes(target_user_id, "Превышение лимита предупреждений")
        try:
            until_date = datetime.now() + timedelta(hours=24)
            await bot.restrict_chat_member(
                message.chat.id,
                target_user_id,
                types.ChatPermissions(can_send_messages=False),
                until_date=until_date)
            db.update_user_mutes(target_user_id, "Превышение лимита предупреждений")
            time_str = f"до {until_date.strftime('%Y-%m-%d %H:%M:%S')}"
            await message.answer(f"Пользователь с ID {target_user_id} был замьючен {time_str}.\nПричина: Превышение лимита предупреждений")
            db.update_rep(user_id, mode="manual_rem", value=15)
            db.update_user_warn_limit(target_user_id, warn_limit)
        except Exception as e:
            await message.reply(f"Не удалось замьютить пользователя.")
            await bot.send_message(chat_id=OWNER_ID, text=f"Во время обработки команды /mute произошла ошибка: {e}")
    else:
        await message.reply(f"Пользователь с ID {target_user_id} был предупреждён.\nПричина: {reason}")

@mod_router.message(Command("mute"))
async def cmd_mute(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    

    # Проверка прав пользователя
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Разбиваем текст команды
    parts = message.text.split(' ', 3)
    parts1 = parts[1] if len(parts) > 1 else None

    # Проверка: ответ на сообщение или указан username/ID
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        duration = parse_time(parts[1]) if len(parts) > 1 and parse_time(parts[1]) else None
        reason = parts[2] if len(parts) > 2 else "Без причины"
        until_date = datetime.now() + duration if duration else None
        await message.reply_to_message.delete()
    else:
        if len(parts) < 2:
            await message.reply("Ошибка: необходимо указать username, ID или ответить на сообщение цели.")
            return

        user_input = parts[1]

        # Если указан username
        if user_input.startswith('@'):
            mention_match = re.search(r"@(\w+)", parts1)
            if mention_match:
                user_tag = mention_match.group(0)
                try:
                    response = requests.get(f"http://127.0.0.1:8000/user/{user_tag}")
                    response.raise_for_status()
                    user_data = response.json()

                    target_user_id = user_data.get("user_id", None)
                    if target_user_id is None:
                        error_message = user_data.get("error", "Не удалось найти пользователя")
                        await message.reply(f"Ошибка: {error_message}")
                        return
                except requests.exceptions.RequestException as e:
                    await message.reply(f"Ошибка при запросе: {str(e)}")
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
        time_str = f"до {until_date.strftime('%Y-%m-%d %H:%M:%S')}" if until_date else "навсегда"
        await message.reply(f"Пользователь с ID {target_user_id} был замьючен {time_str}.\n" 
                            f"Причина: {reason}")
        db.update_rep(user_id, mode="manual_rem", value=10)
    except Exception as e:
        await message.reply(f"Не удалось замьютить пользователя.")
        await bot.send_message(chat_id=OWNER_ID, 
                                text=f"Во время обработки команды /mute произошла ошибка: {e}")

@mod_router.message(Command('ban'))
async def cmd_ban(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=2)

    parts1 = parts[1] if len(parts) > 1 else None
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        user = message.reply_to_message.from_user
        ban_duration = parse_time(parts[1]) if len(parts) > 1 and parse_time(parts[1]) else None
        reason = parts[2] if len(parts) > 2 else "Без причины"
        until_date = datetime.now() + ban_duration if ban_duration else None
        await message.reply_to_message.delete()
    elif parts1 and "@" in parts1:
        mention_match = re.search(r"@(\w+)", parts1)
        ban_duration = parse_time(parts[1]) if len(parts) > 1 and parse_time(parts[1]) else None
        reason = parts[2] if len(parts) > 2 else "Без причины"
        until_date = datetime.now() + ban_duration if ban_duration else None
        if mention_match:
            user_tag = mention_match.group(0)
            try:
                response = requests.get(f"http://127.0.0.1:8000/user/{user_tag}")
                response.raise_for_status()
                user_data = response.json()

                target_id = user_data.get("user_id", None)
                if target_id is None:
                    error_message = user_data.get("error", "Не удалось найти пользователя")
                    await message.reply(f"Ошибка: {error_message}")
                    return

                user = None
            except requests.exceptions.RequestException as e:
                await message.reply(f"Ошибка при запросе: {str(e)}")
                return
        else:
            await message.reply("Неверный формат юзернейма.")
            return
    else:
        if len(parts) > 1:
            target_id = parts[1]
            user = None
        else:
            user = message.from_user
            target_id = user.id

        # Проверяем время и причину
        ban_duration = parse_time(parts[2]) if len(parts) > 2 and parse_time(parts[2]) else None
        reason = parts[3] if len(parts) > 3 else "Без причины"
        until_date = datetime.now() + ban_duration if ban_duration else None

    # Выполняем бан
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id, until_date=until_date)
        ban_time_str = f"до {until_date}" if until_date else "навсегда"
        await message.reply(f"Пользователь {target_id} был забанен {ban_time_str}.\nПричина: {reason}")
        db.update_rep(user_id, mode="manual_rem", value=15)
    except Exception as e:
        await message.reply(f"Не удалось забанить пользователя.")
        await bot.send_message(chat_id=OWNER_ID, 
                                text=f"Во время обработки команды /ban произошла ошибка: {e}")

@mod_router.message(Command('unmute'))
async def cmd_unmute(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    text = message.text
    parts = text.split(maxsplit=1)
    parts1 = parts[1] if len(parts) > 1 else None
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        user = message.reply_to_message.from_user
    elif parts1 and "@" in parts1:
        mention_match = re.search(r"@(\w+)", parts1)
        if mention_match:
            user_tag = mention_match.group(0)
            try:
                response = requests.get(f"http://127.0.0.1:8000/user/{user_tag}")
                response.raise_for_status()
                user_data = response.json()

                target_id = user_data.get("user_id", None)
                if target_id is None:
                    error_message = user_data.get("error", "Не удалось найти пользователя")
                    await message.reply(f"Ошибка: {error_message}")
                    return

                user = None
            except requests.exceptions.RequestException as e:
                await message.reply(f"Ошибка при запросе: {str(e)}")
                return
        else:
            await message.reply("Неверный формат юзернейма.")
            return
    else:
        if len(parts) > 1:
            target_id = parts[1]
            user = None
        else:
            user = message.from_user
            target_id = user.id
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            target_id, 
            types.ChatPermissions(can_send_messages=True, can_send_other_messages=True), 
            until_date=None)
        await message.reply(f"Пользователь {target_id} размьючен.")
    except Exception as e:
        await message.reply(f"Не удалось снять мьют.")
        await bot.send_message(chat_id=OWNER_ID, 
                                text=f"Во время обработки команды /unmute произошла ошибка: {e}")

@mod_router.message(Command('unban'))
async def cmd_unmute(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    text = message.text
    parts = text.split(maxsplit=1)
    parts1 = parts[1] if len(parts) > 1 else None
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        user = message.reply_to_message.from_user
    elif parts1 and "@" in parts1:
        mention_match = re.search(r"@(\w+)", parts1)
        if mention_match:
            user_tag = mention_match.group(0)
            try:
                response = requests.get(f"http://127.0.0.1:8000/user/{user_tag}")
                response.raise_for_status()
                user_data = response.json()

                target_id = user_data.get("user_id", None)
                if target_id is None:
                    error_message = user_data.get("error", "Не удалось найти пользователя")
                    await message.reply(f"Ошибка: {error_message}")
                    return

                user = None
            except requests.exceptions.RequestException as e:
                await message.reply(f"Ошибка при запросе: {str(e)}")
                return
        else:
            await message.reply("Неверный формат юзернейма.")
            return
    else:
        if len(parts) > 1:
            target_id = parts[1]
            user = None
        else:
            user = message.from_user
            target_id = user.id

    try:
        await bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
        await message.reply(f"Пользователь {target_id} разбанен.")
    except Exception as e:
        await message.reply(f"Не удалось снять бан.")
        await bot.send_message(chat_id=OWNER_ID, 
                                text=f"Во время обработки команды /unban произошла ошибка: {e}")

@mod_router.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = db.get_history(user_id)
    
    if not history:
        await message.reply("У вас пока нет наказаний.")
        return

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

@mod_router.message(Command("repadd"))
async def cmd_repadd(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    parts = text.split(' ', 2)
    if not db.has_permission(user_id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
@mod_router.message(Command("restart"))
async def restart_bot(message: types.Message, bot: Bot):
    if not db.has_permission(message.from_user.id, 2):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    await message.answer("Перезапускаюсь... 🔄")

    try:
        subprocess.Popen(["sudo", "systemctl", "restart", "komaru-tools"])
    except Exception as e:
        await message.reply("Не удалось перезагрузиться!")
        await bot.send_message(chat_id=OWNER_ID, 
                                text=f"Во время обработки команды /restart произошла ошибка: {e}")

@mod_router.message(Command("get_admins"))
async def cmd_getadmins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    