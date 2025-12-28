import bcrypt
from flask import request, jsonify
from .database import get_db
from .models import User
from .auth import generate_token
from sqlalchemy.orm import Session

def init_routes(app):
    @app.route('/api/signup', methods=['POST'])
    def signup():
        db: Session = next(get_db())
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        organization_id = data.get('organization_id')

        if not all([email, password, organization_id]):
            return jsonify({'message': 'Email, password, and organization ID are required'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            email=email,
            password=hashed_password.decode('utf-8'),
            organization_id=organization_id,
            role='employee'
        )
        db.add(new_user)
        try:
            db.commit()
            return jsonify({'message': 'Signup successful!'}), 201
        except:
            db.rollback()
            return jsonify({'message': 'Email already exists'}), 400

    @app.route('/api/login', methods=['POST'])
    def login():
        db: Session = next(get_db())
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        user = db.query(User).filter(User.email == email).first()

        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'message': 'Invalid email or password'}), 401

        token = generate_token(user.id, user.role)

        return jsonify({'token': token}), 200
