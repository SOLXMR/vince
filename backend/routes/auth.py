from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
import logging
from models.models import User
from database import db
from functools import wraps
from bson import ObjectId

logger = logging.getLogger(__name__)
auth = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        logger.debug(f"Auth header received: {auth_header}")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
                logger.debug(f"Token extracted: {token}")
            except IndexError:
                logger.error("Malformed Authorization header")
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            logger.error("No token provided")
            return jsonify({'message': 'Token is missing'}), 401

        try:
            logger.debug(f"Attempting to decode token with secret key: {current_app.config['SECRET_KEY'][:10]}...")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.debug(f"Token decoded successfully. Data: {data}")
            
            user_id = data['sub']
            logger.debug(f"Looking for user with ID: {user_id}")
            
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            logger.debug(f"Database query result: {user_data}")
            
            if not user_data:
                logger.error(f"No user found for ID: {user_id}")
                return jsonify({'message': 'Invalid user'}), 401
            
            current_user = User.from_db_object(user_data)
            logger.debug(f"User authenticated: {current_user.username}")
            
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Error processing token: {str(e)}")
            return jsonify({'message': 'Error processing token', 'error': str(e)}), 401
    
    return decorated

@auth.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    logger.debug(f"Register request received with data: {data}")
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        logger.error("Missing required fields in registration request")
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    existing_user = db.users.find_one({'username': data['username']})
    if existing_user:
        logger.error(f"Username {data['username']} already exists")
        return jsonify({'message': 'Username already exists'}), 400
    
    existing_email = db.users.find_one({'email': data['email']})
    if existing_email:
        logger.error(f"Email {data['email']} already exists")
        return jsonify({'message': 'Email already exists'}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    logger.debug(f"Created new user object for {data['username']}")
    
    # Insert into MongoDB
    result = db.users.insert_one(new_user.to_dict())
    new_user._id = result.inserted_id
    logger.debug(f"Inserted new user with ID: {new_user._id}")
    
    # Generate token
    token = jwt.encode({
        'sub': str(new_user._id),
        'username': new_user.username,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, current_app.config['SECRET_KEY'])
    logger.debug(f"Generated token for new user: {token[:20]}...")
    
    return jsonify({
        'token': token,
        'username': new_user.username,
        'message': 'User created successfully'
    }), 201

@auth.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    logger.debug(f"Login request received with username: {data.get('username')}")
    
    if not data or not data.get('username') or not data.get('password'):
        logger.error("Missing username or password in login request")
        return jsonify({'message': 'Missing username or password'}), 400
    
    # Find user in MongoDB
    user_data = db.users.find_one({'username': data['username']})
    if not user_data:
        logger.error(f"No user found with username: {data['username']}")
        return jsonify({'message': 'Invalid username or password'}), 401
    
    user = User.from_db_object(user_data)
    logger.debug(f"Found user: {user.username}")
    
    if not user.check_password(data['password']):
        logger.error(f"Invalid password for user: {user.username}")
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Generate token
    token = jwt.encode({
        'sub': str(user._id),
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, current_app.config['SECRET_KEY'])
    logger.debug(f"Generated token for user: {token[:20]}...")
    
    return jsonify({
        'token': token,
        'username': user.username
    })

@auth.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        return jsonify({
            'user': {
                '_id': str(current_user._id),
                'username': current_user.username,
                'email': current_user.email
            }
        })
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        return jsonify({
            'message': f'Failed to fetch profile: {str(e)}'
        }), 500 