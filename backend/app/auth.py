import sqlite3
from functools import wraps
from flask import session, jsonify

def get_current_user():
    if 'email' not in session:
        return None, None, None

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, role, organization_id FROM users WHERE email = ?', (session['email'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return None, None, None

    return user[0], user[1], user[2]

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return jsonify({'message': 'Unauthorized: No role found in session'}), 401
            
            user_role = session['role']
            if user_role not in allowed_roles:
                return jsonify({'message': f'Unauthorized: Access restricted to {", ".join(allowed_roles)}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator