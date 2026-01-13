
import sqlite3
import bcrypt
import argparse
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def make_super_admin(email, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute(
            'INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
            (email, hashed_password, 'super_admin')
        )
        conn.commit()
        print(f"Successfully created super admin: {email}")
    except sqlite3.IntegrityError:
        print(f"Error: User with email {email} already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a new super admin user.')
    parser.add_argument('email', type=str, help='Email of the super admin')
    parser.add_argument('password', type=str, help='Password for the super admin')
    
    args = parser.parse_args()
    
    make_super_admin(args.email, args.password)
