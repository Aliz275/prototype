import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # enforce foreign key constraints
    c = conn.cursor()

    # --- Core Tables ---
    c.execute('''CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'employee',
        organization_id INTEGER,
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        organization_id INTEGER NOT NULL,
        manager_id INTEGER,
        FOREIGN KEY (organization_id) REFERENCES organizations (id),
        FOREIGN KEY (manager_id) REFERENCES users (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS team_members (
        user_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, team_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (team_id) REFERENCES teams (id)
    )''')

    # --- Employee & Assignment Tables ---
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        email TEXT UNIQUE,
        position TEXT,
        department TEXT,
        phone TEXT,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        is_general INTEGER NOT NULL DEFAULT 1,
        team_id INTEGER,
        created_by_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES teams (id),
        FOREIGN KEY (created_by_id) REFERENCES users (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_assignments (
        user_id INTEGER NOT NULL,
        assignment_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, assignment_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (assignment_id) REFERENCES assignments (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assignment_id) REFERENCES assignments (id),
        FOREIGN KEY (employee_id) REFERENCES users (id)
    )''')

    # --- Messaging Tables ---
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        is_group_chat INTEGER NOT NULL DEFAULT 0,
        created_by_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_id) REFERENCES users (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS conversation_participants (
        user_id INTEGER NOT NULL,
        conversation_id INTEGER NOT NULL,
        last_read_timestamp TIMESTAMP,
        PRIMARY KEY (user_id, conversation_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id),
        FOREIGN KEY (sender_id) REFERENCES users (id)
    )''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
