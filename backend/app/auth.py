from functools import wraps
from flask import jsonify, request
import jwt
from datetime import datetime, timedelta

SECRET_KEY = 'your-secret-key' # In a real app, this should be a secure, environment-specific secret

def generate_token(user_id, role):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'sub': user_id,
        'role': role
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(" ")[1]

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401

            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user_role = data['role']
                request.current_user = data
            except:
                return jsonify({'message': 'Token is invalid!'}), 401
            
            if user_role not in allowed_roles:
                return jsonify({'message': f'Unauthorized: Access restricted to {", ".join(allowed_roles)}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
