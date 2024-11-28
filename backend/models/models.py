from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

class User:
    def __init__(self, username, email, password=None, _id=None):
        self._id = ObjectId(_id) if _id else ObjectId()
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.created_at = datetime.utcnow()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def from_db_object(db_object):
        if not db_object:
            return None
        user = User(
            username=db_object['username'],
            email=db_object['email'],
            _id=db_object['_id']
        )
        user.password_hash = db_object['password_hash']
        user.created_at = db_object['created_at']
        return user

    def to_dict(self):
        return {
            '_id': str(self._id),
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }

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