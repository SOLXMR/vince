from flask import Flask, jsonify, request, current_app, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import os
import secrets
from database import db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_secret_key():
    # First try to get from environment variable
    secret_key = os.getenv('SECRET_KEY')
    if secret_key:
        return secret_key
        
    # For local development, use file-based storage
    SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), 'secret_key')
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

# Configure CORS
CORS(app, 
     resources={
         r"/*": {
             "origins": [
                 "http://localhost:3000",
                 "https://vincefrontend.vercel.app"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }
     })

# Handle OPTIONS requests
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in [
        'http://localhost:3000',
        'https://vincefrontend.vercel.app'
    ]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Configure app
app.config['SECRET_KEY'] = get_secret_key()
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
from routes.songs import songs
from routes.auth import auth

app.register_blueprint(songs)
app.register_blueprint(auth)

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Test MongoDB connection
        db.users.find_one()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'secret_key_source': 'env' if os.getenv('SECRET_KEY') else 'file'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 