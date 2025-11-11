from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
import json
import os
from datetime import datetime, timezone
import threading
from config import Config

class Database:
    def __init__(self, mongodb_uri=None, database_name=None):
        """Initialize MongoDB connection"""
        self.mongodb_uri = mongodb_uri or Config.MONGODB_URI
        self.database_name = database_name or Config.MONGODB_DATABASE
        self.lock = threading.Lock()
        self._client = None
        self._db = None
        self._init_connection()
        self._init_collections()
    
    def _init_connection(self):
        """Initialize MongoDB connection"""
        try:
            self._client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[self.database_name]
            print(f"Connected to MongoDB: {self.database_name}")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _init_collections(self):
        """Initialize collections and indexes"""
        try:
            # Sessions collection
            sessions = self._db.sessions
            sessions.create_index("session_id", unique=True)
            sessions.create_index("created_at")
            sessions.create_index("status")
            
            # Results collection
            results = self._db.results
            results.create_index("session_id", unique=True)
            results.create_index("created_at")
            
            # Processing logs collection
            logs = self._db.processing_logs
            logs.create_index("session_id")
            logs.create_index("timestamp")
            
            print("MongoDB collections initialized")
        except Exception as e:
            print(f"Error initializing collections: {e}")
    
    def create_session(self, session_id, filename, options):
        """Create a new processing session"""
        try:
            session_doc = {
                'session_id': session_id,
                'filename': filename,
                'options': options,
                'status': 'uploaded',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            result = self._db.sessions.insert_one(session_doc)
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            raise ValueError(f"Session {session_id} already exists")
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
    
    def update_session_status(self, session_id, status):
        """Update session status"""
        try:
            result = self._db.sessions.update_one(
                {'session_id': session_id},
                {
                    '$set': {
                        'status': status,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating session status: {e}")
            return False
    
    def get_session(self, session_id):
        """Get session information"""
        try:
            session = self._db.sessions.find_one({'session_id': session_id})
            if session:
                # Convert ObjectId to string for JSON serialization
                session['_id'] = str(session['_id'])
                return session
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def save_session_result(self, session_id, result_data):
        """Save processing results"""
        try:
            result_doc = {
                'session_id': session_id,
                'quality_score': result_data.get('quality_score', 0),
                'depth_points': result_data.get('depth_points', 0),
                'processing_time': result_data.get('processing_time', 0),
                'scene_complexity': result_data.get('scene_complexity', 0),
                'ar_scene_path': result_data.get('ar_scene_path', ''),
                'preview_path': result_data.get('preview_path', ''),
                'metadata': result_data,
                'created_at': datetime.now(timezone.utc)
            }
            
            # Upsert result
            self._db.results.replace_one(
                {'session_id': session_id},
                result_doc,
                upsert=True
            )
            
            # Update session status
            self.update_session_status(session_id, 'completed')
            
            return True
        except Exception as e:
            print(f"Error saving session result: {e}")
            return False
    
    def get_session_result(self, session_id):
        """Get processing results for a session"""
        try:
            # Get result data
            result = self._db.results.find_one({'session_id': session_id})
            if not result:
                return None
            
            # Get session data
            session = self._db.sessions.find_one({'session_id': session_id})
            
            # Combine data
            combined_result = {
                **result,
                'filename': session.get('filename', '') if session else '',
                'upload_time': session.get('created_at', '') if session else ''
            }
            
            # Convert ObjectId to string
            combined_result['_id'] = str(combined_result['_id'])
            
            return combined_result
        except Exception as e:
            print(f"Error getting session result: {e}")
            return None
    
    def log_processing_step(self, session_id, step, progress, message=''):
        """Log a processing step"""
        try:
            log_doc = {
                'session_id': session_id,
                'step': step,
                'progress': progress,
                'message': message,
                'timestamp': datetime.now(timezone.utc)
            }
            
            self._db.processing_logs.insert_one(log_doc)
            return True
        except Exception as e:
            print(f"Error logging processing step: {e}")
            return False
    
    def get_processing_logs(self, session_id):
        """Get processing logs for a session"""
        try:
            logs = list(self._db.processing_logs.find(
                {'session_id': session_id}
            ).sort('timestamp', 1))
            
            # Convert ObjectIds to strings
            for log in logs:
                log['_id'] = str(log['_id'])
            
            return logs
        except Exception as e:
            print(f"Error getting processing logs: {e}")
            return []
    
    def get_recent_sessions(self, limit=10):
        """Get recent processing sessions"""
        try:
            pipeline = [
                {
                    '$lookup': {
                        'from': 'results',
                        'localField': 'session_id',
                        'foreignField': 'session_id',
                        'as': 'result'
                    }
                },
                {
                    '$unwind': {
                        'path': '$result',
                        'preserveNullAndEmptyArrays': True
                    }
                },
                {
                    '$sort': {'created_at': -1}
                },
                {
                    '$limit': limit
                },
                {
                    '$project': {
                        'session_id': 1,
                        'filename': 1,
                        'status': 1,
                        'options': 1,
                        'created_at': 1,
                        'updated_at': 1,
                        'quality_score': '$result.quality_score',
                        'processing_time': '$result.processing_time'
                    }
                }
            ]
            
            sessions = list(self._db.sessions.aggregate(pipeline))
            
            # Convert ObjectIds to strings
            for session in sessions:
                session['_id'] = str(session['_id'])
            
            return sessions
        except Exception as e:
            print(f"Error getting recent sessions: {e}")
            return []
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            # Total sessions
            total_sessions = self._db.sessions.count_documents({})
            
            # Completed sessions
            completed_sessions = self._db.sessions.count_documents({'status': 'completed'})
            
            # Average processing time
            pipeline_time = [
                {'$match': {'processing_time': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': None, 'avg_time': {'$avg': '$processing_time'}}}
            ]
            time_result = list(self._db.results.aggregate(pipeline_time))
            avg_processing_time = time_result[0]['avg_time'] if time_result else 0
            
            # Average quality score
            pipeline_quality = [
                {'$match': {'quality_score': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': None, 'avg_quality': {'$avg': '$quality_score'}}}
            ]
            quality_result = list(self._db.results.aggregate(pipeline_quality))
            avg_quality_score = quality_result[0]['avg_quality'] if quality_result else 0
            
            return {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'success_rate': (completed_sessions / max(total_sessions, 1)) * 100,
                'average_processing_time': avg_processing_time,
                'average_quality_score': avg_quality_score
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_sessions': 0,
                'completed_sessions': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'average_quality_score': 0
            }
    
    def cleanup_old_sessions(self, days_old=30):
        """Clean up old sessions and their data"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(
                day=datetime.now().day - days_old
            )
            
            # Find old sessions
            old_sessions = list(self._db.sessions.find(
                {'created_at': {'$lt': cutoff_date}},
                {'session_id': 1}
            ))
            
            session_ids = [session['session_id'] for session in old_sessions]
            
            if session_ids:
                # Delete old data
                self._db.processing_logs.delete_many({'session_id': {'$in': session_ids}})
                self._db.results.delete_many({'session_id': {'$in': session_ids}})
                self._db.sessions.delete_many({'session_id': {'$in': session_ids}})
            
            return len(session_ids)
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
            return 0
    
    def get_session_by_status(self, status, limit=None):
        """Get sessions by status"""
        try:
            query = {'status': status}
            cursor = self._db.sessions.find(query).sort('created_at', -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            sessions = list(cursor)
            
            # Convert ObjectIds to strings
            for session in sessions:
                session['_id'] = str(session['_id'])
            
            return sessions
        except Exception as e:
            print(f"Error getting sessions by status: {e}")
            return []
    
    def update_session_metadata(self, session_id, metadata):
        """Update session metadata"""
        try:
            result = self._db.sessions.update_one(
                {'session_id': session_id},
                {
                    '$set': {
                        'metadata': metadata,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating session metadata: {e}")
            return False
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            print("MongoDB connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()