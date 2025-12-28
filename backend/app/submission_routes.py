import os
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Submission, Assignment, Team
from .auth import role_required

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_submission_routes(app):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    @app.route('/api/submissions/<int:assignment_id>', methods=['POST'])
    def submit_assignment(assignment_id):
        db: Session = next(get_db())
        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if 'file' not in request.files:
            return jsonify({'message': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'message': 'File type not allowed'}), 400

        safe_filename = secure_filename(f"user{user.id}_assign{assignment_id}_{file.filename}")
        dest_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        try:
            file.save(dest_path)
        except Exception as e:
            return jsonify({'message': f'Failed to save file: {e}'}), 500

        new_submission = Submission(
            assignment_id=assignment_id,
            employee_id=user.id,
            file_path=safe_filename,
            status='pending'
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        return jsonify({'message': 'Submission uploaded successfully', 'submission_id': new_submission.id, 'file': safe_filename}), 201

    @app.route('/api/submissions/<int:assignment_id>', methods=['GET'])
    def list_submissions(assignment_id):
        db: Session = next(get_db())
        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.role in ('org_admin', 'super_admin'):
            submissions = db.query(Submission).filter(Submission.assignment_id == assignment_id).all()
        elif user.role == 'team_manager':
            submissions = db.query(Submission).join(Assignment).join(Team).filter(
                (Submission.assignment_id == assignment_id) & ((Team.manager_id == user.id) | (Assignment.is_general == True))
            ).all()
        else:
            submissions = db.query(Submission).filter(
                (Submission.assignment_id == assignment_id) & (Submission.employee_id == user.id)
            ).all()

        submissions_list = []
        for s in submissions:
            submissions_list.append({
                'id': s.id,
                'assignment_id': s.assignment_id,
                'employee_id': s.employee_id,
                'file_path': s.file_path,
                'submitted_at': s.submitted_at.isoformat(),
                'status': s.status,
                'employee_email': s.employee.email
            })

        return jsonify({'submissions': submissions_list}), 200

    @app.route('/api/submissions/<int:submission_id>/accept', methods=['POST'])
    @role_required(['org_admin', 'super_admin', 'team_manager'])
    def accept_submission(submission_id):
        db: Session = next(get_db())
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return jsonify({'message': 'Submission not found'}), 404

        submission.status = 'accepted'
        db.commit()

        return jsonify({'message': 'Submission accepted'}), 200

    @app.route('/api/submissions/delete/<int:submission_id>', methods=['DELETE'])
    @role_required(['org_admin', 'super_admin', 'team_manager'])
    def delete_submission(submission_id):
        db: Session = next(get_db())
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return jsonify({'message': 'Submission not found'}), 404

        file_path = os.path.join(UPLOAD_FOLDER, submission.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.delete(submission)
        db.commit()

        return jsonify({'message': 'Submission deleted'}), 200
