from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def test_connection():
    try:
        # Get MongoDB URI from environment variable
        uri = os.getenv('MONGODB_URI')
        print(f"Connecting to MongoDB at: {uri}")
        
        # Create a new client and connect to the server
        client = MongoClient(uri)
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        # List all databases
        print("\nAvailable databases:")
        for db in client.list_databases():
            print(f"- {db['name']}")
            
        # Use the music_platform database
        db = client.music_platform
        
        # List all collections
        print("\nCollections in music_platform:")
        for collection in db.list_collections():
            print(f"- {collection['name']}")
            
        # Count documents in each collection
        print("\nDocument counts:")
        for collection in db.list_collections():
            name = collection['name']
            count = db[name].count_documents({})
            print(f"- {name}: {count} documents")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_connection() 