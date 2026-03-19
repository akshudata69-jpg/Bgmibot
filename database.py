import sqlite3

def init_db():
    conn = sqlite3.connect('bgmi_bot.db')
    c = conn.cursor()
    # Scammers Table
    c.execute('''CREATE TABLE IF NOT EXISTS scammers 
                 (id TEXT PRIMARY KEY, reason TEXT, proof TEXT)''')
    # Users Table (For Broadcast)
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    # Pending Reports Table (Approval System)
    c.execute('''CREATE TABLE IF NOT EXISTS pending_reports 
                 (report_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                  scammer_id TEXT, reason TEXT, proof_file_id TEXT)''')
    # Trusted Sellers Table
    c.execute('''CREATE TABLE IF NOT EXISTS sellers 
                 (username TEXT PRIMARY KEY, description TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bgmi_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bgmi_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# Logic for searching, adding scammers, and pending reports goes here...
