from pydub import AudioSegment
import os
from flask import current_app
import magic

def convert_to_wav(mp3_path):
    """Convert MP3 file to WAV format"""
    try:
        # Generate WAV filename
        wav_filename = os.path.splitext(os.path.basename(mp3_path))[0] + '.wav'
        wav_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'wav', wav_filename)
        
        # Ensure WAV directory exists
        os.makedirs(os.path.dirname(wav_path), exist_ok=True)
        
        # Load MP3 and export as WAV
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format='wav')
        
        return wav_path
    except Exception as e:
        current_app.logger.error(f"Error converting file to WAV: {str(e)}")
        return None

def validate_audio_file(file):
    """Validate that the uploaded file is an MP3"""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(file.read())
        file.seek(0)  # Reset file pointer
        
        if file_type != 'audio/mpeg':
            return False, "File must be an MP3"
        
        return True, None
    except Exception as e:
        return False, str(e)

def get_audio_metadata(file_path):
    """Extract metadata from audio file"""
    try:
        audio = AudioSegment.from_mp3(file_path)
        return {
            'duration': len(audio) // 1000,  # Convert to seconds
            'bitrate': audio.frame_rate * audio.sample_width * 8 * audio.channels
        }
    except Exception as e:
        current_app.logger.error(f"Error extracting metadata: {str(e)}")
        return None 