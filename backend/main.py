from flask import Flask
from flask_cors import CORS
from app.routes import init_routes
from app.assignment_routes import init_assignment_routes
from app.org_routes import init_org_routes
from app.db_setup import initialize_database
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

# Register API routes
init_routes(app)
init_assignment_routes(app)
init_org_routes(app)

if __name__ == '__main__':
    print("Starting backend on http://0.0.0.0:8000")
    app.run(debug=True, host='0.0.0.0', port=8000)
