from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet
import os

from app.db_setup import initialize_database
from app.routes import init_routes
from app.org_routes import init_org_routes
from app.assignment_routes import init_assignment_routes
from app.messaging_routes import init_messaging_routes
from app.user_routes import init_user_routes
from app.submission_routes import init_submission_routes

# Initialize the database first
initialize_database()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key')
CORS(app, supports_credentials=True)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize routes
init_routes(app)
init_org_routes(app)
init_assignment_routes(app)
init_messaging_routes(app, socketio)
init_user_routes(app)
init_submission_routes(app)

if __name__ == '__main__':
    socketio.run(app, debug=True)