import os
import logging
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create required directories
BASE_DIR = Path(__file__).parent.absolute()
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static" 
LOGS_DIR = BASE_DIR / "logs"
INSTANCE_DIR = BASE_DIR / "instance"

for directory in [TEMPLATES_DIR, STATIC_DIR, LOGS_DIR, INSTANCE_DIR]:
    directory.mkdir(exist_ok=True)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO(cors_allowed_origins="*")

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "vnc-desktop-secret-key-2024")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/vnc_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with extensions
db.init_app(app)
socketio.init_app(app)

# Import and register routes
def register_routes():
    """Register Flask routes"""
    
    @app.route('/')
    def home():
        """الصفحة الرئيسية"""
        try:
            # Get system status safely
            vnc_status = {"active": False, "display": ":1", "port": 5901}
            system_info = {"cpu": "N/A", "memory": "N/A", "disk": "N/A"}
            
            return render_template('index.html', 
                                 vnc_status=vnc_status,
                                 system_info=system_info)
        except Exception as e:
            logger.error(f"Error in home route: {e}")
            return f"خطأ في تحميل الصفحة الرئيسية: {e}", 500
    
    @app.route('/dashboard')
    def dashboard():
        """لوحة التحكم"""
        return render_template('dashboard.html')
    
    @app.route('/vnc')
    def vnc_viewer():
        """عارض VNC"""
        return render_template('vnc_viewer.html')
    
    @app.route('/applications')
    def applications():
        """إدارة التطبيقات"""
        return render_template('applications.html')
    
    @app.route('/logs')
    def logs_view():
        """عرض السجلات"""
        return render_template('logs.html')
    
    @app.route('/settings')
    def settings():
        """الإعدادات"""
        return render_template('settings.html')
    
    @app.route('/api/status')
    def api_status():
        """API حالة النظام"""
        return jsonify({
            "status": "running",
            "vnc_active": False,
            "system": "ok"
        })

def register_socketio_events():
    """Register SocketIO events"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected to SocketIO')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected from SocketIO')

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    
    try:
        db.create_all()
        logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

# Register routes and events
register_routes()
register_socketio_events()
