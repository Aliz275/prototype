from flask import Flask
from flask_cors import CORS
from .routes import init_routes

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"  # Change this later
    
    CORS(app, supports_credentials=True)

    # Initialize routes
    init_routes(app)

    return app
