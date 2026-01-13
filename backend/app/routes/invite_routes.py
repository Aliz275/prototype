import os
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from app.database import db
from app.models import UserInvite

invite_bp = Blueprint("invite", __name__)

FRONTEND_URL = os.getenv("FRONTEND_URL")

@invite_bp.route("/invite", methods=["POST"])
def invite_user():
    if not FRONTEND_URL:
        return jsonify({"error": "FRONTEND_URL not set"}), 500

    data = request.get_json()
    email = data.get("email")
    role = data.get("role")

    if not email or not role:
        return jsonify({"error": "Email and role are required"}), 400

    # 1️⃣ generate secure token
    raw_token = secrets.token_urlsafe(32)

    # 2️⃣ hash token for storage
    token_hash = generate_password_hash(raw_token)

    # 3️⃣ create invite record
    invite = UserInvite(
        email=email,
        role=role,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False
    )

    db.session.add(invite)
    db.session.commit()

    # 4️⃣ build FULL invite link
    invite_link = f"{FRONTEND_URL}/accept-invitation?token={raw_token}"

    # 5️⃣ return link instead of token
    return jsonify({
        "message": "Invitation created",
        "invite_link": invite_link
    }), 201
