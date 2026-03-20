import sqlite3

def init_db():
    conn = sqlite3.connect('bgmi_market.db')
    c = conn.cursor()
    # Users & Sellers Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY, 
                 username TEXT, 
                 reports INTEGER DEFAULT 0, 
                 vouches INTEGER DEFAULT 0, 
                 score INTEGER DEFAULT 50, 
                 is_verified INTEGER DEFAULT 0, 
                 is_banned INTEGER DEFAULT 0,
                 status TEXT DEFAULT 'Safe')''')
    
    # Reports Table for Admin Approval
    c.execute('''CREATE TABLE IF NOT EXISTS pending_reports (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 reporter_id INTEGER,
                 target_username TEXT,
                 reason TEXT,
                 proof_file_id TEXT)''')
    
    # Registration Table
    c.execute('''CREATE TABLE IF NOT EXISTS pending_regs (
                 user_id INTEGER PRIMARY KEY,
                 details TEXT)''')
    conn.commit()
    conn.close()

def get_user(username):
    username = username.replace("@", "")
    conn = sqlite3.connect('bgmi_market.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    res = c.fetchone()
    conn.close()
    return res

def update_score(username, v_mod=0, r_mod=0):
    username = username.replace("@", "")
    conn = sqlite3.connect('bgmi_market.db')
    c = conn.cursor()
    c.execute("UPDATE users SET vouches = vouches + ?, reports = reports + ? WHERE username = ?", (v_mod, r_mod, username))
    # Recalculate Score: (vouches * 5) - (reports * 25) + (20 if verified else 0)
    c.execute("SELECT vouches, reports, is_verified FROM users WHERE username = ?", (username,))
    v, r, ver = c.fetchone()
    new_score = (v * 5) - (r * 25) + (20 if ver else 0)
    
    status = "Trusted" if new_score >= 80 else "Safe" if new_score >= 50 else "Risky" if new_score >= 20 else "Scammer"
    c.execute("UPDATE users SET score = ?, status = ? WHERE username = ?", (new_score, status, username))
    conn.commit()
    conn.close()
