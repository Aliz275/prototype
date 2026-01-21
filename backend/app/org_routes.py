#backend/app/org_routes.py

import sqlite3
from flask import request, jsonify, session
from .auth import role_required, get_current_user

def init_org_routes(app):

    @app.route('/api/organizations', methods=['POST'])
    @role_required(['super_admin'])
    def create_organization():
        data = request.get_json()
        name = data.get('name')
from flask import request, jsonify
import sqlite3
from .role_required import role_required

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_org_routes(app):

    # ---------------- CREATE ORG ----------------
    @app.route("/api/orgs", methods=["POST"])
    @role_required(["super_admin"])
    def create_org():
        data = request.get_json() or {}
        name = data.get("name")

        if not name:
            return jsonify({"message": "Organization name is required"}), 400

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO organizations (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Organization created"}), 201

    # ---------------- GET ORGS ----------------
    @app.route("/api/orgs", methods=["GET"])
    @role_required(["super_admin"])
    def get_orgs():
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name FROM organizations ORDER BY id DESC")
        orgs = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(orgs), 200

    # ---------------- DELETE ORG ----------------
    @app.route("/api/orgs/<int:org_id>", methods=["DELETE"])
    @role_required(["super_admin"])
    def delete_org(org_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
        conn.commit()
        conn.close()

        return jsonify({"message": "Organization deleted"}), 200
