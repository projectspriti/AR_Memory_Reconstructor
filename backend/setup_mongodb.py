#!/usr/bin/env python3
"""MongoDB Setup Script for AR Memory Reconstructor"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import Config

def main():
    try:
        # Connect to MongoDB (Atlas or local)
        if 'mongodb+srv' in Config.MONGODB_URI:
            client = MongoClient(
                Config.MONGODB_URI, 
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
        else:
            client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        client.admin.command('ping')
        print("✓ Connected to MongoDB Atlas")
        
        # Get database
        db = client[Config.MONGODB_DATABASE]
        
        # Create collections and indexes
        print("Setting up collections...")
        
        # Sessions collection
        sessions = db.sessions
        sessions.create_index("session_id", unique=True)
        sessions.create_index("created_at")
        print("✓ Sessions collection")
        
        # Results collection
        results = db.results
        results.create_index("session_id", unique=True)
        results.create_index("created_at")
        print("✓ Results collection")
        
        # Processing logs collection
        logs = db.processing_logs
        logs.create_index("session_id")
        logs.create_index("timestamp")
        print("✓ Processing logs collection")
        
        print("\n✓ MongoDB setup complete!")
        client.close()
        
    except ConnectionFailure:
        print("✗ Cannot connect to MongoDB")
        print("Please start MongoDB: net start MongoDB")
    except Exception as e:
        print(f"✗ Setup failed: {e}")

if __name__ == '__main__':
    main()