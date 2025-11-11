from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime
import threading
import time

# from services.image_processor import ImageProcessor
# from services.depth_estimator import DepthEstimator
# from services.scene_generator import SceneGenerator
# from services.ar_exporter import ARExporter
from utils.file_manager import FileManager
from utils.database import Database
from config import Config

app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_object(Config)

# Initialize services
# image_processor = ImageProcessor()
# depth_estimator = DepthEstimator()
# scene_generator = SceneGenerator()
# ar_exporter = ARExporter()
file_manager = FileManager()

# Initialize database connection
try:
    db = Database()
except Exception as e:
    print(f"Database connection failed: {e}")
    db = None

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Processing status storage
processing_status = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db else 'disconnected',
        'services': {
            'api': True,
            'mongodb': db is not None
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload and validate image for processing"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file_manager.is_allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload JPG, PNG, or GIF'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(file_path)
        
        # Get processing options
        options = {
            'enhanced_depth': request.form.get('enhanced_depth', 'true').lower() == 'true',
            'lighting_optimization': request.form.get('lighting_optimization', 'true').lower() == 'true',
            'background_extension': request.form.get('background_extension', 'false').lower() == 'true'
        }
        
        # Initialize processing status
        processing_status[session_id] = {
            'status': 'uploaded',
            'progress': 0,
            'current_step': 'Analyzing Image',
            'steps': [
                'Analyzing Image',
                'Depth Reconstruction', 
                'Scene Generation',
                'Lighting Optimization',
                'AR Preparation'
            ],
            'created_at': datetime.utcnow().isoformat(),
            'file_path': file_path,
            'options': options
        }
        
        # Save to database
        if db:
            db.create_session(session_id, filename, options)
        
        return jsonify({
            'session_id': session_id,
            'status': 'uploaded',
            'message': 'Image uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<session_id>', methods=['POST'])
def start_processing(session_id):
    """Start the AI processing pipeline"""
    try:
        if session_id not in processing_status:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        if processing_status[session_id]['status'] == 'processing':
            return jsonify({'error': 'Processing already in progress'}), 400
        
        # Start processing in background thread
        thread = threading.Thread(target=process_image_pipeline, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        processing_status[session_id]['status'] = 'processing'
        
        return jsonify({
            'session_id': session_id,
            'status': 'processing',
            'message': 'Processing started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>', methods=['GET'])
def get_processing_status(session_id):
    """Get current processing status"""
    try:
        if session_id not in processing_status:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        status = processing_status[session_id]
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/result/<session_id>', methods=['GET'])
def get_result(session_id):
    """Get processing results and AR scene data"""
    try:
        if session_id not in processing_status:
            return jsonify({'error': 'Invalid session ID'}), 404
        
        status = processing_status[session_id]
        if status['status'] != 'completed':
            return jsonify({'error': 'Processing not completed'}), 400
        
        # Get result data from database
        result = db.get_session_result(session_id) if db else None
        
        return jsonify({
            'session_id': session_id,
            'status': 'completed',
            'result': result,
            'ar_scene_url': f'/api/scene/{session_id}',
            'preview_url': f'/api/preview/{session_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scene/<session_id>', methods=['GET'])
def get_ar_scene(session_id):
    """Get AR scene file for viewing"""
    try:
        scene_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}_scene.glb")
        if not os.path.exists(scene_path):
            return jsonify({'error': 'Scene file not found'}), 404
        
        return send_file(scene_path, as_attachment=True, download_name=f"scene_{session_id}.glb")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<session_id>', methods=['GET'])
def get_preview_image(session_id):
    """Get preview image of reconstructed scene"""
    try:
        preview_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{session_id}_preview.jpg")
        if not os.path.exists(preview_path):
            return jsonify({'error': 'Preview not found'}), 404
        
        return send_file(preview_path, mimetype='image/jpeg')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_image_pipeline(session_id):
    """Background processing pipeline"""
    try:
        status = processing_status[session_id]
        file_path = status['file_path']
        options = status['options']
        
        # Simulate processing steps
        import time
        
        # Step 1: Analyze Image (0-20%)
        update_progress(session_id, 0, 'Analyzing Image')
        time.sleep(2)
        update_progress(session_id, 20, 'Analyzing Image')
        
        # Step 2: Depth Reconstruction (20-40%)
        update_progress(session_id, 20, 'Depth Reconstruction')
        time.sleep(2)
        update_progress(session_id, 40, 'Depth Reconstruction')
        
        # Step 3: Scene Generation (40-70%)
        update_progress(session_id, 40, 'Scene Generation')
        time.sleep(2)
        update_progress(session_id, 70, 'Scene Generation')
        
        # Step 4: Lighting Optimization (70-90%)
        update_progress(session_id, 70, 'Lighting Optimization')
        time.sleep(1)
        update_progress(session_id, 90, 'Lighting Optimization')
        
        # Step 5: AR Preparation (90-100%)
        update_progress(session_id, 90, 'AR Preparation')
        time.sleep(1)
        
        # Mock results
        ar_scene_path = f"processed/{session_id}_scene.glb"
        preview_path = f"processed/{session_id}_preview.jpg"
        quality_score = 85
        
        # Save results to database
        result_data = {
            'quality_score': quality_score,
            'depth_points': 1500000,
            'processing_time': 8.0,
            'scene_complexity': 0.7,
            'ar_scene_path': ar_scene_path,
            'preview_path': preview_path
        }
        
        if db:
            db.save_session_result(session_id, result_data)
        
        # Mark as completed
        update_progress(session_id, 100, 'AR Preparation', 'completed')
        
    except Exception as e:
        processing_status[session_id]['status'] = 'error'
        processing_status[session_id]['error'] = str(e)
        print(f"Processing error for session {session_id}: {e}")

def update_progress(session_id, progress, step, status='processing'):
    """Update processing progress"""
    processing_status[session_id].update({
        'progress': progress,
        'current_step': step,
        'status': status,
        'updated_at': datetime.utcnow().isoformat()
    })

# Removed calculate_quality_score function

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)