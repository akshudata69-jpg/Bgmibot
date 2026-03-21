import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    # Main Users & Sellers Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY, username TEXT, reports INTEGER DEFAULT 0, 
                 vouches INTEGER DEFAULT 0, score INTEGER DEFAULT 50, 
                 is_verified INTEGER DEFAULT 0, status TEXT DEFAULT '🟡 Safe')''')
    # Activity Log
    c.execute('''CREATE TABLE IF NOT EXISTS activity (
                 user_id INTEGER, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_user(username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def update_score(username, v_mod=0, r_mod=0):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    c.execute("UPDATE users SET vouches = vouches + ?, reports = reports + ? WHERE LOWER(username) = ?", (v_mod, r_mod, username))
    
    # Recalculate Score: (vouches * 5) - (reports * 25) + (20 if verified)
    c.execute("SELECT vouches, reports, is_verified FROM users WHERE LOWER(username) = ?", (username,))
    v, r, ver = c.fetchone()
    score = (v * 5) - (r * 25) + (20 if ver else 0)
    status = "🟢 Trusted" if score >= 80 else "🟡 Safe" if score >= 50 else "⚠️ Risky" if score >= 20 else "❌ Scammer"
    
    c.execute("UPDATE users SET score = ?, status = ? WHERE LOWER(username) = ?", (score, status, username))
    conn.commit()
    conn.close()
