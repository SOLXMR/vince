from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
import logging
from models.models import User
from database import db
from functools import wraps
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)
auth = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        # Log all request details
        logger.debug("=== Token Verification Debug ===")
        logger.debug(f"Request Method: {request.method}")
        logger.debug(f"Request Path: {request.path}")
        logger.debug(f"All Headers: {dict(request.headers)}")
        logger.debug(f"Auth Header: {auth_header}")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
                logger.debug(f"Token extracted: {token[:20]}...")
            except IndexError:
                logger.error("Malformed Authorization header")
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            logger.error("No token provided")
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Log the token decoding attempt
            logger.debug(f"Attempting to decode token...")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.debug(f"Token decoded successfully. Data: {data}")
            
            if 'sub' not in data:
                logger.error("Token missing 'sub' claim")
                return jsonify({'message': 'Invalid token format - missing user ID'}), 401
                
            user_id = data['sub']
            logger.debug(f"User ID from token: {user_id}")
            
            try:
                # Convert string ID to ObjectId
                object_id = ObjectId(user_id)
                logger.debug(f"Successfully converted to ObjectId: {object_id}")
            except InvalidId as e:
                logger.error(f"Invalid ObjectId format: {user_id}")
                return jsonify({'message': 'Invalid user ID format'}), 401
            
            # Log MongoDB query
            logger.debug(f"Executing MongoDB query for user ID: {object_id}")
            user_data = db.users.find_one({'_id': object_id})
            logger.debug(f"MongoDB query result: {user_data}")
            
            if not user_data:
                logger.error(f"No user found for ID: {user_id}")
                return jsonify({'message': 'User not found'}), 401
            
            try:
                current_user = User.from_db_object(user_data)
                logger.debug(f"User object created successfully: {current_user.username}")
            except Exception as e:
                logger.error(f"Error creating User object: {str(e)}")
                return jsonify({'message': 'Error processing user data'}), 500
            
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Error processing token: {str(e)}")
            return jsonify({'message': 'Error processing token', 'error': str(e)}), 401
    
    return decorated

@auth.route('/api/auth/register', methods=['POST'])
def register():
    try:
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
        user_dict = new_user.to_dict()
        logger.debug(f"User dict before insert: {user_dict}")
        result = db.users.insert_one(user_dict)
        new_user._id = result.inserted_id
        logger.debug(f"Inserted new user with ID: {new_user._id}")
        
        # Verify the user was inserted
        inserted_user = db.users.find_one({'_id': new_user._id})
        logger.debug(f"Verification - Found user in DB: {inserted_user}")
        
        # Generate token
        token_data = {
            'sub': str(new_user._id),
            'username': new_user.username,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        logger.debug(f"Token data: {token_data}")
        token = jwt.encode(token_data, current_app.config['SECRET_KEY'])
        logger.debug(f"Generated token: {token[:20]}...")
        
        return jsonify({
            'token': token,
            'username': new_user.username,
            'message': 'User created successfully'
        }), 201
    except Exception as e:
        logger.error(f"Error in registration: {str(e)}")
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth.route('/api/auth/login', methods=['POST'])
def login():
    try:
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
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@auth.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        logger.debug(f"Profile request for user: {current_user.username}")
        logger.debug(f"User ID: {current_user._id}")
        logger.debug(f"User object: {current_user.to_dict()}")
        
        # Double-check user exists in database
        user_data = db.users.find_one({'_id': current_user._id})
        logger.debug(f"User data from DB: {user_data}")
        
        if not user_data:
            logger.error(f"User not found in database: {current_user._id}")
            return jsonify({'message': 'User not found in database'}), 404
            
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