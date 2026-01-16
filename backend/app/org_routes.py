import sqlite3
from flask import request, jsonify, session
from .auth import role_required, get_current_user

def init_org_routes(app):

    @app.route('/api/organizations', methods=['POST'])
    @role_required(['super_admin'])
    def create_organization():
        data = request.get_json()
        name = data.get('name')

        if not name:
            return jsonify({'message': 'Organization name is required'}), 400

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('INSERT INTO organizations (name) VALUES (?)', (name,))
            org_id = c.lastrowid
            conn.commit()
            conn.close()
            return jsonify({'message': 'Organization created successfully!', 'organization_id': org_id}), 201
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Organization name already exists'}), 400

    @app.route('/api/teams', methods=['POST'])
    @role_required(['org_admin'])
    def create_team():
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        data = request.get_json()
        name = data.get('name')
        organization_id = data.get('organization_id')

        if not name or not organization_id:
            return jsonify({'message': 'Team name and organization ID are required'}), 400

        if user_organization_id != organization_id:
            return jsonify({'message': 'Unauthorized: You can only create teams in your own organization'}), 403

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO teams (name, organization_id) VALUES (?, ?)', (name, organization_id))
        team_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Team created successfully!', 'team_id': team_id}), 201

    @app.route('/api/teams/<int:team_id>/members', methods=['POST'])
    @role_required(['org_admin'])
    def add_team_member(team_id):
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        data = request.get_json()
        new_member_user_id = data.get('user_id')

        if not new_member_user_id:
            return jsonify({'message': 'User ID is required'}), 400

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Check if the team is in the admin's organization
        c.execute('SELECT organization_id FROM teams WHERE id = ?', (team_id,))
        team_org = c.fetchone()
        if not team_org or team_org[0] != user_organization_id:
            conn.close()
            return jsonify({'message': 'Unauthorized: You can only add members to teams in your own organization'}), 403

        # Check if the user to be added is in the same organization
        c.execute('SELECT organization_id FROM users WHERE id = ?', (new_member_user_id,))
        new_member_org = c.fetchone()
        if not new_member_org or new_member_org[0] != user_organization_id:
            conn.close()
            return jsonify({'message': 'Unauthorized: You can only add users from your own organization to a team'}), 403

        try:
            c.execute('INSERT INTO team_members (user_id, team_id) VALUES (?, ?)', (new_member_user_id, team_id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'message': 'User is already in this team'}), 400
        finally:
            conn.close()

        return jsonify({'message': 'User added to team successfully!'}), 201