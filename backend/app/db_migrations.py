import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def apply_migrations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- Invitations ---
    c.execute('''CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        organization_id INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        is_used INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (created_by) REFERENCES users (id)
    )''')

    conn.commit()
    conn.close()
    print("Migrations applied successfully.")

if __name__ == "__main__":
    apply_migrations()
