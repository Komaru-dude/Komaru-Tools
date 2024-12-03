import sqlite3, os, json, time

DB_PATH = 'users.db'

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username INTEGER DEFAULT '',
                        warns INTEGER DEFAULT 0,
                        bans INTEGER DEFAULT 0,
                        mutes INTEGER DEFAULT 0,
                        reputation INTEGER DEFAULT 0,
                        rank TEXT DEFAULT 'Участник',
                        status TEXT DEFAULT '',
                        message_count INTEGER DEFAULT 0,
                        demotivators INTEGER DEFAULT 0,
                        warn_limit INTEGER DEFAULT 3,
                        history TEXT DEFAULT ''
                    )''')
    conn.commit()
    conn.close()

# Проверяем существование базы данных и создаём её при необходимости
if not os.path.exists(DB_PATH):
    create_db()

# Функция для проверки ранга пользователя
def has_permission(user_id):
    # Список разрешенных статусов
    allowed_ranks = ["Администратор", "Модератор", "Владелец"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Извлекаем ранг пользователя
    cursor.execute('''SELECT rank FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return False
    
    user_status = result[0]  # Получаем статус пользователя
    return user_status in allowed_ranks  # Проверяем, входит ли ранг в разрешенные

def user_have_username(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    conn.close()
    if not exists == '':
        return False
    else:
        return True
    
def add_username(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
    conn.commit()
    conn.close()

def get_username(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_id_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT user_id FROM users WHERE username = ?''', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return None  # Если юзернейм не найден, возвращаем None
    
    return result[0]  # Возвращаем user_id

def set_rank(user_id, rank):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET rank = ? WHERE user_id = ?''', (rank, user_id))
    conn.commit()
    conn.close()

def user_exists(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT 1 FROM users WHERE user_id = ?''', (user_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def set_status(user_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET status = ? WHERE user_id = ?''', (status, user_id))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (user_id) VALUES (?)''', (user_id,))
    conn.commit()
    conn.close()

def get_user_rank(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT rank FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return None
    return result[0]

def update_user_warns(user_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем текущую историю и количество предупреждений
    cursor.execute('''SELECT history, warns FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None:
        history = []
        warns = 0  # Если пользователь не существует, начинаем с 0 предупреждений
    else:
        history = json.loads(result[0]) if result[0] else []  # Парсим историю, если она есть
        warns = result[1]  # Получаем количество предупреждений

    # Добавляем новое предупреждение
    punishment = {
        "type": "warn",
        "reason": reason,
        "timestamp": int(time.time()),  # Время наказания в формате Unix timestamp
    }

    history.append(punishment)

    # Обновляем только историю
    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))

    # Увеличиваем количество предупреждений
    warns += 1
    cursor.execute('''UPDATE users SET warns = ? WHERE user_id = ?''', (warns, user_id))

    conn.commit()
    conn.close()

def update_user_bans(user_id, reason, duration=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем текущую историю
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None or not result[0]:
        history = []  # Если истории нет, создаем новый список
    else:
        history = json.loads(result[0])  # Парсим историю как JSON

    # Добавляем наказание типа ban
    punishment = {
        "type": "ban",
        "reason": reason,  # Причина передается как аргумент
        "timestamp": int(time.time()),  # Время начала наказания в формате Unix timestamp
    }

    if duration:
        punishment["duration"] = duration
        punishment["end_time"] = int(time.time()) + duration  # Время окончания
    else:
        punishment["end_time"] = None  # Если не указано время окончания, оставляем None

    history.append(punishment)

    # Обновляем историю в базе данных
    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))
    conn.commit()
    conn.close()

def update_user_mutes(user_id, reason, duration=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем текущую историю
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None or not result[0]:
        history = []  # Если истории нет, создаем новый список
    else:
        history = json.loads(result[0])  # Парсим историю как JSON

    # Добавляем наказание типа mute
    punishment = {
        "type": "mute",
        "reason": reason,  # Причина передается как аргумент
        "timestamp": int(time.time()),  # Время начала наказания в формате Unix timestamp
    }

    if duration:
        punishment["duration"] = duration
        punishment["end_time"] = int(time.time()) + duration  # Время окончания
    else:
        punishment["end_time"] = None  # Если не указано время окончания, оставляем None

    history.append(punishment)

    # Обновляем историю в базе данных
    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))
    conn.commit()
    conn.close()

def update_count_messges(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET message_count = message_count + 1 WHERE user_id =?''', (user_id,))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
    user_data = cursor.fetchone()
    
    if user_data is None:
        # Если пользователя нет, создаём его
        add_user(user_id)
        # Повторно извлекаем данные для нового пользователя
        cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        user_data = cursor.fetchone()
    
    conn.close()
    return user_data

def update_user_id(user_id, new_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Обновляем ID пользователя
    cursor.execute('''UPDATE users SET user_id = ? WHERE user_id = ?''', (new_id, user_id))
    conn.commit()
    
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Извлекаем историю наказания
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None or not result[0]:
        return []  # Если данных нет, возвращаем пустой список
    
    return json.loads(result[0])  # Парсим JSON и возвращаем список
