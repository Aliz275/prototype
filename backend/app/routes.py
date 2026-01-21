# backend/app/routes.py

import sqlite3
import bcrypt
from flask import request, jsonify, session
from datetime import datetime
from marshmallow import ValidationError
from .schemas import SignupSchema, LoginSchema, EmployeeSchema

DB_PATH = "database.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_routes(app):

    # =========================
    # AUTH
    # =========================
    @app.route('/api/signup', methods=['POST'])
    def signup():
        try:
            data = SignupSchema().load(request.get_json())
        except ValidationError as err:
            return jsonify(err.messages), 400

        password = data.get('password')
        token = data.get('token')

        conn = get_db()
        c = conn.cursor()

        c.execute(
            '''
            SELECT email, role, organization_id, expires_at, is_used
            FROM invitations
            WHERE token = ?
            ''',
            (token,)
        )
        invitation = c.fetchone()

        if not invitation:
            conn.close()
            return jsonify({'message': 'Invalid token'}), 404

        if invitation['is_used']:
            conn.close()
            return jsonify({'message': 'Token already used'}), 400

        if datetime.strptime(
            invitation['expires_at'], '%Y-%m-%d %H:%M:%S.%f'
        ) < datetime.now():
            conn.close()
            return jsonify({'message': 'Token expired'}), 400

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            c.execute(
                '''
                INSERT INTO users (email, password, role, organization_id)
                VALUES (?, ?, ?, ?)
                ''',
                (
                    invitation['email'],
                    hashed_password,
                    invitation['role'],
                    invitation['organization_id']
                )
            )
            c.execute(
                'UPDATE invitations SET is_used = 1 WHERE token = ?',
                (token,)
            )
            conn.commit()
            conn.close()
            return jsonify({'message': 'Signup successful'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'message': 'Email already exists'}), 400

    # =========================
    # LOGIN
    # =========================
    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = LoginSchema().load(request.get_json())
        except ValidationError as err:
            return jsonify(err.messages), 400

        conn = get_db()
        c = conn.cursor()
        c.execute(
            '''
            SELECT id, email, password, role, organization_id
            FROM users
            WHERE email = ?
            ''',
            (data['email'],)
        )
        user = c.fetchone()
        conn.close()

        if not user or not bcrypt.checkpw(
            data['password'].encode(), user['password']
        ):
            return jsonify({'message': 'Invalid credentials'}), 401

        session.update({
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'organization_id': user['organization_id'],
            'is_admin': user['role'] in ['org_admin', 'super_admin']
        })

        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'organization_id': user['organization_id']
        }), 200

    # =========================
    # CURRENT USER
    # =========================
    @app.route('/api/user', methods=['GET'])
    def get_current_user():
        if 'user_id' not in session:
            return jsonify({'user': None}), 401

        return jsonify({
            'id': session['user_id'],
            'email': session['email'],
            'role': session['role'],
            'organization_id': session['organization_id'],
            'is_admin': session['is_admin']
        })

    # =========================
    # EMPLOYEES (ADMIN ONLY)
    # =========================
    @app.route('/api/employees', methods=['GET'])
    def get_employees():
        if not session.get('is_admin'):
            return jsonify({'message': 'Admins only'}), 403

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM employees")
        rows = c.fetchall()
        conn.close()

        return jsonify([dict(r) for r in rows])

    @app.route('/api/employees', methods=['POST'])
    def add_employee():
        if not session.get('is_admin'):
            return jsonify({'message': 'Admins only'}), 403

        try:
            data = EmployeeSchema().load(request.get_json())
        except ValidationError as err:
            return jsonify(err.messages), 400

        conn = get_db()
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO employees
            (first_name, last_name, email, position, department, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                data['first_name'],
                data.get('last_name'),
                data['email'],
                data.get('position'),
                data.get('department'),
                data.get('phone')
            )
        )
        conn.commit()
        conn.close()

        return jsonify({'message': 'Employee added'}), 201
