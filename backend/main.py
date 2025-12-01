from flask import Flask
from flask_cors import CORS
from app.routes import init_routes
from app.assignment_routes import init_assignment_routes
from app.org_routes import init_org_routes
from app.messaging_routes import init_messaging_routes
from app.user_routes import init_user_routes
from app.db_setup import initialize_database
from flask_socketio import SocketIO
import eventlet
import os

# Ensure DB is initialized first
initialize_database()

app = Flask(__name__)
app.secret_key = 'f3d9b1c2e7a54d1f8b3c9e4d0a67f821'

CORS(
    app,
    origins=["http://localhost:3000"],
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# Register API routes
init_routes(app)
init_assignment_routes(app)
init_org_routes(app)
init_messaging_routes(app, socketio)
init_user_routes(app)

if __name__ == '__main__':
    print("Starting backend on http://0.0.0.0:8001")
    socketio.run(app, host='0.0.0.0', port=8001)
