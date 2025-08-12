from flask import Flask
from flask_cors import CORS
from app.routes import init_routes

app = Flask(__name__)
app.secret_key = 'f3d9b1c2e7a54d1f8b3c9e4d0a67f821'
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)  # Restrict to frontend port (adjust if different)

# Initialize API routes with /api prefix
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)