#!/usr/bin/env python3
"""
MongoDB Atlas Connection Setup Helper
"""

import os
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def validate_atlas_uri(uri):
    """Validate MongoDB Atlas connection string format"""
    atlas_pattern = r'mongodb\+srv://.*\.mongodb\.net/'
    return bool(re.match(atlas_pattern, uri))

def test_connection(uri):
    """Test MongoDB Atlas connection"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        client.close()
        return True, "Connection successful!"
    except ConnectionFailure as e:
        return False, f"Connection failed: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("MongoDB Atlas Setup Helper")
    print("=" * 30)
    print()
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                content = f.read()
            with open('.env', 'w') as f:
                f.write(content)
            print("✓ .env file created")
        else:
            print("✗ .env.example not found")
            return
    
    print("Please follow these steps:")
    print()
    print("1. Go to https://www.mongodb.com/atlas")
    print("2. Create a free account and cluster")
    print("3. Create a database user")
    print("4. Whitelist your IP address")
    print("5. Get your connection string")
    print()
    
    # Get connection string from user
    while True:
        uri = input("Enter your MongoDB Atlas connection string: ").strip()
        
        if not uri:
            print("Please enter a connection string")
            continue
            
        if not validate_atlas_uri(uri):
            print("⚠ This doesn't look like a MongoDB Atlas URI")
            print("Expected format: mongodb+srv://username:password@cluster.mongodb.net/database")
            continue
            
        # Test connection
        print("Testing connection...")
        success, message = test_connection(uri)
        
        if success:
            print(f"✓ {message}")
            
            # Update .env file
            with open('.env', 'r') as f:
                content = f.read()
            
            # Replace the MONGODB_URI line
            updated_content = re.sub(
                r'MONGODB_URI=.*',
                f'MONGODB_URI={uri}',
                content
            )
            
            with open('.env', 'w') as f:
                f.write(updated_content)
            
            print("✓ .env file updated with Atlas connection string")
            
            # Setup collections
            setup_choice = input("\nSetup database collections now? (y/n): ").lower()
            if setup_choice == 'y':
                os.system('python setup_mongodb.py')
            
            print("\n✓ MongoDB Atlas setup complete!")
            print("You can now start the server with: python run.py")
            break
            
        else:
            print(f"✗ {message}")
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                break

if __name__ == '__main__':
    main()