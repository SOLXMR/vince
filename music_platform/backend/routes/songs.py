from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file
from werkzeug.utils import secure_filename
from models.models import db, Song
from auth.auth import token_required
import os
from datetime import datetime
import jwt
from models.models import User
from utils.spotify import SpotifyDownloader
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

songs = Blueprint('songs', __name__)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

# Initialize Spotify downloader with credentials from env
spotify_downloader = SpotifyDownloader(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@songs.route('/api/songs/upload', methods=['POST'])
@token_required
def upload_song(current_user):
    # Debug information
    print("Files in request:", request.files)
    print("Form data:", request.form)
    
    if 'file' not in request.files:
        print("No file in request.files")
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    print("File object:", file)
    print("Filename:", file.filename)
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        print("Uploads directory:", uploads_dir)

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(uploads_dir, unique_filename)
        print("Saving file to:", file_path)
        
        file.save(file_path)
        print("File saved successfully")

        # Create song record in database
        title = request.form.get('title', filename)
        new_song = Song(
            title=title,
            file_path=unique_filename,
            user_id=current_user.id
        )
        
        db.session.add(new_song)
        db.session.commit()
        print("Database record created successfully")

        return jsonify({
            'status': 'success',
            'message': 'Song uploaded successfully',
            'song': new_song.to_dict()
        }), 201

    except Exception as e:
        print(f"Upload error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to upload song: {str(e)}'
        }), 500

@songs.route('/api/songs/upload/spotify', methods=['POST'])
@token_required
def upload_spotify(current_user):
    try:
        data = request.get_json()
        if not data or 'spotify_url' not in data:
            return jsonify({'status': 'error', 'message': 'No Spotify URL provided'}), 400

        spotify_url = data['spotify_url']
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        print(f"Using Spotify credentials - Client ID: {os.getenv('SPOTIFY_CLIENT_ID')}")
        
        # Download the track
        track_info = spotify_downloader.download_track(spotify_url, uploads_dir)

        # Create song record in database
        new_song = Song(
            title=track_info['title'],
            artist=track_info['artist'],
            album=track_info['album'],
            duration=track_info['duration'],
            cover_art=track_info['cover_art'],
            file_path=track_info['file_path'],
            user_id=current_user.id
        )
        
        db.session.add(new_song)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Song uploaded successfully',
            'song': new_song.to_dict()
        }), 201

    except Exception as e:
        print(f"Spotify upload error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to upload song: {str(e)}'
        }), 500

@songs.route('/api/songs/list', methods=['GET'])
@token_required
def list_songs(current_user):
    try:
        songs = Song.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'status': 'success',
            'songs': [song.to_dict() for song in songs]
        })
    except Exception as e:
        print(f"Error fetching songs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch songs'
        }), 500

@songs.route('/api/songs/stream/<path:filename>', methods=['GET', 'OPTIONS'])
def stream_song(filename):
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Only check authentication for actual GET requests
        if request.method == 'GET':
            # Get the auth header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'message': 'Token is missing'}), 401
            
            token = auth_header.split(" ")[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = int(data['sub'])
            current_user = User.query.filter_by(id=user_id).first()
            
            if not current_user:
                return jsonify({'message': 'Invalid user'}), 401

            # Check if the song exists and belongs to the user
            song = Song.query.filter_by(file_path=filename, user_id=current_user.id).first()
            if not song:
                return jsonify({'status': 'error', 'message': 'Song not found'}), 404

            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            file_path = os.path.join(uploads_dir, filename)
            
            # Get requested format from query parameters
            requested_format = request.args.get('format', 'mp3').lower()
            
            if requested_format not in ['mp3', 'wav']:
                return jsonify({'status': 'error', 'message': 'Invalid format'}), 400
                
            # If the requested format matches the source format, send the file directly
            source_format = filename.rsplit('.', 1)[1].lower()
            if requested_format == source_format:
                return send_file(
                    file_path,
                    mimetype=f'audio/{requested_format}',
                    as_attachment=True,
                    download_name=f"{filename.rsplit('.', 1)[0]}.{requested_format}"
                )
            
            # Convert the file
            try:
                audio = AudioSegment.from_file(file_path, format=source_format)
                
                # Create a temporary file for the converted audio
                with tempfile.NamedTemporaryFile(suffix=f'.{requested_format}', delete=False) as temp_file:
                    audio.export(temp_file.name, format=requested_format)
                    
                    # Send the converted file
                    return send_file(
                        temp_file.name,
                        mimetype=f'audio/{requested_format}',
                        as_attachment=True,
                        download_name=f"{filename.rsplit('.', 1)[0]}.{requested_format}"
                    )
            except Exception as e:
                print(f"Conversion error: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Error converting file format'}), 500

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error streaming song: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to stream song'
        }), 500

@songs.route('/default-album-art.jpg')
def default_album_art():
    try:
        static_dir = os.path.join(current_app.root_path, 'static')
        return send_from_directory(static_dir, 'default-album-art.jpg')
    except Exception as e:
        print(f"Error serving default album art: {str(e)}")
        return '', 404

@songs.route('/api/songs/<int:song_id>', methods=['DELETE', 'OPTIONS'])
def delete_song(song_id):
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Get the auth header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'Token is missing'}), 401
        
        token = auth_header.split(" ")[1]
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = int(data['sub'])
        current_user = User.query.filter_by(id=user_id).first()
        
        if not current_user:
            return jsonify({'message': 'Invalid user'}), 401

        # Find the song
        song = Song.query.filter_by(id=song_id, user_id=current_user.id).first()
        if not song:
            return jsonify({'status': 'error', 'message': 'Song not found'}), 404

        # Delete the file
        try:
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            file_path = os.path.join(uploads_dir, song.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {str(e)}")

        # Delete from database
        db.session.delete(song)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Song deleted successfully'
        })

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error deleting song: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete song'
        }), 500