# backend/app/assignment_routes.py
import sqlite3
from flask import request, jsonify, session
import os
from .auth import role_required, get_current_user
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
    @role_required(['super_admin', 'org_admin', 'team_manager'])
    def create_assignment():
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

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

        if user_role == 'org_admin':
            # Org admin can't assign to a team, only to employees in their org
            if team_id:
                c.execute('SELECT organization_id FROM teams WHERE id = ?', (team_id,))
                team_org = c.fetchone()
                if not team_org or team_org[0] != user_organization_id:
                    conn.close()
                    return jsonify({'message': 'Unauthorized: You can only assign to teams in your own organization'}), 403
            for emp_id in employee_ids:
                c.execute('SELECT organization_id FROM users WHERE id = ?', (emp_id,))
                emp_org = c.fetchone()
                if not emp_org or emp_org[0] != user_organization_id:
                    conn.close()
                    return jsonify({'message': f'Unauthorized: User {emp_id} is not in your organization'}), 403
        
        elif user_role == 'team_manager':
            c.execute('SELECT organization_id, manager_id FROM teams WHERE id = ?', (team_id,))
            team_info = c.fetchone()
            if not team_info or team_info[1] != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403
            
            # Check if all employees are in the manager's team
            for emp_id in employee_ids:
                c.execute('SELECT team_id FROM team_members WHERE user_id = ? AND team_id = ?', (emp_id, team_id))
                member = c.fetchone()
                if not member:
                    conn.close()
                    return jsonify({'message': f'Unauthorized: User {emp_id} is not in your team'}), 403

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
    @role_required(['super_admin', 'org_admin', 'team_manager', 'employee'])
    def get_assignments():
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        if user_role == 'super_admin':
             c.execute('SELECT a.* FROM assignments a')
        elif user_role == 'org_admin':
            c.execute('''
                SELECT a.* FROM assignments a
                JOIN users u ON a.created_by_id = u.id
                WHERE u.organization_id = ?
            ''', (user_organization_id,))
        elif user_role == 'team_manager':
            c.execute('''
                SELECT DISTINCT a.* FROM assignments a
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE t.manager_id = ? OR a.is_general = 1
            ''', (user_id,))
        else: # employee
            c.execute('''
                SELECT DISTINCT a.* FROM assignments a
                LEFT JOIN user_assignments ua ON a.id = ua.assignment_id
                LEFT JOIN team_members tm ON a.team_id = tm.team_id
                WHERE ua.user_id = ? OR tm.user_id = ? OR a.is_general = 1
            ''', (user_id, user_id))
        
        assignments = c.fetchall()
        assignments_list = []
        for a in assignments:
            aid = a[0]
            c.execute('SELECT user_id FROM user_assignments WHERE assignment_id = ?', (aid,))
            employee_ids = [row[0] for row in c.fetchall()]
            assignments_list.append({
                'id': aid, 'title': a[1], 'description': a[2], 'due_date': a[3],
                'is_general': a[4], 'team_id': a[5], 'created_by_id': a[6],
                'employee_ids': employee_ids
            })

        conn.close()
        return jsonify({'assignments': assignments_list}), 200

    # ---------------- GET SINGLE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
    @role_required(['super_admin', 'org_admin', 'team_manager', 'employee'])
    def get_assignment(assignment_id):
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        c.execute('SELECT a.*, u.organization_id FROM assignments a JOIN users u ON a.created_by_id = u.id WHERE a.id = ?', (assignment_id,))
        assignment = c.fetchone()

        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404
        
        if user_role != 'super_admin' and assignment[7] != user_organization_id:
            conn.close()
            return jsonify({'message': 'Unauthorized: You can only view assignments in your own organization'}), 403

        c.execute('SELECT user_id FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        employee_ids = [row[0] for row in c.fetchall()]

        conn.close()
        return jsonify({'assignment': {
            'id': assignment[0], 'title': assignment[1], 'description': assignment[2],
            'due_date': assignment[3], 'is_general': assignment[4], 'team_id': assignment[5],
            'created_by_id': assignment[6], 'employee_ids': employee_ids
        }}), 200

    # ---------------- UPDATE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
    @role_required(['super_admin', 'org_admin', 'team_manager'])
    def update_assignment(assignment_id):
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

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

        c.execute('SELECT a.*, u.organization_id FROM assignments a JOIN users u ON a.created_by_id = u.id WHERE a.id = ?', (assignment_id,))
        assignment = c.fetchone()
        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404

        if user_role == 'org_admin' and assignment[7] != user_organization_id:
            conn.close()
            return jsonify({'message': 'Unauthorized: Not in your organization'}), 403
        elif user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (assignment[5],))
            manager = c.fetchone()
            if not manager or manager[0] != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403

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
    @role_required(['super_admin', 'org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        c.execute('SELECT a.*, u.organization_id FROM assignments a JOIN users u ON a.created_by_id = u.id WHERE a.id = ?', (assignment_id,))
        assignment = c.fetchone()
        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404

        if user_role == 'org_admin' and assignment[7] != user_organization_id:
            conn.close()
            return jsonify({'message': 'Unauthorized: Not in your organization'}), 403
        elif user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (assignment[5],))
            manager = c.fetchone()
            if not manager or manager[0] != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403

        c.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment deleted successfully!'}), 200