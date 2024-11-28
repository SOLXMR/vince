from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file, after_this_request
from werkzeug.utils import secure_filename
from models.models import Song
from auth.auth import token_required
import os
from datetime import datetime
from database import db
from utils.spotify import SpotifyDownloader
import tempfile
from bson import ObjectId
from dotenv import load_dotenv
import logging
import subprocess

# Configure logging
logger = logging.getLogger(__name__)

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
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file type'}), 400

    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        file.save(file_path)

        # Create song record in MongoDB
        title = request.form.get('title', filename)
        new_song = Song(
            title=title,
            file_path=unique_filename,
            user_id=ObjectId(str(current_user._id))
        )
        
        # Insert into MongoDB
        result = db.songs.insert_one(new_song.to_dict())

        return jsonify({
            'message': 'Song uploaded successfully',
            'song': new_song.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            'message': f'Failed to upload song: {str(e)}'
        }), 500

@songs.route('/api/songs/upload/spotify', methods=['POST'])
@token_required
def upload_spotify(current_user):
    try:
        data = request.get_json()
        if not data or 'spotify_url' not in data:
            return jsonify({'message': 'No Spotify URL provided'}), 400

        spotify_url = data['spotify_url']
        logger.debug(f"Uploading Spotify track: {spotify_url} for user: {current_user.username}")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        logger.debug(f"Using uploads directory: {uploads_dir}")
        
        # Check if Spotify credentials are available
        if not os.getenv('SPOTIFY_CLIENT_ID') or not os.getenv('SPOTIFY_CLIENT_SECRET'):
            logger.error("Missing Spotify credentials")
            return jsonify({'message': 'Spotify credentials not configured'}), 500
        
        try:
            # Download the track
            logger.debug("Downloading track from Spotify...")
            track_info = spotify_downloader.download_track(spotify_url, uploads_dir)
            logger.debug(f"Track info received: {track_info}")
            
            # Verify the downloaded file exists
            file_path = os.path.join(uploads_dir, track_info['file_path'])
            if not os.path.exists(file_path):
                logger.error(f"Downloaded file not found at: {file_path}")
                return jsonify({'message': 'Failed to download track: File not found'}), 500
            
            logger.debug(f"File successfully downloaded to: {file_path}")
        except Exception as e:
            logger.error(f"Error during download: {str(e)}")
            return jsonify({'message': f'Failed to download track: {str(e)}'}), 500

        try:
            # Create song record in MongoDB
            new_song = Song(
                title=track_info['title'],
                artist=track_info['artist'],
                album=track_info['album'],
                duration=track_info['duration'],
                cover_art=track_info['cover_art'],
                file_path=track_info['file_path'],
                user_id=str(current_user._id)
            )
            
            # Insert into MongoDB
            logger.debug(f"Saving song to MongoDB: {new_song.to_dict()}")
            result = db.songs.insert_one(new_song.to_dict())
            logger.debug(f"Song saved with ID: {result.inserted_id}")

            return jsonify({
                'message': 'Song uploaded successfully',
                'song': new_song.to_dict()
            }), 201

        except Exception as e:
            logger.error(f"Error saving to MongoDB: {str(e)}")
            # If MongoDB save fails, clean up the downloaded file
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up file after MongoDB error: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up file: {str(cleanup_error)}")
            raise

    except Exception as e:
        logger.error(f"Failed to upload song: {str(e)}")
        return jsonify({
            'message': f'Failed to upload song: {str(e)}'
        }), 500

@songs.route('/api/songs/list', methods=['GET'])
@token_required
def list_songs(current_user):
    try:
        # Find all songs for the current user
        logger.debug(f"Fetching songs for user: {current_user.username} (ID: {current_user._id})")
        
        # Log the query we're about to make
        query = {'user_id': str(current_user._id)}
        logger.debug(f"MongoDB query: {query}")
        
        # Execute the query
        songs_cursor = db.songs.find(query)
        
        # Convert cursor to list and log each song
        songs_list = []
        for song in songs_cursor:
            logger.debug(f"Found song in DB: {song}")
            try:
                song_obj = Song.from_db_object(song)
                if song_obj:
                    songs_list.append(song_obj.to_dict())
                else:
                    logger.error(f"Failed to convert song to object: {song}")
            except Exception as e:
                logger.error(f"Error processing song {song}: {str(e)}")
        
        logger.debug(f"Returning {len(songs_list)} songs")
        
        return jsonify({
            'songs': songs_list
        })
    except Exception as e:
        logger.error(f"Failed to fetch songs: {str(e)}")
        return jsonify({
            'message': f'Failed to fetch songs: {str(e)}'
        }), 500

@songs.route('/api/songs/<song_id>', methods=['DELETE'])
@token_required
def delete_song(current_user, song_id):
    try:
        logger.debug(f"Attempting to delete song {song_id} for user {current_user.username}")
        
        # Find the song
        song_data = db.songs.find_one({
            '_id': song_id,
            'user_id': str(current_user._id)
        })
        
        if not song_data:
            logger.error(f"Song not found: {song_id}")
            return jsonify({'message': 'Song not found'}), 404

        logger.debug(f"Found song to delete: {song_data}")
        song = Song.from_db_object(song_data)

        # Delete the file
        try:
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            file_path = os.path.join(uploads_dir, song.file_path)
            logger.debug(f"Attempting to delete file: {file_path}")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("File deleted successfully")
            else:
                logger.warning("File not found on disk")
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")

        # Delete from MongoDB
        logger.debug("Deleting song from MongoDB")
        result = db.songs.delete_one({'_id': song_id})
        if result.deleted_count > 0:
            logger.debug("Song deleted from MongoDB successfully")
        else:
            logger.error("Failed to delete song from MongoDB")

        return jsonify({
            'message': 'Song deleted successfully'
        })
    except Exception as e:
        logger.error(f"Failed to delete song: {str(e)}")
        return jsonify({
            'message': f'Failed to delete song: {str(e)}'
        }), 500

@songs.route('/api/songs/stream/<song_id>', methods=['GET'])
@token_required
def stream_song(current_user, song_id):
    try:
        # Get the requested format
        requested_format = request.args.get('format', 'mp3')
        logger.debug(f"Streaming song {song_id} in {requested_format} format for user {current_user.username}")
        
        # Find the song by ID
        logger.debug(f"Looking for song with ID: {song_id}")
        logger.debug(f"Current user ID: {current_user._id}")
        
        # Query MongoDB
        query = {
            '_id': song_id,
            'user_id': str(current_user._id)
        }
        logger.debug(f"MongoDB query: {query}")
        
        song_data = db.songs.find_one(query)
        logger.debug(f"MongoDB result: {song_data}")
        
        if not song_data:
            logger.error(f"Song not found: {song_id}")
            return jsonify({'message': 'Song not found'}), 404

        song = Song.from_db_object(song_data)
        logger.debug(f"Found song: {song.title}")
        
        # Get the file path
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        source_path = os.path.join(uploads_dir, song.file_path)
        logger.debug(f"Source file path: {source_path}")
        
        if not os.path.exists(source_path):
            logger.error(f"Source file not found: {source_path}")
            return jsonify({'message': 'File not found'}), 404

        # If MP3 is requested, send the file directly
        if requested_format.lower() == 'mp3':
            logger.debug("Sending MP3 file directly")
            return send_file(source_path, mimetype='audio/mpeg', as_attachment=True, download_name=f"{song.title}.mp3")
        
        # For WAV conversion
        if requested_format.lower() == 'wav':
            try:
                # Create a temporary WAV file
                wav_filename = os.path.splitext(song.file_path)[0] + '.wav'
                output_path = os.path.join(uploads_dir, wav_filename)
                
                logger.debug(f"Converting to WAV: {output_path}")
                
                # Use ffmpeg to convert to WAV
                command = [
                    'ffmpeg', '-y',  # -y to overwrite output file
                    '-i', source_path,
                    '-acodec', 'pcm_s16le',  # Standard WAV format
                    '-ar', '44100',  # Standard sample rate
                    output_path
                ]
                
                logger.debug(f"Running ffmpeg command: {' '.join(command)}")
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if process.returncode != 0:
                    error_output = process.stderr.decode()
                    logger.error(f"FFmpeg conversion failed: {error_output}")
                    return jsonify({'message': 'Conversion failed'}), 500
                
                logger.debug("Conversion successful")
                
                # Send the WAV file
                @after_this_request
                def cleanup(response):
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            logger.debug(f"Cleaned up temporary WAV file: {output_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning up WAV file: {str(e)}")
                    return response
                
                return send_file(output_path, mimetype='audio/wav', as_attachment=True, download_name=f"{song.title}.wav")
            
            except Exception as e:
                logger.error(f"Error during WAV conversion: {str(e)}")
                return jsonify({'message': f'Conversion failed: {str(e)}'}), 500
        
        # Unsupported format
        logger.error(f"Unsupported format requested: {requested_format}")
        return jsonify({'message': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Error streaming song: {str(e)}")
        return jsonify({'message': f'Error streaming song: {str(e)}'}), 500