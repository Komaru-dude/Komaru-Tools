import sqlite3, os, json, time, random

DB_PATH = 'users.db'

RANK_TO_LEVEL = {
    "Забанен": 0,
    "Замьючен": 0,
    "Участник": 1,
    "Модератор": 2,
    "Администратор": 3,
    "Владелец": 4
}

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
                        prefix TEXT DEFAULT 'Отсутствует',
                        message_count INTEGER DEFAULT 0,
                        demotivators INTEGER DEFAULT 0,
                        warn_limit INTEGER DEFAULT 3,
                        history TEXT DEFAULT '',
                        first_name TEXT DEFAULT '',
                        need_msg INTEGER DEFAULT 10
                    )''')
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    create_db()

def has_permission(user_id, level):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''SELECT rank FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return False
    
    user_rank = result[0]
    user_level = RANK_TO_LEVEL.get(user_rank)
    
    if user_level is None:
        return False

    return user_level >= level

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

def set_prefix(user_id, prefix):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET prefix = ? WHERE user_id = ?''', (prefix, user_id))
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

    cursor.execute('''SELECT history, warns FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None:
        history = []
        warns = 0
    else:
        history = json.loads(result[0]) if result[0] else []
        warns = result[1]

    punishment = {
        "type": "warn",
        "reason": reason,
        "timestamp": int(time.time()),
    }

    history.append(punishment)

    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))

    warns += 1
    cursor.execute('''UPDATE users SET warns = ? WHERE user_id = ?''', (warns, user_id))

    conn.commit()
    conn.close()

def update_user_bans(user_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT history, bans FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None or not result[0]:
        history = []
        bans = 0
    else:
        history = json.loads(result[0])
        bans = result[1]

    punishment = {
        "type": "ban",
        "reason": reason,
        "timestamp": int(time.time()),
    }

    history.append(punishment)

    bans += 1
    cursor.execute('''UPDATE users SET bans = ? WHERE user_id = ?''', (bans, user_id))

    cursor.execute('''UPDATE users SET history = ? WHERE user_id = ?''', (json.dumps(history), user_id))
    conn.commit()
    conn.close()

def update_user_mutes(user_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT history, mutes FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()

    if result is None or not result[0]:
        history = []
        mutes = 0
    else:
        history = json.loads(result[0])
        mutes = result[1]

    punishment = {
        "type": "mute",
        "reason": reason,
        "timestamp": int(time.time()),
    }

    mutes += 1
    cursor.execute('''UPDATE users SET mutes = ? WHERE user_id = ?''', (mutes, user_id))

    history.append(punishment)

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
    
    cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
    user_data = cursor.fetchone()
    
    if user_data is None:
        add_user(user_id)
        cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
        user_data = cursor.fetchone()
    
    conn.close()
    return user_data

def update_user_id(user_id, new_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET user_id = ? WHERE user_id = ?''', (new_id, user_id))
    conn.commit()
    
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''SELECT history FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None or not result[0]:
        return []
    
    return json.loads(result[0])

def update_user_warn_limit(user_id, limit):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET warn_limit = warn_limit + ? WHERE user_id = ?''', (limit, user_id))
    conn.commit()
    conn.close()

def set_param(user_id, param, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"UPDATE users SET {param} = ? WHERE user_id = ?"
    try:
        cursor.execute(query, (value, user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении параметра: {e}")
    conn.close()

def get_first_name_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT first_name FROM users WHERE user_id = ?''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_first_name(user_id, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET first_name = ? WHERE user_id = ?''', (first_name, user_id))
    conn.commit()
    conn.close()

def user_have_first_name(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT first_name FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    conn.close()
    if not exists == '':
        return False
    else:
        return True

def update_rep(user_id, mode, value=None):
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Неверный user_id. Он должен быть целым числом.")
    if mode not in ["auto_add", "manual_add", "manual_rem"]:
        raise ValueError(f"Режим {mode} некорректен, доступные режимы: auto_add, manual_add, manual_rem.")
    if mode in ["manual_add", "manual_rem"] and (not value or not isinstance(value, int)):
        raise ValueError("Для режимов manual_add и manual_rem необходимо указать целое значение для value.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if value is None and mode == "auto_add":
        value = random.randint(1, 6)
    
    if mode == "auto_add":
        add = random.randint(1, 6)
        cursor.execute('''UPDATE users SET reputation = reputation + ? WHERE user_id = ?''', (add, user_id))
    elif mode == "manual_add":
        cursor.execute('''UPDATE users SET reputation = reputation + ? WHERE user_id = ?''', (value, user_id))
    elif mode == "manual_rem":
        cursor.execute('''UPDATE users SET reputation = reputation - ? WHERE user_id = ?''', (value, user_id))
    
    conn.commit()
    conn.close()

def update_need_msg(user_id, count_msg):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET need_msg = ? WHERE user_id = ?''', (count_msg, user_id))
    conn.commit()
    conn.close()