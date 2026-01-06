from flask import Flask
from flask_cors import CORS
from .org_routes import init_org_routes
from .user_routes import init_user_routes
from .assignment_routes import init_assignment_routes
from .db_setup import initialize_database

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"

    CORS(app, supports_credentials=True)

    # Initialize DB (creates default org + default admin)
    initialize_database()

    # Register all routes
    init_org_routes(app)
    init_user_routes(app)
    init_assignment_routes(app)

    return app
