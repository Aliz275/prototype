import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, session
from app.auth import role_required
from app.email_service import send_invitation_email

def init_invitation_routes(app):

    # ---------------- CREATE INVITATION ----------------
    @app.route('/api/invitations', methods=['POST', 'OPTIONS'])
    @role_required(['super_admin'])
    def create_invitation():
        # Handle preflight CORS
        if request.method == 'OPTIONS':
            return jsonify({}), 200

        data = request.get_json()
        email = data.get('email')
        role = data.get('role')
        organization_id = data.get('organization_id')

        if not all([email, role, organization_id]):
            return jsonify({'message': 'Email, role, and organization ID are required'}), 400

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        created_by = session.get('user_id', 0)  # fallback

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO invitations 
            (email, token, role, organization_id, created_by, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (email, token, role, organization_id, created_by, expires_at))
        conn.commit()
        conn.close()

        invite_link = f"http://localhost:3000/accept-invitation?token={token}"

        # Send email
        send_invitation_email(email, invite_link)

        return jsonify({
            "message": "Invitation created successfully",
            "token": token,
            "invite_link": invite_link
        }), 201

    # ---------------- GET ALL INVITATIONS ----------------
    @app.route('/api/invitations', methods=['GET'])
    @role_required(['super_admin'])
    def get_invitations():
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT id, email, role, organization_id, expires_at, is_used
            FROM invitations
            ORDER BY id DESC
        """)
        rows = c.fetchall()
        conn.close()
        return jsonify({'invitations': [dict(row) for row in rows]}), 200

    # ---------------- DELETE INVITATION ----------------
    @app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
    @role_required(['super_admin'])
    def delete_invitation(invitation_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM invitations WHERE id = ?', (invitation_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Invitation deleted'}), 200

    # ---------------- VERIFY INVITATION TOKEN ----------------
    @app.route('/api/invitations/<token>', methods=['GET'])
    def verify_invitation(token):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            SELECT email, role, organization_id, expires_at, is_used
            FROM invitations WHERE token = ?
        """, (token,))
        invitation = c.fetchone()
        conn.close()

        if not invitation:
            return jsonify({'message': 'Invalid token'}), 404

        email, role, organization_id, expires_at, is_used = invitation

        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')

        if expires_at < datetime.now():
            return jsonify({'message': 'Token expired'}), 400

        if is_used:
            return jsonify({'message': 'Token already used'}), 400

        return jsonify({
            'email': email,
            'role': role,
            'organization_id': organization_id
        }), 200

    # ---------------- REGISTER FROM INVITATION ----------------
    @app.route('/api/register', methods=['POST'])
    def register_from_invitation():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        organization_id = data.get("organization_id")
        token = data.get("token")

        if not all([email, password, role, organization_id, token]):
            return jsonify({"message": "Missing fields"}), 400

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT is_used FROM invitations WHERE token = ?", (token,))
        inv = c.fetchone()

        if not inv:
            conn.close()
            return jsonify({"message": "Invalid token"}), 404

        if inv[0]:
            conn.close()
            return jsonify({"message": "Invitation already used"}), 400

        # ⚠️ Hash password in production apps
        c.execute("""
            INSERT INTO users (email, password, role, organization_id)
            VALUES (?, ?, ?, ?)
        """, (email, password, role, organization_id))
        c.execute("UPDATE invitations SET is_used = 1 WHERE token = ?", (token,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Account created successfully"}), 201
