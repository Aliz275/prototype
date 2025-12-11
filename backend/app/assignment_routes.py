# backend/app/assignment_routes.py
import sqlite3
from flask import request, jsonify, session
import os
from .auth import role_required

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def _connect():
    return sqlite3.connect(DB_PATH)

def init_assignment_routes(app):
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    def _get_employee_ids_for_assignment(c, assignment_id):
        c.execute('SELECT user_id FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        rows = c.fetchall()
        return [r[0] for r in rows]

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

        # if manager assigns to individual employees, optionally check membership (omitted here for brevity)

        is_general = 1 if (not employee_ids and not team_id) else 0

        c.execute('INSERT INTO assignments (title, description, created_by_id, due_date, is_general, team_id) VALUES (?, ?, ?, ?, ?, ?)',
                  (title, description, user_id, due_date, is_general, team_id))
        assignment_id = c.lastrowid

        if employee_ids:
            for emp_id in employee_ids:
                try:
                    emp_int = int(emp_id)
                except Exception:
                    continue
                # ensure user exists
                c.execute('SELECT id FROM users WHERE id = ?', (emp_int,))
                if not c.fetchone():
                    conn.rollback()
                    conn.close()
                    return jsonify({'message': f'Employee id {emp_int} not found'}), 400
                c.execute('INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_int, assignment_id))

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
            assignments = c.fetchall()
        elif role == 'team_manager':
            c.execute('''
                SELECT DISTINCT a.* FROM assignments a
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE a.is_general = 1 OR t.manager_id = ?
            ''', (user_id,))
            assignments = c.fetchall()
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
            employee_ids = _get_employee_ids_for_assignment(c, aid)
            assignments_list.append({
                'id': aid,
                'title': a[1],
                'description': a[2],
                'due_date': a[3],
                'is_general': a[4],
                'team_id': a[5],
                'created_by_id': a[6] if len(a) > 6 else None,
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
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
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

        # include employee_ids
        employee_ids = _get_employee_ids_for_assignment(c, assignment_id)

        conn.close()
        return jsonify({'assignment': {
            'id': assignment[0],
            'title': assignment[1],
            'description': assignment[2],
            'due_date': assignment[3],
            'is_general': assignment[4],
            'team_id': assignment[5],
            'created_by_id': assignment[6] if len(assignment) > 6 else None,
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

        is_general = 1 if (not employee_ids and not team_id) else 0

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT created_by_id, team_id FROM assignments WHERE id = ?', (assignment_id,))
        existing = c.fetchone()
        if not existing:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404

        created_by_id, existing_team_id = existing[0], existing[1]

        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, user_role = user[0], user[1]

        if user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (existing_team_id,))
            t = c.fetchone()
            manager_id = t[0] if t else None
            if created_by_id != user_id and manager_id != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: cannot update this assignment'}, 403)

            if team_id:
                c.execute('SELECT manager_id FROM teams WHERE id = ?', (team_id,))
                m = c.fetchone()
                if not m or m[0] != user_id:
                    conn.close()
                    return jsonify({'message': 'Unauthorized: cannot assign to a team you do not manage'}, 403)

        c.execute('UPDATE assignments SET title = ?, description = ?, due_date = ?, is_general = ?, team_id = ? WHERE id = ?',
                  (title, description, due_date, is_general, team_id, assignment_id))

        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        if employee_ids:
            for emp_id in employee_ids:
                try:
                    emp_int = int(emp_id)
                except Exception:
                    continue
                c.execute('SELECT id FROM users WHERE id = ?', (emp_int,))
                if not c.fetchone():
                    conn.rollback()
                    conn.close()
                    return jsonify({'message': f'Employee id {emp_int} not found'}), 400
                c.execute('INSERT OR IGNORE INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_int, assignment_id))

        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment updated successfully!'}), 200

    # ---------------- DELETE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
    @role_required(['org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT created_by_id, team_id FROM assignments WHERE id = ?', (assignment_id,))
        assignment = c.fetchone()
        if not assignment:
            conn.close()
            return jsonify({'message': 'Assignment not found'}), 404

        created_by_id, assignment_team_id = assignment[0], assignment[1]

        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, user_role = user[0], user[1]

        if user_role == 'team_manager':
            c.execute('SELECT manager_id FROM teams WHERE id = ?', (assignment_team_id,))
            t = c.fetchone()
            manager_id = t[0] if t else None
            if created_by_id != user_id and manager_id != user_id:
                conn.close()
                return jsonify({'message': 'Unauthorized: cannot delete this assignment'}, 403)

        c.execute('DELETE FROM submissions WHERE assignment_id = ?', (assignment_id,))
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        c.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Assignment deleted successfully!'}), 200
