import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER DEFAULT 50, status TEXT DEFAULT '🟡 Safe')''')
    c.execute('''CREATE TABLE IF NOT EXISTS sellers (username TEXT PRIMARY KEY, deals TEXT, channel TEXT, experience TEXT)''')
    conn.commit()
    conn.close()

def add_user(uid, user):
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, user))
    conn.commit()
    conn.close()

def get_all_uids():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    data = [row[0] for row in c.fetchall()]
    conn.close()
    return data

def save_reg(user, deals, channel, exp):
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sellers VALUES (?, ?, ?, ?)", (user, deals, channel, exp))
    conn.commit()
    conn.close()
