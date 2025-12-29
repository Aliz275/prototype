import secrets
from datetime import datetime, timedelta
from flask import request, jsonify
from sqlalchemy.orm import Session
from .database import get_db
from .models import Invitation, User
from .auth import role_required

def init_invitation_routes(app):
    @app.route('/api/invitations', methods=['POST'])
    @role_required(['super_admin'])
    def create_invitation():
        db: Session = next(get_db())
        data = request.get_json()
        email = data.get('email')
        role = data.get('role')
        organization_id = data.get('organization_id')

        if not all([email, role, organization_id]):
            return jsonify({'message': 'Email, role, and organization ID are required'}), 400

        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(days=7)
        
        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        new_invitation = Invitation(
            email=email,
            token=token,
            role=role,
            organization_id=organization_id,
            created_by=user.id,
            expires_at=expires_at
        )
        db.add(new_invitation)
        db.commit()

        return jsonify({'message': 'Invitation created successfully', 'token': token}), 201

    @app.route('/api/invitations', methods=['GET'])
    @role_required(['super_admin'])
    def get_invitations():
        db: Session = next(get_db())
        invitations = db.query(Invitation).all()
        invitations_list = []
        for inv in invitations:
            invitations_list.append({
                'id': inv.id,
                'email': inv.email,
                'role': inv.role,
                'organization_id': inv.organization_id,
                'expires_at': inv.expires_at.isoformat(),
                'is_used': inv.is_used
            })
        return jsonify(invitations_list), 200

    @app.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
    @role_required(['super_admin'])
    def delete_invitation(invitation_id):
        db: Session = next(get_db())
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        if not invitation:
            return jsonify({'message': 'Invitation not found'}), 404
        
        db.delete(invitation)
        db.commit()

        return jsonify({'message': 'Invitation deleted successfully'}), 200

    @app.route('/api/invitations/<token>', methods=['GET'])
    def verify_invitation(token):
        db: Session = next(get_db())
        invitation = db.query(Invitation).filter(Invitation.token == token).first()

        if not invitation:
            return jsonify({'message': 'Invalid token'}), 404

        if invitation.expires_at < datetime.now():
            return jsonify({'message': 'Token has expired'}), 400
        
        if invitation.is_used:
            return jsonify({'message': 'Token has already been used'}), 400

        return jsonify({
            'email': invitation.email,
            'role': invitation.role,
            'organization_id': invitation.organization_id
        }), 200
