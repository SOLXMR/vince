from pymongo import MongoClient
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database():
    try:
        MONGO_URI = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        logger.debug(f"Connecting to MongoDB at: {MONGO_URI}")
        client = MongoClient(MONGO_URI)
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        return client.music_platform
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

# Initialize database connection
db = get_database() 