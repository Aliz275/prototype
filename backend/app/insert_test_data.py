import sqlite3
import bcrypt

def insert_test_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # --- Create a test organization ---
    c.execute("INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)", (1, "Test Org"))

    # --- Create test users ---
    users = [
        ("admin@test.com", "password123", "org_admin", 1),
        ("manager@test.com", "password123", "team_manager", 1),
        ("employee@test.com", "password123", "employee", 1),
        ("employee2@test.com", "password123", "employee", 1)
    ]

    for email, pwd, role, org_id in users:
        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT OR IGNORE INTO users (email, password, role, organization_id) VALUES (?, ?, ?, ?)",
                  (email, hashed, role, org_id))

    # --- Create a test team ---
    # Assume manager id = 2 (manager@test.com)
    c.execute("INSERT OR IGNORE INTO teams (id, name, organization_id, manager_id) VALUES (?, ?, ?, ?)",
              (1, "Dev Team", 1, 2))

    # --- Assign employees to the team ---
    # Employee id 3 and 4
    c.execute("INSERT OR IGNORE INTO team_members (user_id, team_id) VALUES (?, ?)", (3, 1))
    c.execute("INSERT OR IGNORE INTO team_members (user_id, team_id) VALUES (?, ?)", (4, 1))

    # --- Create some assignments ---
    # General assignment
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, is_general)
        VALUES (?, ?, ?, ?, ?)
    """, (1, "General Assignment", "Visible to all employees", 1, 1))

    # Team assignment (Dev Team)
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, team_id, is_general)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (2, "Team Assignment", "Visible to Dev Team", 2, 1, 0))

    # User-specific assignment for employee@test.com (id=3)
    c.execute("""
        INSERT OR IGNORE INTO assignments (id, title, description, created_by_id, is_general)
        VALUES (?, ?, ?, ?, ?)
    """, (3, "Personal Assignment", "Visible to employee@test.com only", 1, 0))
    c.execute("INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)", (3, 3))

    conn.commit()
    conn.close()
    print("Test data inserted successfully!")

if __name__ == "__main__":
    insert_test_data()
