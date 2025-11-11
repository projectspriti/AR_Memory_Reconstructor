#!/usr/bin/env python3
"""AR Memory Reconstructor Backend Server"""

import os
from app import app
from config import Config

def main():
    """Main entry point"""
    # Initialize app with config
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Get host and port from environment
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    
    print(f"Starting AR Memory Reconstructor Backend...")
    print(f"Debug mode: {debug}")
    print(f"Server: http://localhost:{port}")
    print(f"API Base: http://localhost:{port}/api")
    
    # Start the server
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()