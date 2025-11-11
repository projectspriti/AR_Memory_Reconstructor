import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = 'ar-memory-reconstructor-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'
    MODELS_FOLDER = 'models'
    
    # MongoDB settings
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/ar_memory_reconstructor')
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'ar_memory_reconstructor')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        directories = ['uploads', 'processed', 'models']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)