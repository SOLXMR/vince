from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.models import User
import logging
from database import db
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)

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
        logger.debug(f"Secret Key exists: {bool(current_app.config.get('SECRET_KEY'))}")
        
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
            logger.debug(f"Attempting to decode token with secret key...")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.debug(f"Token decoded successfully. Data: {data}")
            
            if 'sub' not in data:
                logger.error("Token missing 'sub' claim")
                return jsonify({'message': 'Invalid token format - missing user ID'}), 401
            
            user_id = data['sub']
            logger.debug(f"Looking for user with ID: {user_id}")
            
            try:
                # Convert string ID to ObjectId
                object_id = ObjectId(user_id)
                logger.debug(f"Successfully converted to ObjectId: {object_id}")
            except InvalidId as e:
                logger.error(f"Invalid ObjectId format: {user_id}")
                return jsonify({'message': 'Invalid user ID format'}), 401
            
            # Log MongoDB connection status
            try:
                db.client.server_info()
                logger.debug("MongoDB connection is active")
            except Exception as e:
                logger.error(f"MongoDB connection error: {str(e)}")
                return jsonify({'message': 'Database connection error'}), 500
            
            # Find user in database
            user_data = db.users.find_one({'_id': object_id})
            logger.debug(f"Database query result: {user_data}")
            
            if not user_data:
                logger.error(f"No user found for ID: {user_id}")
                return jsonify({'message': 'User not found'}), 401
            
            try:
                current_user = User.from_db_object(user_data)
                logger.debug(f"User object created: {current_user.username}")
                return f(current_user, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error creating User object: {str(e)}")
                return jsonify({'message': 'Error processing user data'}), 500
            
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