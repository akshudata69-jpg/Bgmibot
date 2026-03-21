import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    # Users for broadcast
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    # Scammers: Username, Amount, Proof File ID
    c.execute('CREATE TABLE IF NOT EXISTS scammers (username TEXT PRIMARY KEY, amount TEXT, proof_id TEXT)')
    # Sellers: Username, Channel, Deals
    c.execute('CREATE TABLE IF NOT EXISTS sellers (username TEXT PRIMARY KEY, channel TEXT, deals TEXT)')
    conn.commit()
    conn.close()

def add_user(uid):
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    return [row[0] for row in c.fetchall()]

def check_db(username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM scammers WHERE LOWER(username)=?", (username,))
    scam = c.fetchone()
    c.execute("SELECT * FROM sellers WHERE LOWER(username)=?", (username,))
    sell = c.fetchone()
    conn.close()
    return scam, sell
