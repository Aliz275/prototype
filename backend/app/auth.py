from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from functools import wraps

from .database import SessionLocal
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


# ===============================
# ROLE-BASED ACCESS DECORATOR
# ===============================
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session or "role" not in session:
                return jsonify({"message": "Unauthorized"}), 401

            if session["role"] not in allowed_roles:
                return jsonify({
                    "message": f"Forbidden: requires {', '.join(allowed_roles)}"
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


# ===============================
# LOGIN ROUTE
# ===============================
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({"message": "Invalid email or password"}), 401

        # 🔐 STORE SESSION
        session.clear()
        session["user_id"] = user.id
        session["email"] = user.email
        session["role"] = user.role

        return jsonify({
            "id": user.id,
            "email": user.email,
            "role": user.role
        }), 200

    finally:
        db.close()
