# AR Memory Reconstructor Backend

Flask API for transforming photos into 3D AR experiences.

## Quick Setup

1. **Install MongoDB**: Download from https://www.mongodb.com/try/download/community
2. **Start MongoDB**: `net start MongoDB`
3. **Run setup**: `setup_windows.bat`
4. **Start server**: `python run.py`

## Manual Setup

```cmd
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
copy .env.example .env

# Initialize database
python setup_mongodb.py

# Start server
python run.py
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload image
- `POST /api/process/<session_id>` - Start processing
- `GET /api/status/<session_id>` - Get progress
- `GET /api/result/<session_id>` - Get results
- `GET /api/scene/<session_id>` - Download AR scene

## Verification

```cmd
# Check health
python check_health.py

# Test API
curl http://localhost:5000/api/health
```

Server runs at http://localhost:5000