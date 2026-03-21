import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    # Users for broadcast
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id PRIMARY KEY)')
    # Scammers with Proofs
    c.execute('CREATE TABLE IF NOT EXISTS scammers (username TEXT PRIMARY KEY, amount TEXT, proof_id TEXT)')
    # Verified Sellers
    c.execute('CREATE TABLE IF NOT EXISTS sellers (username TEXT PRIMARY KEY, channel TEXT, deals TEXT)')
    conn.commit()
    conn.close()

def add_to_db(table, data):
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    if table == "users":
        c.execute("INSERT OR IGNORE INTO users VALUES (?)", (data,))
    elif table == "scammers":
        c.execute("INSERT OR REPLACE INTO scammers VALUES (?, ?, ?)", data)
    elif table == "sellers":
        c.execute("INSERT OR REPLACE INTO sellers VALUES (?, ?, ?)", data)
    conn.commit()
    conn.close()

def check_user(username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM scammers WHERE LOWER(username)=?", (username,))
    scam = c.fetchone()
    c.execute("SELECT * FROM sellers WHERE LOWER(username)=?", (username,))
    sell = c.fetchone()
    conn.close()
    return scam, sell
