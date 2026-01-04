from functools import wraps
from flask import session, jsonify

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
