#backend/app/user_routes.py

from flask import jsonify, session
from app.auth import role_required
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")


def init_user_routes(app):

    # =========================
    # LIST USERS (FOR MESSAGING)
    # =========================
    @app.route("/api/users", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def list_users():
        org_id = session.get("organization_id")
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT id, email, role
            FROM users
            WHERE organization_id = ?
              AND id != ?
        """, (org_id, user_id))

        users = [
            {"id": u[0], "email": u[1], "role": u[2]}
            for u in c.fetchall()
        ]

        conn.close()
        return jsonify(users), 200


    # =========================
    # GET USER PROFILE
    # =========================
    @app.route("/api/users/<int:user_id>", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def get_user_profile(user_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT u.id, u.email, u.role,
                   e.first_name, e.last_name, e.position
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            WHERE u.id = ?
        """, (user_id,))

        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "id": user[0],
            "email": user[1],
            "role": user[2],
            "first_name": user[3],
            "last_name": user[4],
            "position": user[5],
        }), 200
