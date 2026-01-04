from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os

from app.db_setup import initialize_database
from app.db_migrations import apply_migrations

from app.auth import auth_bp
from app.org_routes import init_org_routes
from app.assignment_routes import init_assignment_routes
from app.messaging_routes import init_messaging_routes
from app.user_routes import init_user_routes
from app.submission_routes import init_submission_routes
from app.invitation_routes import init_invitation_routes

# -------------------------
# DATABASE INIT
# -------------------------
initialize_database()
apply_migrations()

# -------------------------
# FLASK APP
# -------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:3000"]
)

socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# -------------------------
# ROUTES
# -------------------------
app.register_blueprint(auth_bp)

init_org_routes(app)
init_assignment_routes(app)
init_messaging_routes(app, socketio)
init_user_routes(app)
init_submission_routes(app)
init_invitation_routes(app)

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
