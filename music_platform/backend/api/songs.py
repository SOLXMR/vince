from flask import Blueprint, request, jsonify, current_app, send_from_directory, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from models.models import Song, db, User
from werkzeug.utils import secure_filename
import os
import logging
import jwt

logger = logging.getLogger(__name__)

songs_bp = Blueprint('songs', __name__)

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@songs_bp.route('/list', methods=['GET'])
@jwt_required()
def list_songs():
    try:
        if not current_user:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 401
            
        songs = Song.query.all()
        
        return jsonify({
            'status': 'success',
            'songs': [{
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'duration': song.duration,
                'cover_art': song.cover_art,
                'file_path': song.file_path
            } for song in songs]
        }), 200
    except Exception as e:
        logger.error(f"Error listing songs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@songs_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_song():
    try:
        if not current_user:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 401

        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Create song record
        song = Song(
            title=request.form.get('title', filename),
            artist='Unknown Artist',
            album='Unknown Album',
            duration=0,
            cover_art='',
            file_path=filename,
            user_id=current_user.id
        )

        db.session.add(song)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Song uploaded successfully',
            'song': {
                'id': song.id,
                'title': song.title,
                'file_path': song.file_path
            }
        }), 201

    except Exception as e:
        logger.error(f"Error uploading song: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@songs_bp.route('/stream/<path:filename>', methods=['GET', 'OPTIONS'])
def stream_song(filename):
    if request.method == 'OPTIONS':
        return '', 200

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'No authorization header'}), 401

    try:
        token = auth_header.split(" ")[1]
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = int(data['sub'])
        current_user = User.query.filter_by(id=user_id).first()
        
        if not current_user:
            return jsonify({'message': 'Invalid user'}), 401

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404

        response = make_response(send_from_directory(UPLOAD_FOLDER, filename))
        response.headers['Content-Type'] = 'audio/mpeg'
        return response

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error streaming song: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500