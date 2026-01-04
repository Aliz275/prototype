
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import request, jsonify, session
from app.auth import role_required

def init_invitation_routes(app):
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
        created_by = session.get('user_id')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            'INSERT INTO invitations (email, token, role, organization_id, created_by, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
            (email, token, role, organization_id, created_by, expires_at)
        )
        conn.commit()
        conn.close()

        return jsonify({'message': 'Invitation created successfully', 'token': token}), 201

    @app.route('/api/invitations', methods=['GET'])
    @role_required(['super_admin'])
    def get_invitations():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, email, role, organization_id, expires_at, is_used FROM invitations')
        invitations = c.fetchall()
        conn.close()

        return jsonify(invitations), 200

    @app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
    @role_required(['super_admin'])
    def delete_invitation(invitation_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM invitations WHERE id = ?', (invitation_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Invitation deleted successfully'}), 200

    @app.route('/api/invitations/<token>', methods=['GET'])
    def verify_invitation(token):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT email, role, organization_id, expires_at, is_used FROM invitations WHERE token = ?', (token,))
        invitation = c.fetchone()
        conn.close()

        if not invitation:
            return jsonify({'message': 'Invalid token'}), 404

        email, role, organization_id, expires_at, is_used = invitation
        
        from datetime import datetime
        if datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f') < datetime.now():
            return jsonify({'message': 'Token has expired'}), 400
        
        if is_used:
            return jsonify({'message': 'Token has already been used'}), 400

        return jsonify({
            'email': email,
            'role': role,
            'organization_id': organization_id
        }), 200
