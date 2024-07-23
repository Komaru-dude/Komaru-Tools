import sqlite3

DB_PATH = 'G:/Komaru db/users.db'

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
                        message_count INTEGER DEFAULT 0,
                        demotivators INTEGER DEFAULT 0,
                        pred_limit INTEGER DEFAULT 3
                    )''')
    conn.commit()
    conn.close()

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
    rank = cursor.fetchone()[0]
    conn.close()
    return rank

def update_user_warns(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET warns = warns + 1 WHERE user_id = ?''', (user_id,))
    conn.commit()
    cursor.execute('''SELECT warns FROM users WHERE user_id = ?''', (user_id,))
    warns = cursor.fetchone()[0]
    conn.close()
    return warns

def update_user_bans(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET bans = bans + 1 WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()

def update_user_mutes(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET mutes = mutes + 1 WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()
