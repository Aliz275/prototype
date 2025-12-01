from flask import jsonify, session
from app.auth import role_required
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def init_user_routes(app):
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_user_profile(user_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, email, role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'id': user[0],
            'email': user[1],
            'role': user[2]
        }), 200
