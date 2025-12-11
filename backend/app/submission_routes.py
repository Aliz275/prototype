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
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # ---------------- POST upload submission ----------------
    @app.route('/api/submissions/<int:assignment_id>', methods=['POST'])
    def submit_assignment(assignment_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        # get user id
        c.execute('SELECT id FROM users WHERE email = ?', (session.get('email'),))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id = row[0]

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

        safe_filename = secure_filename(f"user{user_id}_assign{assignment_id}_{file.filename}")
        dest_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        try:
            file.save(dest_path)
        except Exception as e:
            conn.close()
            return jsonify({'message': f'Failed to save file: {e}'}), 500

        try:
            # Insert submission with status "pending"
            c.execute(
                'INSERT INTO submissions (assignment_id, employee_id, file_path, status) VALUES (?, ?, ?, ?)',
                (assignment_id, user_id, safe_filename, 'pending')
            )
            conn.commit()
            submission_id = c.lastrowid
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'message': f'DB error: {e}'}), 500

        conn.close()
        return jsonify({'message': 'Submission uploaded successfully', 'submission_id': submission_id, 'file': safe_filename}), 201

    # ---------------- GET submissions for an assignment ----------------
    @app.route('/api/submissions/<int:assignment_id>', methods=['GET'])
    def list_submissions(assignment_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()

        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        u = c.fetchone()
        if not u:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, role = u[0], u[1]

        if role in ('org_admin', 'super_admin'):
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, s.status, u.email
                FROM submissions s
                LEFT JOIN users u ON s.employee_id = u.id
                WHERE s.assignment_id = ?
                ORDER BY s.submitted_at DESC
            ''', (assignment_id,))
        elif role == 'team_manager':
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, s.status, u.email
                FROM submissions s
                LEFT JOIN users u ON s.employee_id = u.id
                LEFT JOIN assignments a ON s.assignment_id = a.id
                LEFT JOIN teams t ON a.team_id = t.id
                WHERE s.assignment_id = ? AND (t.manager_id = ? OR a.is_general = 1)
                ORDER BY s.submitted_at DESC
            ''', (assignment_id, user_id))
        else:
            c.execute('''
                SELECT s.id, s.assignment_id, s.employee_id, s.file_path, s.submitted_at, s.status, u.email
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
                'status': r[5] or 'pending',
                'employee_email': r[6]
            })

        conn.close()
        return jsonify({'submissions': submissions}), 200

    # ---------------- POST accept submission ----------------
    @app.route('/api/submissions/<int:submission_id>/accept', methods=['POST'])
    def accept_submission(submission_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        u = c.fetchone()
        if not u:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, role = u[0], u[1]

        if role not in ('org_admin', 'super_admin', 'team_manager'):
            conn.close()
            return jsonify({'message': 'Forbidden'}), 403

        try:
            c.execute('UPDATE submissions SET status = "accepted" WHERE id = ?', (submission_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'message': f'DB error: {e}'}), 500

        conn.close()
        return jsonify({'message': 'Submission accepted'}), 200

    # ---------------- DELETE submission ----------------
    @app.route('/api/submissions/delete/<int:submission_id>', methods=['DELETE'])
    def delete_submission(submission_id):
        if 'email' not in session:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = _connect()
        c = conn.cursor()
        c.execute('SELECT id, role FROM users WHERE email = ?', (session.get('email'),))
        u = c.fetchone()
        if not u:
            conn.close()
            return jsonify({'message': 'User not found'}), 404
        user_id, role = u[0], u[1]

        if role not in ('org_admin', 'super_admin', 'team_manager'):
            conn.close()
            return jsonify({'message': 'Forbidden'}), 403

        try:
            c.execute('SELECT file_path FROM submissions WHERE id = ?', (submission_id,))
            row = c.fetchone()
            if row:
                file_path = os.path.join(UPLOAD_FOLDER, row[0])
                if os.path.exists(file_path):
                    os.remove(file_path)
            c.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'message': f'DB error: {e}'}), 500

        conn.close()
        return jsonify({'message': 'Submission deleted'}), 200
