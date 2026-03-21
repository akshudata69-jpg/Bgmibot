import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    # Users table for stats and broadcasting
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY, 
                 username TEXT, 
                 reports INTEGER DEFAULT 0, 
                 vouches INTEGER DEFAULT 0, 
                 score INTEGER DEFAULT 50, 
                 is_verified INTEGER DEFAULT 0, 
                 status TEXT DEFAULT '🟡 Safe')''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_user_data(username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,))
    res = c.fetchone()
    conn.close()
    return res
