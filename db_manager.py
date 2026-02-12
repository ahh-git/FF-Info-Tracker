import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "firetracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            searched_uid TEXT,
            player_name TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def add_history(user_email, uid, player_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (user_email, searched_uid, player_name, timestamp) VALUES (?, ?, ?, ?)",
              (user_email, uid, player_name, datetime.now()))
    conn.commit()
    conn.close()

def get_user_history(user_email):
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT searched_uid, player_name, timestamp FROM history WHERE user_email = ? ORDER BY timestamp DESC", conn, params=(user_email,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df
