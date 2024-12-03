import sqlite3, os, json, time

DB_PATH = 'users.db'

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
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

def add_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (user_id) VALUES (?)''', (user_id,))
    conn.commit()
    conn.close()

def set_user_rank(user_id, rank):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET rank = ? WHERE user_id = ?''', (rank, user_id))
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

def update_user_warns(user_id, reason, punishment_type="warn", duration=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем текущую историю
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    
    if result is None or not result[0]:
        history = []  # Если истории нет, создаем новый список
    else:
        history = json.loads(result[0])  # Парсим историю как JSON
    
    # Добавляем новое наказание
    punishment = {
        "type": punishment_type,
        "reason": reason,
        "timestamp": int(time.time()),  # Время наказания в формате Unix timestamp
    }
    
    if punishment_type in ["ban", "mute"] and duration:
        punishment["duration"] = duration
        punishment["end_time"] = int(time.time()) + duration  # Время окончания
    
    history.append(punishment)
    
    # Обновляем историю в базе данных
    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))
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
    
    # Добавляем новое наказание (ban)
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
    
    # Добавляем новое наказание (mute)
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
        cursor.execute('''INSERT INTO users (user_id) VALUES (?)''', (user_id,))
        conn.commit()
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
