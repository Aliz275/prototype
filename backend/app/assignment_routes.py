# backend/app/assignment_routes.py
import sqlite3
from flask import request, jsonify, session
import os
from .auth import role_required
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def _connect():
    return sqlite3.connect(DB_PATH)

def init_assignment_routes(app):
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ---------------- CREATE ASSIGNMENT ----------------
    @app.route('/api/assignments', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def create_assignment():
        data = request.get_json() or {}
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        employee_ids = data.get('employee_ids', []) or []
        team_id = data.get('team_id', None)

        if not title:
            return jsonify({'message': 'Title is required'}), 400

        if due_date:
            try:
                due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return jsonify({'message': 'Invalid due date format. Use ISO 8601 format.'}), 400

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        user_id, user_role = user[0], user[1]

        # team manager validation (if team_id present)
        if team_id and user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (team_id,))
            manager = c.fetchone()
            if not manager or manager[0] != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403

        is_general = 1 if (not employee_ids and not team_id) else 0

        c.execute('INSERT INTO assignments (title, description, created_by_id, due_date, is_general, team_id) VALUES (?, ?, ?, ?, ?, ?)',
                  (title, description, user_id, due_date, is_general, team_id))
        assignment_id = c.lastrowid

        if employee_ids:
            for emp_id in employee_ids:
                c.execute('INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment created successfully!', 'assignment_id': assignment_id}), 201

    # ---------------- GET ALL ASSIGNMENTS ----------------
    @app.route('/api/assignments', methods=['GET'])
    def get_assignments():
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404

        user_id, role = user[0], user[1]

        if role == 'org_admin':
            c.execute('SELECT * FROM assignments')
        elif role == 'team_manager':
            c.execute('''
                SELECT DISTINCT a.* FROM assignments a
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE a.is_general = 1 OR t.manager_id = ?
            ''', (user_id,))
        else:
            c.execute('''
                SELECT DISTINCT a.* FROM assignments a
                LEFT JOIN user_assignments ua ON a.id = ua.assignment_id
                LEFT JOIN team_members tm ON a.team_id = tm.team_id
                WHERE a.is_general = 1 OR ua.user_id = ? OR tm.user_id = ?
            ''', (user_id, user_id))
        
        assignments = c.fetchall()
        assignments_list = []
        for a in assignments:
            aid = a[0]
            c.execute('SELECT user_id FROM user_assignments WHERE assignment_id = ?', (aid,))
            employee_ids = [row[0] for row in c.fetchall()]
            assignments_list.append({
                'id': aid,
                'title': a[1],
                'description': a[2],
                'due_date': a[3],
                'is_general': a[4],
                'team_id': a[5],
                'created_by_id': a[6],
                'employee_ids': employee_ids
            })

        conn.close()
        return jsonify({'assignments': assignments_list}), 200

    # ---------------- GET SINGLE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
    def get_assignment(assignment_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        c.execute('SELECT * FROM assignments WHERE id = ?', (assignment_id,))
        assignment = c.fetchone()

        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404
        
        c.execute('SELECT user_id FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        employee_ids = [row[0] for row in c.fetchall()]

        conn.close()
        return jsonify({'assignment': {
            'id': assignment[0],
            'title': assignment[1],
            'description': assignment[2],
            'due_date': assignment[3],
            'is_general': assignment[4],
            'team_id': assignment[5],
            'created_by_id': assignment[6],
            'employee_ids': employee_ids
        }}), 200

    # ---------------- UPDATE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def update_assignment(assignment_id):
        data = request.get_json() or {}
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        employee_ids = data.get('employee_ids', []) or []
        team_id = data.get('team_id', None)

        if due_date:
            try:
                due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return jsonify({'message': 'Invalid due date format. Use ISO 8601 format.'}), 400

        conn = _connect()
        c = conn.cursor()
        c.execute('UPDATE assignments SET title = ?, description = ?, due_date = ?, team_id = ? WHERE id = ?',
                  (title, description, due_date, team_id, assignment_id))

        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        if employee_ids:
            for emp_id in employee_ids:
                c.execute('INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment updated successfully!'}), 200

    # ---------------- DELETE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
    @role_required(['org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        conn = _connect()
        c = conn.cursor()
        c.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment deleted successfully!'}), 200

    # ---------------- EXTEND DUE DATE ----------------
    @app.route('/api/assignments/<int:assignment_id>/extend', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def extend_due_date(assignment_id):
        data = request.get_json()
        new_due_date = data.get('due_date')

        if not new_due_date:
            return jsonify({'message': 'New due date is required'}), 400

        try:
            new_due_date = datetime.fromisoformat(new_due_date)
        except ValueError:
            return jsonify({'message': 'Invalid due date format. Use ISO 8601 format.'}), 400

        conn = _connect()
        c = conn.cursor()
        c.execute('UPDATE assignments SET due_date = ? WHERE id = ?', (new_due_date, assignment_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Due date extended successfully!'}), 200

    # ---------------- RE-ASSIGN ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>/reassign', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def reassign_assignment(assignment_id):
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        team_id = data.get('team_id')

        if not employee_ids and not team_id:
            return jsonify({'message': 'Employee IDs or a team ID is required'}), 400

        conn = _connect()
        c = conn.cursor()

        if employee_ids:
            # Clear existing assignments before re-assigning
            c.execute("DELETE FROM user_assignments WHERE assignment_id = ?", (assignment_id,))
            for emp_id in employee_ids:
                c.execute('INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        if team_id:
            c.execute('UPDATE assignments SET team_id = ? WHERE id = ?', (team_id, assignment_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Assignment re-assigned successfully!'}), 200
