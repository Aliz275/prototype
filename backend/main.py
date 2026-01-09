from flask import Flask, session
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import eventlet
import os

from app.db_setup import initialize_database
from app.db_migrations import apply_migrations
from app.routes import init_routes
from app.org_routes import init_org_routes
from app.assignment_routes import init_assignment_routes
from app.messaging_routes import init_messaging_routes
from app.user_routes import init_user_routes
from app.submission_routes import init_submission_routes
from app.invitation_routes import init_invitation_routes

# Initialize the database first
initialize_database()
apply_migrations()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set for Flask application")
CORS(app, supports_credentials=True)

# Initialize Talisman for security headers
Talisman(app)

def get_user_id():
    if 'user_id' in session:
        return session['user_id']
    return get_remote_address

# Initialize Rate Limiter
# Rate limits are applied to selected routes in app/routes.py
limiter = Limiter(
    key_func=get_user_id,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize routes
init_routes(app, limiter)
init_org_routes(app)
init_assignment_routes(app)
init_messaging_routes(app, socketio)
init_user_routes(app)
init_submission_routes(app)
init_invitation_routes(app)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8000)
