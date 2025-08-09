import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    try:
        import models  # noqa: F401
    except ImportError:
        pass  # No models yet
    db.create_all()

# Initialize advanced services
try:
    # Redis Cache Manager
    from redis_manager import init_redis
    init_redis(app)
    
    # WebSocket Manager for real-time updates
    from websocket_manager import init_websocket
    socketio = init_websocket(app)
    
    # Security Manager
    from security import init_security
    init_security(app)
    
    # Cloud Services Integration
    from cloud_integration import init_cloud_services
    init_cloud_services(app)
    
    logging.info("✅ All advanced services initialized successfully")
    
except Exception as e:
    logging.error(f"❌ Failed to initialize advanced services: {e}")

# Import routes after app creation
try:
    import routes  # noqa: F401
    import api_fixed  # noqa: F401 - Using fixed API without circular imports
    # import admin  # noqa: F401 - Skip for now due to imports
    logging.info("Routes imported successfully")
except ImportError as e:
    logging.warning(f"Failed to import some modules: {e}")