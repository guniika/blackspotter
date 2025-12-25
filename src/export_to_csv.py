import pandas as pd
import sqlite3
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "blackspotter_logs.db"

def inject_mock_data():
    print("Generating analytics data...")
    tiers = ["TIER 1: STALLED VEHICLE", "TIER 2: HIGH PROXIMITY", "TIER 3: CRITICAL IMPACT"]
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, tier TEXT)''')
        for _ in range(100):
            r_time = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("INSERT INTO incidents (timestamp, tier) VALUES (?, ?)", (r_time, random.choice(tiers)))
        conn.commit()

if os.path.exists(DB_PATH):
    inject_mock_data()
    with sqlite3.connect(str(DB_PATH)) as conn:
        df = pd.read_sql_query("SELECT * FROM incidents", conn)
        df.to_csv(BASE_DIR / "crash_analytics.csv", index=False)
        print(f"SUCCESS: Exported {len(df)} rows to 'crash_analytics.csv'.")
else:
    print("ERROR: Database not found. Run 'blackspotter_final.py' first!")