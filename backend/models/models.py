from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, username, email, password=None, _id=None):
        self._id = ObjectId(_id) if _id else ObjectId()
        self.username = username
        self.email = email
        if password:
            logger.debug(f"Generating password hash for user: {username}")
            self.password_hash = generate_password_hash(password)
        else:
            self.password_hash = None
        self.created_at = datetime.utcnow()

    def set_password(self, password):
        logger.debug(f"Setting new password for user: {self.username}")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        logger.debug(f"Checking password for user: {self.username}")
        if not self.password_hash:
            logger.error(f"No password hash found for user: {self.username}")
            return False
        result = check_password_hash(self.password_hash, password)
        if not result:
            logger.error(f"Password check failed for user: {self.username}")
        return result

    @staticmethod
    def from_db_object(db_object):
        if not db_object:
            logger.error("Attempted to create User from None db_object")
            return None
        try:
            user = User(
                username=db_object['username'],
                email=db_object['email'],
                _id=db_object['_id']
            )
            user.password_hash = db_object['password_hash']
            user.created_at = db_object['created_at']
            logger.debug(f"Created User object from db_object for: {user.username}")
            return user
        except KeyError as e:
            logger.error(f"Missing key in db_object: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating User from db_object: {str(e)}")
            return None

    def to_dict(self):
        try:
            return {
                '_id': str(self._id),
                'username': self.username,
                'email': self.email,
                'password_hash': self.password_hash,
                'created_at': self.created_at
            }
        except Exception as e:
            logger.error(f"Error converting User to dict: {str(e)}")
            raise

class Song:
    def __init__(self, title, file_path, user_id, artist=None, album=None, duration=None, cover_art=None, _id=None):
        self._id = str(_id) if _id else str(ObjectId())
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.cover_art = cover_art
        self.file_path = file_path
        self.user_id = str(user_id) if isinstance(user_id, (str, ObjectId)) else user_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def from_db_object(db_object):
        if not db_object:
            return None
        return Song(
            _id=db_object['_id'],
            title=db_object['title'],
            artist=db_object.get('artist'),
            album=db_object.get('album'),
            duration=db_object.get('duration'),
            cover_art=db_object.get('cover_art'),
            file_path=db_object['file_path'],
            user_id=db_object['user_id']
        )

    def to_dict(self):
        return {
            '_id': self._id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'cover_art': self.cover_art,
            'file_path': self.file_path,
            'user_id': self.user_id,
            'created_at': self.created_at
        } 