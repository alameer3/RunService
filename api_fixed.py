"""
REST API endpoints for VNC Desktop Server
واجهات API REST لخادم سطح مكتب VNC - Fixed Version
"""
from flask import jsonify, request, abort
from app import app, db
from models import VNCSession, ConnectionLog
from security import rate_limit_decorator, log_security_event, validate_vnc_password, validate_screen_resolution
from datetime import datetime, timedelta
import subprocess
import socket
import json

@app.route('/api/v1/system/health', methods=['GET'])
@rate_limit_decorator(max_requests=30, window_minutes=1)
def api_system_health():
    """فحص صحة النظام - API متقدم"""
    try:
        # فحص قاعدة البيانات
        db_status = False
        try:
            db.session.execute('SELECT 1')
            db_status = True
        except Exception as e:
            app.logger.error(f"Database health check failed: {e}")
        
        # فحص Redis
        redis_status = False
        try:
            from redis_manager import redis_manager
            redis_status = redis_manager.is_connected()
        except:
            pass
        
        # فحص VNC
        vnc_status = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5900))
                vnc_status = result == 0
        except:
            pass
        
        # معلومات الأداء
        system_metrics = {}
        try:
            import psutil
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except:
            pass
        
        health_data = {
            'status': 'healthy' if db_status else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': db_status,
                'redis': redis_status,
                'vnc_server': vnc_status,
                'web_server': True  # إذا وصلنا هنا فالويب يعمل
            },
            'metrics': system_metrics,
            'uptime': 'unknown'
        }
        
        # تسجيل فحص الصحة
        log_security_event('health_check', 'System health checked via API', success=True)
        
        return jsonify(health_data)
        
    except Exception as e:
        app.logger.error(f"Health check API error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/v1/vnc/status', methods=['GET'])
@rate_limit_decorator(max_requests=20, window_minutes=1)
def api_vnc_status():
    """حالة خادم VNC"""
    try:
        # فحص المنفذ
        vnc_running = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5900))
                vnc_running = result == 0
        except:
            pass
        
        # معلومات الجلسات
        total_sessions = VNCSession.query.count()
        active_sessions = VNCSession.query.filter_by(is_active=True).count()
        
        return jsonify({
            'vnc_server': {
                'running': vnc_running,
                'port': 5900,
                'url': 'vnc://localhost:5900'
            },
            'sessions': {
                'total': total_sessions,
                'active': active_sessions
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"VNC status API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/sessions', methods=['GET'])
@rate_limit_decorator(max_requests=10, window_minutes=1)
def api_sessions_list():
    """قائمة جلسات VNC"""
    try:
        sessions = VNCSession.query.order_by(VNCSession.last_accessed.desc()).all()
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'name': session.session_name,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'last_accessed': session.last_accessed.isoformat() if session.last_accessed else None,
                'is_active': session.is_active,
                'port': session.vnc_port,
                'resolution': session.screen_resolution
            })
        
        return jsonify({
            'sessions': sessions_data,
            'total': len(sessions_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Sessions list API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/logs', methods=['GET'])
@rate_limit_decorator(max_requests=5, window_minutes=1)
def api_logs_recent():
    """السجلات الحديثة"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)  # حد أقصى 100
        
        logs = ConnectionLog.query.order_by(
            ConnectionLog.timestamp.desc()
        ).limit(limit).all()
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'success': log.success,
                'message': log.message,
                'client_ip': log.client_ip
            })
        
        return jsonify({
            'logs': logs_data,
            'count': len(logs_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Logs API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/stats', methods=['GET'])
@rate_limit_decorator(max_requests=10, window_minutes=1) 
def api_stats():
    """إحصائيات عامة"""
    try:
        # إحصائيات الجلسات
        total_sessions = VNCSession.query.count()
        active_sessions = VNCSession.query.filter_by(is_active=True).count()
        
        # إحصائيات آخر 24 ساعة
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h
        ).count()
        
        successful_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h,
            ConnectionLog.success == True
        ).count()
        
        # حساب معدل النجاح
        success_rate = 0
        if recent_connections > 0:
            success_rate = (successful_connections / recent_connections) * 100
        
        stats_data = {
            'sessions': {
                'total': total_sessions,
                'active': active_sessions,
                'inactive': total_sessions - active_sessions
            },
            'connections_24h': {
                'total': recent_connections,
                'successful': successful_connections,
                'failed': recent_connections - successful_connections,
                'success_rate': round(success_rate, 2)
            },
            'system': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # إضافة معلومات النظام إذا متوفرة
        try:
            import psutil
            stats_data['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except:
            pass
        
        return jsonify(stats_data)
        
    except Exception as e:
        app.logger.error(f"Stats API error: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket status for real-time updates
@app.route('/api/v1/websocket/status', methods=['GET'])
def api_websocket_status():
    """حالة WebSocket"""
    try:
        websocket_data = {
            'enabled': True,
            'endpoint': '/socket.io',
            'connected_clients': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # محاولة الحصول على معلومات WebSocket
        try:
            from websocket_manager import websocket_manager
            websocket_data['connected_clients'] = websocket_manager.get_connected_clients_count()
        except:
            pass
        
        return jsonify(websocket_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500