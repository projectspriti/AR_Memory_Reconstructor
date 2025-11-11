#!/usr/bin/env python3
"""
Quick script to update MongoDB Atlas password in .env file
"""

import os
import re

def main():
    print("MongoDB Atlas Password Setup")
    print("=" * 30)
    
    # Get password from user
    password = input("Enter your MongoDB Atlas database password: ").strip()
    
    if not password:
        print("Password cannot be empty!")
        return
    
    # Read .env file
    if not os.path.exists('.env'):
        print("Error: .env file not found!")
        return
    
    with open('.env', 'r') as f:
        content = f.read()
    
    # Replace <db_password> with actual password
    updated_content = content.replace('<db_password>', password)
    
    # Write back to .env
    with open('.env', 'w') as f:
        f.write(updated_content)
    
    print("✓ Password updated in .env file")
    
    # Test connection
    print("\nTesting MongoDB Atlas connection...")
    try:
        from pymongo import MongoClient
        from config import Config
        
        # Load the updated config
        import importlib
        import config
        importlib.reload(config)
        
        client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        client.close()
        
        print("✓ MongoDB Atlas connection successful!")
        
        # Setup collections
        setup = input("\nSetup database collections? (y/n): ").lower()
        if setup == 'y':
            os.system('python setup_mongodb.py')
        
        print("\n✅ MongoDB Atlas setup complete!")
        print("You can now start the server with: python run.py")
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease check:")
        print("1. Your password is correct")
        print("2. Your IP is whitelisted in MongoDB Atlas")
        print("3. Your database user has proper permissions")

if __name__ == '__main__':
    main()