from flask import request, jsonify
from sqlalchemy.orm import Session
from .auth import role_required
from datetime import datetime
from .database import get_db
from .models import User, Assignment, Team, UserAssignment

def init_assignment_routes(app):
    # ---------------- CREATE ASSIGNMENT ----------------
    @app.route('/api/assignments', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def create_assignment():
        """
        Create a new assignment
        ---
        parameters:
          - in: body
            name: body
            schema:
              id: Assignment
              required:
                - title
              properties:
                title:
                  type: string
                description:
                  type: string
                due_date:
                  type: string
                  format: date-time
                employee_ids:
                  type: array
                  items:
                    type: integer
                team_id:
                  type: integer
        responses:
          201:
            description: Assignment created successfully
          400:
            description: Bad request
        """
        db: Session = next(get_db())
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

        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if team_id and user.role == 'team_manager':
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team or team.manager_id != user.id:
                return jsonify({'message': 'Unauthorized: Not manager of this team'}), 403

        is_general = not employee_ids and not team_id

        new_assignment = Assignment(
            title=title,
            description=description,
            created_by_id=user.id,
            due_date=due_date,
            is_general=is_general,
            team_id=team_id
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        if employee_ids:
            for emp_id in employee_ids:
                user_assignment = UserAssignment(user_id=emp_id, assignment_id=new_assignment.id)
                db.add(user_assignment)
            db.commit()

        return jsonify({'message': 'Assignment created successfully!', 'assignment_id': new_assignment.id}), 201

    # ---------------- GET ALL ASSIGNMENTS ----------------
    @app.route('/api/assignments', methods=['GET'])
    def get_assignments():
        """
        Get all assignments
        ---
        responses:
          200:
            description: A list of assignments
            schema:
              type: array
              items:
                $ref: '#/definitions/Assignment'
        """
        db: Session = next(get_db())
        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.role == 'org_admin':
            assignments = db.query(Assignment).all()
        elif user.role == 'team_manager':
            assignments = db.query(Assignment).join(Team).filter((Assignment.is_general == True) | (Team.manager_id == user.id)).all()
        else:
            assignments = db.query(Assignment).outerjoin(UserAssignment).outerjoin(Team).filter(
                (Assignment.is_general == True) | (UserAssignment.user_id == user.id) | (Team.members.any(id=user.id))
            ).all()

        assignments_list = []
        for a in assignments:
            assignments_list.append({
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'due_date': a.due_date.isoformat() if a.due_date else None,
                'is_general': a.is_general,
                'team_id': a.team_id,
                'created_by_id': a.created_by_id,
                'employee_ids': [ua.user_id for ua in a.user_assignments]
            })

        return jsonify({'assignments': assignments_list}), 200

    # ---------------- GET SINGLE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
    def get_assignment(assignment_id):
        db: Session = next(get_db())
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404

        return jsonify({'assignment': {
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'is_general': assignment.is_general,
            'team_id': assignment.team_id,
            'created_by_id': assignment.created_by_id,
            'employee_ids': [ua.user_id for ua in assignment.user_assignments]
        }}), 200

    # ---------------- UPDATE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def update_assignment(assignment_id):
        db: Session = next(get_db())
        data = request.get_json() or {}
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404

        assignment.title = data.get('title', assignment.title)
        assignment.description = data.get('description', assignment.description)
        due_date = data.get('due_date')
        if due_date:
            try:
                assignment.due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return jsonify({'message': 'Invalid due date format. Use ISO 8601 format.'}), 400
        assignment.team_id = data.get('team_id', assignment.team_id)

        employee_ids = data.get('employee_ids', [])
        db.query(UserAssignment).filter(UserAssignment.assignment_id == assignment_id).delete()
        if employee_ids:
            for emp_id in employee_ids:
                user_assignment = UserAssignment(user_id=emp_id, assignment_id=assignment.id)
                db.add(user_assignment)
        
        db.commit()
        return jsonify({'message': 'Assignment updated successfully!'}), 200

    # ---------------- DELETE ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
    @role_required(['org_admin', 'team_manager'])
    def delete_assignment(assignment_id):
        db: Session = next(get_db())
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
        
        db.delete(assignment)
        db.commit()
        return jsonify({'message': 'Assignment deleted successfully!'}), 200

    # ---------------- EXTEND DUE DATE ----------------
    @app.route('/api/assignments/<int:assignment_id>/extend', methods=['PUT'])
    @role_required(['org_admin', 'team_manager'])
    def extend_due_date(assignment_id):
        db: Session = next(get_db())
        data = request.get_json()
        new_due_date = data.get('due_date')

        if not new_due_date:
            return jsonify({'message': 'New due date is required'}), 400

        try:
            new_due_date = datetime.fromisoformat(new_due_date)
        except ValueError:
            return jsonify({'message': 'Invalid due date format. Use ISO 8601 format.'}), 400

        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
        
        assignment.due_date = new_due_date
        db.commit()

        return jsonify({'message': 'Due date extended successfully!'}), 200

    # ---------------- RE-ASSIGN ASSIGNMENT ----------------
    @app.route('/api/assignments/<int:assignment_id>/reassign', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def reassign_assignment(assignment_id):
        db: Session = next(get_db())
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        team_id = data.get('team_id')

        if not employee_ids and not team_id:
            return jsonify({'message': 'Employee IDs or a team ID is required'}), 400
        
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404

        if employee_ids:
            db.query(UserAssignment).filter(UserAssignment.assignment_id == assignment_id).delete()
            for emp_id in employee_ids:
                user_assignment = UserAssignment(user_id=emp_id, assignment_id=assignment.id)
                db.add(user_assignment)

        if team_id:
            assignment.team_id = team_id

        db.commit()

        return jsonify({'message': 'Assignment re-assigned successfully!'}), 200
