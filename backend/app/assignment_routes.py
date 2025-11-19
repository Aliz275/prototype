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

        if team_id:
            if user_role == 'team_manager':
                c.execute('SELECT manager_id FROM teams WHERE id = ?', (team_id,))
                manager = c.fetchone()
                if not manager or manager[0] != user_id:
                    conn.close()
                    return jsonify({'message': 'Unauthorized: You are not the manager of this team'}), 403
        
        is_general = not employee_ids and not team_id
        
        c.execute('INSERT INTO assignments (title, description, created_by_id, due_date, is_general, team_id) VALUES (?, ?, ?, ?, ?, ?)',
                  (title, description, user_id, due_date, is_general, team_id))
        assignment_id = c.lastrowid

        if employee_ids:
            for emp_id in employee_ids:
                c.execute('INSERT INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (emp_id, assignment_id))

        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Assignment created successfully!'}), 201

    @app.route('/api/assignments', methods=['GET'])
    def get_assignments():
        if 'user_id' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        user_id = session['user_id']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Assignments that are general
        c.execute("SELECT * FROM assignments WHERE is_general = 1")
        general_assignments = c.fetchall()

        # Assignments for teams the user belongs to
        c.execute("""
            SELECT a.*
            FROM assignments a
            JOIN team_members tm ON a.team_id = tm.team_id
            WHERE tm.user_id = ?
        """, (user_id,))
        team_assignments = c.fetchall()

        # Assignments directly assigned to the user
        c.execute("""
            SELECT a.*
            FROM assignments a
            JOIN user_assignments ua ON a.id = ua.assignment_id
            WHERE ua.user_id = ?
        """, (user_id,))
        user_assignments = c.fetchall()

        # Merge all assignments and remove duplicates by id
        all_assignments = {a[0]: a for a in general_assignments + team_assignments + user_assignments}

        conn.close()

        # Map to JSON-friendly format
        assignments_list = []
        for a in all_assignments.values():
            assignments_list.append({
                'id': a[0],
                'title': a[1],
                'description': a[2],
                'due_date': a[3],
                'is_general': bool(a[4]),
                'team_id': a[5],
                'created_by_id': a[6],
                'created_at': a[7]
            })

        return jsonify(assignments_list), 200

    @app.route('/api/assignments/<int:assignment_id>/submit', methods=['POST'])
    def submit_assignment(assignment_id):
        if 'user_id' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            employee_id = session['user_id']
            c.execute('INSERT INTO submissions (assignment_id, employee_id, file_path) VALUES (?, ?, ?)',
                      (assignment_id, employee_id, file_path))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'File submitted successfully!'}), 201

    @app.route('/api/assignments/<int:assignment_id>/submissions', methods=['GET'])
    @role_required(['org_admin', 'team_manager'])
    def get_submissions(assignment_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM submissions WHERE assignment_id = ?', (assignment_id,))
        submissions = c.fetchall()
        conn.close()
        return jsonify(submissions), 200

    @app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def update_assignment(assignment_id):
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        employee_ids = data.get('employee_ids', [])

        is_general = not employee_ids

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE assignments SET title = ?, description = ?, due_date = ?, is_general = ? WHERE id = ?',
                  (title, description, due_date, is_general, assignment_id))

        # Update the user assignments
        c.execute('DELETE FROM user_assignments WHERE assignment_id = ?', (assignment_id,))
        if not is_general:
            for user_id in employee_ids:
                c.execute('INSERT INTO user_assignments (user_id, assignment_id) VALUES (?, ?)',
                          (user_id, assignment_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Assignment updated successfully!'}), 200

    @app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
    @role_required(['org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Optional: You might want to delete related submissions as well
        c.execute('DELETE FROM submissions WHERE assignment_id = ?', (assignment_id,))
        c.execute('DELETE FROM assignments WHERE id = ?', (assignment_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Assignment deleted successfully!'}), 200
