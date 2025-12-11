import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def add_status_column_to_submissions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if 'status' column exists
    c.execute("PRAGMA table_info(submissions)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'status' not in columns:
        c.execute("ALTER TABLE submissions ADD COLUMN status TEXT DEFAULT 'pending'")
        print("✅ Column 'status' added to submissions table.")
    else:
        print("ℹ️ Column 'status' already exists, skipping.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_status_column_to_submissions()
