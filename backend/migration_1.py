import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add last_message_at to conversations table
    try:
        c.execute("ALTER TABLE conversations ADD COLUMN last_message_at DATETIME")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column last_message_at already exists in conversations table.")
        else:
            raise

    # Create unread_messages table
    c.execute("""
        CREATE TABLE IF NOT EXISTS unread_messages (
            user_id INTEGER NOT NULL,
            conversation_id INTEGER NOT NULL,
            unread_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, conversation_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Migration 1 applied successfully.")

if __name__ == "__main__":
    migrate()
