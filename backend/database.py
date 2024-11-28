from pymongo import MongoClient
import os
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database():
    try:
        # Get MongoDB URI from environment
        MONGO_URI = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
        if not MONGO_URI:
            logger.error("MongoDB URI not found in environment variables")
            raise ValueError("MongoDB URI not configured")
        
        logger.debug(f"Connecting to MongoDB with URI: {MONGO_URI[:20]}...")
        
        # Create client with increased timeout
        client = MongoClient(MONGO_URI, 
                           serverSelectionTimeoutMS=5000,  # 5 second timeout
                           connectTimeoutMS=5000,
                           socketTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Get database name from URI or use default
        db_name = MONGO_URI.split('/')[-1].split('?')[0] or 'music_platform'
        logger.debug(f"Using database: {db_name}")
        
        db = client[db_name]
        
        # Ensure indexes
        try:
            db.users.create_index('username', unique=True)
            db.users.create_index('email', unique=True)
            logger.debug("Database indexes created/verified")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
        
        return db
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

# Initialize database connection
try:
    db = get_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise e
  