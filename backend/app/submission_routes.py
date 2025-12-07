# backend/app/submission_routes.py
import sqlite3
import os
from flask import request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

def _connect():
    return sqlite3.connect(DB_PATH)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_submission_routes(app):
    # ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # ---------------- POST upload submission ----------------
    @app.route('/api/submissions/<int:assignment_id>', methods=['POST'])
    def submit_assignment(assignment_id):
        # require login
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        # get user id from session
        c.execute('SELECT id FROM users WHERE email = ?', (session.get('email'),))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id = row[0]

        # check file
        if 'file' not in request.files:
            conn.close()
            return jsonify({'message': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            conn.close()
            return jsonify({'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            conn.close()
            return jsonify({'message': 'File type not allowed'}), 400

        # Build safe filename
        safe_filename = secure_filename(f"user{user_id}_assign{assignment_id}_{file.filename}")
        dest_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        try:
            file.save(dest_path)
        except Exception as e:
            conn.close()
            return jsonify({'message': f'Failed to save file: {e}'}), 500

        # insert submission record (DB columns: assignment_id, employee_id, file_path)
        try:
            c.execute('INSERT INTO submissions (assignment_id, employee_id, file_path) VALUES (?, ?, ?)',
                      (assignment_id, user_id, safe_filename))
            conn.commit()
            submission_id = c.lastrowid
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'message': f'DB error: {e}'}), 500

        conn.close()
        return jsonify({
            'message': 'Submission uploaded successfully',
            'submission_id': submission_id,
            'file': safe_filename
        }), 201

    # ---------------- GET submissions for an assignment ----------------
    @app.route('/api/submissions/<int:assignment_id>', methods=['GET'])
    def list_submissions(assignment_id):
        # require login
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        # get current user id + role
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        u = c.fetchone()
        if not u:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, role = u[0], u[1]

        # if user is org_admin or team_manager -> can see all submissions for assignment
        if role in ('org_admin', 'super_admin'):
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, u.email
                FROM submissions s
                LEFT JOIN users u ON s.employee_id = u.id
                WHERE s.assignment_id = ?
                ORDER BY s.submitted_at DESC
            ''', (assignment_id,))
            rows = c.fetchall()
        elif role == 'team_manager':
            # ensure manager either created/owns team for that assignment OR manager of that team
            # For simplicity: return submissions only for assignments that belong to teams this manager manages OR general assignments
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, u.email
                FROM submissions s
                LEFT JOIN users u ON s.employee_id = u.id
                LEFT JOIN assignments a ON s.assignment_id = a.id
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE s.assignment_id = ? AND (t.manager_id = ? OR a.is_general = 1)
                ORDER BY s.submitted_at DESC
            ''', (assignment_id, user_id))
            rows = c.fetchall()
        else:
            # employee: only their own submissions for that assignment
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, u.email
                FROM submissions s
                LEFT JOIN users u ON s.employee_id = u.id
                WHERE s.assignment_id = ? AND s.employee_id = ?
                ORDER BY s.submitted_at DESC
            ''', (assignment_id, user_id))
            rows = c.fetchall()

        submissions = []
        for r in rows:
            submissions.append({
                'id': r[0],
                'assignment_id': r[1],
                'employee_id': r[2],
                'file_path': r[3],
                'submitted_at': r[4],
                'employee_email': r[5]
            })

        conn.close()
        return jsonify({'submissions': submissions}), 200

    # ---------------- GET current user's submissions (optional) ----------------
    @app.route('/api/my_submissions', methods=['GET'])
    def my_submissions():
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (session.get('email'),))
        r = c.fetchone()
        if not r:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id = r[0]

        c.execute('''
            SELECT s.id, s.assignment_id, s.file_path, s.submitted_at, a.title
            FROM submissions s
            LEFT JOIN assignments a ON s.assignment_id = a.id
            WHERE s.employee_id = ?
            ORDER BY s.submitted_at DESC
        ''', (user_id,))
        rows = c.fetchall()
        out = []
        for row in rows:
            out.append({
                'id': row[0],
                'assignment_id': row[1],
                'file_path': row[2],
                'submitted_at': row[3],
                'assignment_title': row[4]
            })
        conn.close()
        return jsonify({'submissions': out}), 200

    # ---------------- DOWNLOAD submission file ----------------
    @app.route('/api/submissions/download/<path:filename>', methods=['GET'])
    def download_submission_file(filename):
        # check login
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        # Security: ensure filename exists in DB and user is authorized to access it
        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT s.id, s.assignment_id, s.employee_id, a.team_id FROM submissions s LEFT JOIN assignments a ON s.assignment_id = a.id WHERE s.file_path = ?', (filename,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'message': 'File not found'}), 404

        submission_id, assignment_id, employee_id, team_id = row[0], row[1], row[2], row[3]

        # get current user
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        u = c.fetchone()
        if not u:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, role = u[0], u[1]

        # Authorization rules:
        # - super_admin/org_admin: allowed
        # - team_manager: allowed if they manage the team this assignment belongs to
        # - employee: allowed only for their own submissions
        allowed = False
        if role in ('org_admin', 'super_admin'):
            allowed = True
        elif role == 'team_manager':
            if team_id is not None:
                c.execute('SELECT manager_id FROM teams WHERE id = ?', (team_id,))
                t = c.fetchone()
                if t and t[0] == user_id:
                    allowed = True
        else:
            if user_id == employee_id:
                allowed = True

        conn.close()

        if not allowed:
            return jsonify({'message': 'Unauthorized to download this file'}), 403

        # serve file from uploads directory
        safe_dir = os.path.abspath(UPLOAD_FOLDER)
        return send_from_directory(safe_dir, filename, as_attachment=True)
