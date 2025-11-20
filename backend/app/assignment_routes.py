import sqlite3
from flask import request, jsonify, session
import os
from werkzeug.utils import secure_filename
from .auth import role_required

UPLOAD_FOLDER = 'backend/uploads'

def init_assignment_routes(app):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ---------------- CREATE ASSIGNMENT ----------------
    @app.route('/api/assignments', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def create_assignment():
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        employee_ids = data.get('employee_ids', [])
        team_id = data.get('team_id')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session['email'],))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        user_id, user_role = user[0], user[1]

        # Team manager check
        if team_id and user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (team_id,))
            manager = c.fetchone()
            if not manager or manager[0] != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403

        is_general = not employee_ids and not team_id

        c.execute('INSERT INTO assignments (title, description, created_by_id, due_date, is_general, team_id) VALUES (?, ?, ?, ?, ?, ?)',
                  (title, description, user_id, due_date, is_general, team_id))
        assignment_id = c.lastrowid

        # Insert employee assignments if any
        if employee_ids:
            for emp_id in employee_ids:
                c.execute('INSERT INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment created successfully!'}), 201

    # ---------------- GET ALL ASSIGNMENTS ----------------
    @app.route('/api/assignments', methods=['GET'])
    def get_assignments():
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session['email'],))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        user_id, role = user[0], user[1]

        # Fetch assignments based on role
        if role == 'org_admin':
            c.execute('SELECT * FROM assignments')
        elif role == 'team_manager':
            c.execute('''
                SELECT a.* FROM assignments a
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE a.is_general = 1 OR t.manager_id = ?
            ''', (user_id,))
        else:  # employee
            c.execute('''
                SELECT a.* FROM assignments a
                LEFT JOIN user_assignments ua ON a.id = ua.assignment_id
                LEFT JOIN team_members tm ON a.team_id = tm.team_id
                WHERE a.is_general = 1 OR ua.user_id = ? OR tm.user_id = ?
            ''', (user_id, user_id))

        assignments = c.fetchall()
        conn.close()

        assignments_list = []
        for a in assignments:
            assignments_list.append({
                'id': a[0],
                'title': a[1],
                'description': a[2],
                'due_date': a[3],
                'is_general': a[4],
                'team_id': a[5]
            })
        return jsonify({'assignments': assignments_list}), 200

    # ---------------- GET SINGLE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
    def get_assignment(assignment_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session['email'],))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        user_id, role = user[0], user[1]

        c.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,))
        assignment = c.fetchone()
        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404

        is_general = assignment[4]
        team_id = assignment[5]

        # Employee access check
        if role == 'employee':
            c.execute('SELECT 1 FROM user_assignments WHERE user_id = ? AND assignment_id = ?', (user_id, assignment_id))
            ua = c.fetchone()
            c.execute('SELECT 1 FROM team_members WHERE user_id = ? AND team_id = ?', (user_id, team_id))
            tm = c.fetchone()
            if not is_general and not ua and not tm:
                conn.close()
                return jsonify({'message': 'Unauthorized: Cannot access this assignment'}), 403

        conn.close()
        return jsonify({'assignment': {
            'id': assignment[0],
            'title': assignment[1],
            'description': assignment[2],
            'due_date': assignment[3],
            'is_general': assignment[4],
            'team_id': assignment[5]
        }}), 200

    # ---------------- UPDATE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def update_assignment(assignment_id):
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        employee_ids = data.get('employee_ids', [])
        team_id = data.get('team_id', None)

        is_general = not employee_ids and not team_id

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE assignments SET title = ?, description = ?, due_date = ?, is_general = ?, team_id = ? WHERE id = ?',
                  (title, description, due_date, is_general, team_id, assignment_id))

        # Clear old user assignments
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        if employee_ids:
            for emp_id in employee_ids:
                c.execute('INSERT INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment updated successfully!'}), 200

    # ---------------- DELETE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
    @role_required(['org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Remove submissions first
        c.execute('DELETE FROM submissions WHERE assignment_id = ?', (assignment_id,))
        # Remove user_assignments
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        # Remove assignment
        c.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment deleted successfully!'}), 200
