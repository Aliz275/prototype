# backend/app/insert_test_data.py
import sqlite3
import bcrypt
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db_setup import initialize_database

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def insert_test_data():
    initialize_database()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- Create a test organization ---
    c.execute("INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)", (1, "Test Org"))

    # --- Create test users ---
    users = [
        ("admin@test.com", "password123", "org_admin", 1),
        ("manager@test.com", "password123", "team_manager", 1),
        ("employee1@test.com", "password123", "employee", 1),
        ("employee2@test.com", "password123", "employee", 2),
        ("employee3@test.com", "password123", "employee", 2)
    ]

    user_ids = {}

    for email, pwd, role, org_id in users:
        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
        try:
            c.execute(
                "INSERT INTO users (email, password, role, organization_id) VALUES (?, ?, ?, ?)",
                (email, hashed, role, org_id)
            )
            conn.commit()
            user_ids[email] = c.lastrowid
        except sqlite3.IntegrityError:
            # User already exists, fetch their ID
            c.execute("SELECT id FROM users WHERE email = ?", (email,))
            user_ids[email] = c.fetchone()[0]

    # --- Create a test team ---
    # Assume manager id = user_ids["manager@test.com"]
    manager_id = user_ids["manager@test.com"]
    c.execute("INSERT OR IGNORE INTO teams (id, name, organization_id, manager_id) VALUES (?, ?, ?, ?)",
              (1, "Dev Team", 1, manager_id))

    # --- Assign employees to the team ---
    # Employee1 and Employee2
    c.execute("INSERT OR IGNORE INTO team_members (user_id, team_id) VALUES (?, ?)", (user_ids["employee1@test.com"], 1))
    c.execute("INSERT OR IGNORE INTO team_members (user_id, team_id) VALUES (?, ?)", (user_ids["employee2@test.com"], 1))

    # --- Create some assignments ---
    # General assignment
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, is_general)
        VALUES (?, ?, ?, ?, ?)
    """, (1, "General Assignment", "Visible to all employees", user_ids["admin@test.com"], 1))

    # Team assignment (Dev Team)
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, team_id, is_general)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (2, "Team Assignment", "Visible to Dev Team", manager_id, 1, 0))

    # User-specific assignment for employee1@test.com
    employee1_id = user_ids["employee1@test.com"]
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, is_general)
        VALUES (?, ?, ?, ?, ?)
    """, (3, "Personal Assignment", "Visible to employee1@test.com only", user_ids["admin@test.com"], 0))
    c.execute("INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)", (employee1_id, 3))

    # --- Create a test conversation ---
    c.execute("INSERT OR IGNORE INTO conversations (id, name, is_group_chat, created_by_id) VALUES (?, ?, ?, ?)",
              (1, "Test Group Chat", 1, user_ids["manager@test.com"]))
    c.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (1, user_ids["manager@test.com"]))
    c.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (1, user_ids["employee1@test.com"]))
    c.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (1, user_ids["employee2@test.com"]))
    
    # --- Create test messages ---
    c.execute("INSERT OR IGNORE INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
              (1, user_ids["manager@test.com"], "Hello team!"))
    c.execute("INSERT OR IGNORE INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
              (1, user_ids["employee1@test.com"], "Hello manager!"))
    c.execute("INSERT OR IGNORE INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
                (1, user_ids["employee2@test.com"], "Hello!"))

    conn.commit()
    conn.close()

    print("Test data inserted successfully!\n")
    print("User IDs:")
    for email, uid in user_ids.items():
        print(f"{email}: {uid}")

    return user_ids

if __name__ == "__main__":
    insert_test_data()
