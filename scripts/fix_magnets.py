import sqlite3
import os

db_path = r'c:\Antigravity\Project\scripts\shop.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET name = 'Магниты' WHERE name = 'Магниты и Бижутерия'")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows")
    conn.close()
else:
    print("Database not found")
