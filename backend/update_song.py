from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.music_platform

result = db.songs.update_one(
    {'_id': '6748200de7606d0d5ccbbf8a'},
    {'$set': {'file_path': 'The_Weeknd___Timeless_with_Playboi_Carti.mp3'}}
)

print(f'Modified {result.modified_count} document(s)')

# List all songs
docs = list(db.songs.find())
print('Found', len(docs), 'songs:')
[print(doc) for doc in docs] 