"""
Configuration management for VNC Desktop application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Settings
    SECRET_KEY = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')
    WTF_CSRF_ENABLED = True
    
    # Database Settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///vnc_desktop.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # VNC Server Settings
    VNC_PORT = int(os.getenv('VNC_PORT', '5901'))
    VNC_PASSWORD = os.getenv('VNC_PASSWORD', 'vnc123456')
    VNC_SCREEN_RESOLUTION = os.getenv('VNC_SCREEN_RESOLUTION', '1024x768')
    VNC_DISPLAY = os.getenv('VNC_DISPLAY', ':1')
    
    # External Access Settings
    REPLIT_URL = os.getenv('REPLIT_URL')
    REPL_SLUG = os.getenv('REPL_SLUG')
    REPL_OWNER = os.getenv('REPL_OWNER', os.getenv('USER', 'user'))
    
    # Logging Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Session Settings
    SESSION_TIMEOUT = timedelta(hours=2)
    
    # Performance Settings
    MAX_CONCURRENT_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', '5'))
    PROCESS_MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '30'))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    WTF_CSRF_ENABLED = True
    
    # Override with secure defaults for production
    VNC_PASSWORD = os.getenv('VNC_PASSWORD')  # Must be set in production
    if not VNC_PASSWORD:
        raise ValueError("VNC_PASSWORD must be set in production environment")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'default')
    return config_by_name.get(env, DevelopmentConfig)