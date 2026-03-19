import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    # External and Internal Render DBs both require SSL in 2026
    return psycopg2.connect(DB_URL, sslmode='require')

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS scammers 
                   (bgmi_id TEXT PRIMARY KEY, reason TEXT, proof TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

def search_scammer(query_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scammers WHERE bgmi_id = %s", (query_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res

def add_scammer(bgmi_id, reason, proof):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO scammers (bgmi_id, reason, proof) VALUES (%s, %s, %s) ON CONFLICT (bgmi_id) DO NOTHING", (bgmi_id, reason, proof))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
