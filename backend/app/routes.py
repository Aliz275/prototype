# backend/app/routes.py
import sqlite3
import bcrypt
from flask import request, jsonify, session

def init_routes(app):
    @app.route('/api/signup', methods=['POST'])
    def signup():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        organization_id = data.get('organization_id')  # Users must join an organization

        if not all([email, password, organization_id]):
            return jsonify({'message': 'Email, password, and organization ID are required'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            # By default, new users are 'employees'. Admins can change this later.
            c.execute(
                'INSERT INTO users (email, password, organization_id, role) VALUES (?, ?, ?, ?)',
                (email, hashed_password, organization_id, 'employee')
            )
            conn.commit()
            conn.close()
            return jsonify({'message': 'Signup successful!'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Email already exists'}), 400

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, password, role, organization_id FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401

        user_id, hashed_password, role, organization_id = user

        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return jsonify({'message': 'Invalid email or password'}), 401

        # Save user info in session
        session['user_id'] = user_id
        session['email'] = email
        session['role'] = role
        session['organization_id'] = organization_id
        session['is_admin'] = role in ['org_admin', 'super_admin']

        return jsonify({
            'id': user_id,
            'email': email,
            'role': role,
            'organization_id': organization_id
        }), 200

    @app.route('/api/user', methods=['GET'])
    def get_current_user():
        if 'email' in session:
            return jsonify({
                'id': session.get('user_id'),
                'email': session['email'],
                'role': session.get('role'),
                'organization_id': session.get('organization_id'),
                'is_admin': session.get('is_admin', False)
            })
        else:
            return jsonify({'email': None, 'is_admin': False})

    @app.route('/api/employees', methods=['GET'])
    def get_employees():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM employees")
        employees = c.fetchall()
        conn.close()
        return jsonify(employees), 200

    @app.route('/api/employees', methods=['POST'])
    def add_employee():
        if not session.get('is_admin'):
            return jsonify({'message': 'Unauthorized: Admins only'}), 403

        data = request.get_json()
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        position = data.get('position')
        department = data.get('department')
        phone = data.get('phone')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO employees (first_name, last_name, email, position, department, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, position, department, phone))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Employee added successfully!'}), 201
