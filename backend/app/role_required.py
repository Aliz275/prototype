from functools import wraps
from flask import session, jsonify

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role not in roles:
                return jsonify({"message": "Access denied"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
