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
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.debug(f"Token data: {data}")
            user_id = data['sub']
            logger.debug(f"Looking for user with ID: {user_id}")
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            logger.debug(f"Found user data: {user_data}")
            current_user = User.from_db_object(user_data)
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if db.users.find_one({'username': data['username']}):
        return jsonify({'message': 'Username already exists'}), 400
    
    if db.users.find_one({'email': data['email']}):
        return jsonify({'message': 'Email already exists'}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    
    # Insert into MongoDB
    result = db.users.insert_one(new_user.to_dict())
    new_user._id = result.inserted_id
    
    # Generate token
    token = jwt.encode({
        'sub': str(new_user._id),
        'username': new_user.username,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, current_app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'username': new_user.username,
        'message': 'User created successfully'
    }), 201

@auth.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    # Find user in MongoDB
    user_data = db.users.find_one({'username': data['username']})
    if not user_data:
        return jsonify({'message': 'Invalid username or password'}), 401
    
    user = User.from_db_object(user_data)
    
    if not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Generate token
    token = jwt.encode({
        'sub': str(user._id),
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, current_app.config['SECRET_KEY'])
    
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