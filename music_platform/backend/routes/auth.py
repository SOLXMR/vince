from flask import Blueprint, request, jsonify, current_app
from models.models import db, User
import jwt
from datetime import datetime, timedelta
import logging
from flask import current_app as app
from flask_jwt_extended import jwt_required, current_user

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.debug(f"Register request data: {data}")
        
        if not data or not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 400

        new_user = User(username=data['username'], email=data['email'])
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()

        # Generate token for the new user
        secret_key = app.config.get('SECRET_KEY')
        if not secret_key:
            logger.error("No SECRET_KEY configured")
            return jsonify({'status': 'error', 'message': 'Server configuration error'}), 500

        # Create the token payload with string ID
        payload = {
            'sub': str(new_user.id),  # Convert ID to string
            'username': new_user.username,
            'email': new_user.email,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        logger.debug(f"Token payload for new user: {payload}")

        try:
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            logger.debug("Token generated successfully for new user")
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Error generating token'}), 500

        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500

@auth.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.debug(f"Login request data: {data}")
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'status': 'error', 'message': 'Missing username or password'}), 400

        user = User.query.filter_by(username=data['username']).first()
        logger.debug(f"Found user: {user}")

        if not user or not user.check_password(data['password']):
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

        # Get the secret key from config
        secret_key = app.config.get('SECRET_KEY')
        if not secret_key:
            logger.error("No SECRET_KEY configured")
            return jsonify({'status': 'error', 'message': 'Server configuration error'}), 500

        # Create the token payload with string ID
        payload = {
            'sub': str(user.id),  # Convert ID to string
            'username': user.username,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        logger.debug(f"Token payload: {payload}")

        # Generate the token
        try:
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            logger.debug("Token generated successfully")
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Error generating token'}), 500

        return jsonify({
            'status': 'success',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Login failed: {str(e)}'
        }), 500

@auth.route('/profile', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_profile():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if not current_user:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 401

        return jsonify({
            'status': 'success',
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 