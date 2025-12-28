from flask import jsonify, session
from app.auth import role_required
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session

def init_user_routes(app):
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_user_profile(user_id):
        db: Session = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'position': user.position
        }), 200
