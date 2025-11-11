import os
import shutil
from werkzeug.utils import secure_filename
import mimetypes

class FileManager:
    def __init__(self):
        """Initialize file manager"""
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB
    
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def validate_image_file(self, file):
        """Validate uploaded image file"""
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        if not self.is_allowed_file(file.filename):
            return False, f"File type not allowed. Supported: {', '.join(self.allowed_extensions)}"
        
        # Check file size (if possible)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.max_file_size:
            return False, f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
        
        return True, "File is valid"
    
    def save_uploaded_file(self, file, upload_folder, session_id):
        """Save uploaded file with secure filename"""
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, f"{session_id}_{filename}")
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        file.save(file_path)
        return file_path
    
    def cleanup_session_files(self, session_id, folders):
        """Clean up files associated with a session"""
        for folder in folders:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    if filename.startswith(session_id):
                        file_path = os.path.join(folder, filename)
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
    
    def get_file_info(self, file_path):
        """Get information about a file"""
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            'path': file_path,
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'mime_type': mime_type,
            'extension': os.path.splitext(file_path)[1].lower()
        }
    
    def create_directory_structure(self, base_path):
        """Create necessary directory structure"""
        directories = [
            'uploads',
            'processed',
            'models',
            'temp',
            'exports'
        ]
        
        for directory in directories:
            dir_path = os.path.join(base_path, directory)
            os.makedirs(dir_path, exist_ok=True)
    
    def get_storage_usage(self, directories):
        """Get storage usage statistics"""
        usage = {}
        total_size = 0
        
        for directory in directories:
            if os.path.exists(directory):
                dir_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)
                            dir_size += size
                            file_count += 1
                        except OSError:
                            pass
                
                usage[directory] = {
                    'size_bytes': dir_size,
                    'size_mb': dir_size / (1024 * 1024),
                    'file_count': file_count
                }
                total_size += dir_size
        
        usage['total'] = {
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024)
        }
        
        return usage