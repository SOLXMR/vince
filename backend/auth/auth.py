from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.models import User
import logging
from database import db
from bson import ObjectId

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        logger.debug(f"Auth header: {auth_header}")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                logger.error("Malformed Authorization header")
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            logger.error("No token provided")
            return jsonify({'message': 'Token is missing'}), 401

        try:
            logger.debug(f"Decoding token: {token}")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.debug(f"Decoded token data: {data}")
            
            user_id = data['sub']
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            
            if not user_data:
                logger.error(f"No user found for ID: {user_id}")
                return jsonify({'message': 'Invalid user'}), 401
            
            current_user = User.from_db_object(user_data)
            logger.debug(f"User authenticated: {current_user.username}")
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Error processing token: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated