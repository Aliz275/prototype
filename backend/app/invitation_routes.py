import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, session
import bcrypt
from app.auth import role_required

# -------------------------
# Helper DB Connection
# -------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# Initialize Invitation Routes
# -------------------------
def init_invitation_routes(app):

    # -------------------------
    # CORS PREFLIGHT (OPTIONS)
    # -------------------------
    @app.route('/api/invitations', methods=['OPTIONS'])
    @app.route('/api/invitations/<int:invitation_id>', methods=['OPTIONS'])
    def invitations_options(invitation_id=None):
        return jsonify({}), 200

    # -------------------------
    # CREATE INVITATION
    # -------------------------
    @app.route('/api/invitations', methods=['POST'])
    @role_required(['super_admin'])
    def create_invitation():
        data = request.get_json()
        email = data.get('email')
        role = data.get('role')
        organization_id = data.get('organization_id')

        if not all([email, role, organization_id]):
            return jsonify({'message': 'Email, role, and organization ID are required'}), 400

        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(days=7)
        created_by = session.get('user_id', 0)

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO invitations
            (email, token, role, organization_id, created_by, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (email, token, role, organization_id, created_by, expires_at))
        conn.commit()
        conn.close()

        invite_link = f"http://localhost:3000/accept-invitation?token={token}"

        return jsonify({
            "message": "Invitation created successfully",
            "token": token,
            "invite_link": invite_link
        }), 201

    # -------------------------
    # GET ALL INVITATIONS
    # -------------------------
    @app.route('/api/invitations', methods=['GET'])
    @role_required(['super_admin'])
    def get_invitations():
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, email, role, organization_id, expires_at, is_used FROM invitations ORDER BY id DESC')
        invitations = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({'invitations': invitations}), 200

    # -------------------------
    # DELETE INVITATION
    # -------------------------
    @app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
    @role_required(['super_admin'])
    def delete_invitation(invitation_id):
        conn = get_db_connection()
        c = conn.cursor()

        # Check if invitation exists
        c.execute('SELECT id FROM invitations WHERE id = ?', (invitation_id,))
        inv = c.fetchone()
        if not inv:
            conn.close()
            return jsonify({'message': 'Invitation not found'}), 404

        # Delete the invitation
        c.execute('DELETE FROM invitations WHERE id = ?', (invitation_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Invitation deleted successfully'}), 200

    # -------------------------
    # VERIFY INVITATION TOKEN
    # -------------------------
    @app.route('/api/invitations/<token>', methods=['GET'])
    def verify_invitation(token):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT email, role, organization_id, expires_at, is_used FROM invitations WHERE token = ?', (token,))
        invitation = c.fetchone()
        conn.close()

        if not invitation:
            return jsonify({'message': 'Invalid token'}), 404

        expires_at = invitation['expires_at']
        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')

        if expires_at < datetime.now():
            return jsonify({'message': 'Token has expired'}), 400

        if invitation['is_used']:
            return jsonify({'message': 'Token has already been used'}), 400

        return jsonify({
            'email': invitation['email'],
            'role': invitation['role'],
            'organization_id': invitation['organization_id']
        }), 200

    # -------------------------
    # REGISTER USER FROM INVITATION
    # -------------------------
    @app.route('/api/register', methods=['POST'])
    def register_from_invitation():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        organization_id = data.get("organization_id")
        token = data.get("token")

        if not all([email, password, role, organization_id, token]):
            return jsonify({"message": "All fields are required"}), 400

        conn = get_db_connection()
        c = conn.cursor()

        # Check invitation
        c.execute("SELECT is_used FROM invitations WHERE token = ?", (token,))
        inv = c.fetchone()
        if not inv:
            conn.close()
            return jsonify({"message": "Invalid invitation token"}), 404
        if inv['is_used']:
            conn.close()
            return jsonify({"message": "Invitation already used"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create user
        c.execute(
            "INSERT INTO users (email, password, role, organization_id) VALUES (?, ?, ?, ?)",
            (email, hashed_password, role, organization_id)
        )

        # Mark invitation as used
        c.execute("UPDATE invitations SET is_used = 1 WHERE token = ?", (token,))
        conn.commit()
        conn.close()

        return jsonify({"message": "User registered successfully"}), 201