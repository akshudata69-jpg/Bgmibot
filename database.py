import sqlite3

def init_db():
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    # User data: reports, vouches, score, verified status
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY, username TEXT, reports INTEGER DEFAULT 0, 
                 vouches INTEGER DEFAULT 0, score INTEGER DEFAULT 50, 
                 is_verified INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, 
                 status TEXT DEFAULT '🟡 Safe', experience INTEGER DEFAULT 0)''')
    # Admin Approval Queue for Proofs and Registrations
    c.execute('''CREATE TABLE IF NOT EXISTS pending_actions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                 target TEXT, type TEXT, proof_id TEXT, details TEXT)''')
    # Activity Log
    c.execute('''CREATE TABLE IF NOT EXISTS activity (
                 user_id INTEGER, action_text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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

def add_or_update_user(user_id, username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_stats(username, v_mod=0, r_mod=0):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("UPDATE users SET vouches = vouches + ?, reports = reports + ? WHERE LOWER(username) = ?", (v_mod, r_mod, username))
    conn.commit()
    conn.close()
    recalculate_score(username)

def recalculate_score(username):
    username = username.replace("@", "").strip().lower()
    conn = sqlite3.connect('safedeal.db')
    c = conn.cursor()
    c.execute("SELECT vouches, reports, is_verified, experience FROM users WHERE LOWER(username) = ?", (username,))
    row = c.fetchone()
    if row:
        v, r, ver, exp = row
        # Trust Formula: (v*5) - (r*25) + bonus(ver:20, exp:10)
        score = (v * 5) - (r * 25) + (20 if ver else 0) + (10 if exp > 0 else 0)
        status = "🟢 Trusted" if score >= 80 else "🟡 Safe" if score >= 50 else "⚠️ Risky" if score >= 20 else "❌ Scammer"
        c.execute("UPDATE users SET score = ?, status = ? WHERE LOWER(username) = ?", (score, status, username))
    conn.commit()
    conn.close()
