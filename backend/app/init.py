#backend/app/init.py

from flask import Flask
from flask_cors import CORS

from app.db import init_db

# 🔹 ROUTE INITIALIZERS
from app.routes import init_routes
from app.invitation import init_invitation_routes
from app.assignment_routes import init_assignment_routes
from app.auth_routes import init_auth_routes


def create_app():
    app = Flask(__name__)

    # 🔐 CONFIG
    app.secret_key = "supersecretkey"

    # 🌐 CORS (IMPORTANT for Next.js fetch)
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": "http://localhost:3000"}}
    )

    # 🗄️ DATABASE
    init_db()

    # 🚏 REGISTER ROUTES (ORDER MATTERS)
    init_auth_routes(app)          # /api/login
    init_routes(app)               # /api/me, health, etc
    init_invitation_routes(app)    # /api/invitations
    init_assignment_routes(app)    # /api/assignments

    return app

