from functools import wraps
from flask import session, jsonify

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if not role:
                return jsonify({"message": "Unauthorized"}), 401

            if role not in allowed_roles:
                return jsonify({"message": "Forbidden"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
