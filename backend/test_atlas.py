#!/usr/bin/env python3
"""Simple MongoDB Atlas connection test"""

from pymongo import MongoClient
import ssl

def test_connection():
    # Your Atlas connection string with password
    uri = "mongodb+srv://talavanekarpriti3101_db_user:987654321@cluster0.pgwo0hl.mongodb.net/ar_memory_reconstructor?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
    
    try:
        # Create client with basic settings
        client = MongoClient(uri, serverSelectionTimeoutMS=30000)
        
        # Test connection
        client.admin.command('ping')
        print("✓ MongoDB Atlas connection successful!")
        
        # Test database access
        db = client.ar_memory_reconstructor
        collections = db.list_collection_names()
        print(f"✓ Database access successful. Collections: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == '__main__':
    test_connection()