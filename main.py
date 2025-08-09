#!/usr/bin/env python3
"""
Main entry point for VNC Desktop Flask Application
"""
import os
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import routes to register them
import routes  # noqa: F401

def main():
    """Main function to run the Flask app"""
    try:
        # Get configuration from environment
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '5000'))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        logger.info(f"Starting VNC Desktop Flask App on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the application
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise

if __name__ == '__main__':
    main()