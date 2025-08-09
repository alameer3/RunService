"""
تطبيق Flask الرئيسي للنظام
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

logger = logging.getLogger(__name__)

# قاعدة البيانات
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    """إنشاء تطبيق Flask مع جميع الإعدادات"""
    app = Flask(__name__)
    
    # الإعدادات الأساسية
    app.secret_key = os.environ.get('SESSION_SECRET', 'vnc-desktop-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vnc_system.db')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Proxy fix for Replit
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # تهيئة الإضافات
    db.init_app(app)
    socketio.init_app(app)
    
    # تسجيل النماذج وإنشاء الجداول
    with app.app_context():
        try:
            # استيراد النماذج بحيث تُسجل مع SQLAlchemy
            import models
            db.create_all()
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
    
    # تسجيل المسارات
    register_routes(app)
    register_api_routes(app)
    register_websocket_events(app)
    
    # تسجيل Blueprint إضافي
    from web_vnc import register_vnc_web
    register_vnc_web(app)
    
    logger.info("✅ تم إنشاء تطبيق Flask بنجاح")
    return app

def register_routes(app):
    """تسجيل مسارات الويب الرئيسية"""
    
    @app.route('/')
    def home():
        """الصفحة الرئيسية"""
        from vnc_manager import get_vnc_status, get_system_info
        
        vnc_status = get_vnc_status()
        system_info = get_system_info()
        
        return render_template('index.html', 
                             vnc_status=vnc_status,
                             system_info=system_info)
    
    @app.route('/dashboard')
    def dashboard():
        """لوحة التحكم المتقدمة"""
        from vnc_manager import get_detailed_status
        from models import VNCSession, ConnectionLog
        
        status = get_detailed_status()
        sessions = VNCSession.query.order_by(VNCSession.created_at.desc()).limit(10).all()
        recent_logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(20).all()
        
        return render_template('dashboard.html',
                             status=status,
                             sessions=sessions,
                             recent_logs=recent_logs)
    
    @app.route('/apps')
    def applications():
        """مدير التطبيقات"""
        from app_manager import get_installed_apps, get_available_apps
        
        installed = get_installed_apps()
        available = get_available_apps()
        
        return render_template('applications.html',
                             installed_apps=installed,
                             available_apps=available)
    
    @app.route('/settings')
    def settings():
        """إعدادات النظام"""
        from vnc_manager import get_vnc_config
        
        config = get_vnc_config()
        return render_template('settings.html', config=config)
    
    @app.route('/logs')
    def logs():
        """عرض السجلات"""
        from models import SystemLog
        
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(100).all()
        return render_template('logs.html', logs=logs)

def register_api_routes(app):
    """تسجيل مسارات API"""
    
    @app.route('/api/vnc/start', methods=['POST'])
    def api_start_vnc():
        """بدء خادم VNC"""
        try:
            from vnc_manager import start_vnc_server
            result = start_vnc_server()
            
            if result['success']:
                socketio.emit('vnc_status_changed', {'status': 'running'})
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"خطأ في بدء VNC: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/vnc/stop', methods=['POST'])
    def api_stop_vnc():
        """إيقاف خادم VNC"""
        try:
            from vnc_manager import stop_vnc_server
            result = stop_vnc_server()
            
            if result['success']:
                socketio.emit('vnc_status_changed', {'status': 'stopped'})
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"خطأ في إيقاف VNC: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/vnc/status')
    def api_vnc_status():
        """حالة خادم VNC"""
        from vnc_manager import get_vnc_status
        return jsonify(get_vnc_status())
    
    @app.route('/api/system/info')
    def api_system_info():
        """معلومات النظام"""
        from vnc_manager import get_system_info
        return jsonify(get_system_info())
    
    @app.route('/api/apps/install', methods=['POST'])
    def api_install_app():
        """تثبيت تطبيق"""
        try:
            data = request.get_json()
            app_name = data.get('app_name')
            
            from app_manager import install_application
            result = install_application(app_name)
            
            if result['success']:
                socketio.emit('app_installed', {'app': app_name})
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"خطأ في تثبيت التطبيق: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

def register_websocket_events(app):
    """تسجيل أحداث WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("عميل جديد متصل")
        
        # إرسال حالة النظام الحالية
        from vnc_manager import get_vnc_status, get_system_info
        socketio.emit('vnc_status_update', get_vnc_status())
        socketio.emit('system_info_update', get_system_info())
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("عميل منقطع")
    
    @socketio.on('request_status_update')
    def handle_status_request():
        from vnc_manager import get_vnc_status, get_system_info
        socketio.emit('vnc_status_update', get_vnc_status())
        socketio.emit('system_info_update', get_system_info())