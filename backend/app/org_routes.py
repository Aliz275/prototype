from flask import request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import get_db
from .models import Organization, Team, User, TeamMember
from .auth import role_required

def init_org_routes(app):
    @app.route('/api/organizations', methods=['POST'])
    @role_required(['super_admin'])
    def create_organization():
        db: Session = next(get_db())
        data = request.get_json()
        name = data.get('name')

        if not name:
            return jsonify({'message': 'Organization name is required'}), 400

        new_org = Organization(name=name)
        db.add(new_org)
        try:
            db.commit()
            db.refresh(new_org)
            return jsonify({'message': 'Organization created successfully!', 'organization_id': new_org.id}), 201
        except IntegrityError:
            db.rollback()
            return jsonify({'message': 'Organization name already exists'}), 400

    @app.route('/api/teams', methods=['POST'])
    @role_required(['org_admin'])
    def create_team():
        db: Session = next(get_db())
        data = request.get_json()
        name = data.get('name')
        organization_id = data.get('organization_id')
        manager_id = data.get('manager_id')

        if not name or not organization_id:
            return jsonify({'message': 'Team name and organization ID are required'}), 400
        
        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if user.organization_id != organization_id:
            return jsonify({'message': 'Unauthorized: You can only create teams for your own organization'}), 403

        new_team = Team(name=name, organization_id=organization_id, manager_id=manager_id)
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        
        return jsonify({'message': 'Team created successfully!', 'team_id': new_team.id}), 201

    @app.route('/api/teams/<int:team_id>/members', methods=['POST'])
    @role_required(['org_admin', 'team_manager'])
    def add_team_member(team_id):
        db: Session = next(get_db())
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'message': 'User ID is required'}), 400
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return jsonify({'message': 'Team not found'}), 404

        user_id = request.current_user['sub']
        user = db.query(User).filter(User.id == user_id).first()
        if user.role == 'team_manager' and team.manager_id != user.id:
            return jsonify({'message': 'Unauthorized: You are not the manager of this team'}), 403

        new_member = TeamMember(user_id=user_id, team_id=team_id)
        db.add(new_member)
        try:
            db.commit()
            return jsonify({'message': 'User added to team successfully!'}), 201
        except IntegrityError:
            db.rollback()
            return jsonify({'message': 'User is already in this team'}), 400
