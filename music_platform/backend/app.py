from flask import Flask, jsonify, request, current_app, send_from_directory
from flask_cors import CORS
from models.models import db
from routes.songs import songs
from routes.auth import auth
import logging
import os
import secrets

# Create a file to store the secret key
SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), 'secret_key')

def get_or_create_secret_key():
    try:
        if os.path.exists(SECRET_KEY_FILE):
            with open(SECRET_KEY_FILE, 'r') as f:
                return f.read().strip()
        else:
            # Generate a new secret key
            secret_key = secrets.token_hex(32)
            # Save it to the file
            with open(SECRET_KEY_FILE, 'w') as f:
                f.write(secret_key)
            return secret_key
    except Exception as e:
        logger.error(f"Error handling secret key: {str(e)}")
        return secrets.token_hex(32)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization", "Content-Disposition"],
        "max_age": 3600,
        "supports_credentials": True,
        "send_wildcard": False
    }
})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set the secret key
app.config['SECRET_KEY'] = get_or_create_secret_key()
logger.info("Secret key configured")

# Initialize extensions
db.init_app(app)

# Register blueprints
app.register_blueprint(songs)
app.register_blueprint(auth)

@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

# Create database tables
with app.app_context():
    try:
        if not os.path.exists('instance'):
            os.makedirs('instance')
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 