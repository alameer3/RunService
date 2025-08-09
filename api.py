"""
Advanced API endpoints for VNC Desktop management
واجهات برمجية متقدمة لإدارة سطح مكتب VNC
"""
from flask import jsonify, request, abort
from app import app, db
from models import VNCSession, ConnectionLog
from security import rate_limit_decorator, log_security_event, validate_vnc_password, validate_screen_resolution
from performance import performance_monitor, monitor_request_performance, cached
from datetime import datetime, timedelta
import subprocess
import socket
import json

@app.route('/api/v1/system/health', methods=['GET'])
@rate_limit_decorator(max_requests=30, window_minutes=1)
@monitor_request_performance
def api_system_health():
    """فحص صحة النظام - API متقدم"""
    try:
        metrics = performance_monitor.get_current_metrics()
        alerts = performance_monitor.get_performance_alerts()
        
        health_status = "healthy"
        if len(alerts) > 0:
            severity_levels = [alert['severity'] for alert in alerts]
            if 'critical' in severity_levels:
                health_status = "critical"
            elif 'high' in severity_levels:
                health_status = "warning"
            else:
                health_status = "degraded"
        
        return jsonify({
            'status': 'success',
            'data': {
                'health_status': health_status,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'alerts': alerts,
                'uptime_seconds': metrics.get('application', {}).get('uptime_seconds', 0)
            }
        })
        
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'فشل في فحص صحة النظام',
            'error': str(e)
        }), 500

@app.route('/api/v1/vnc/status', methods=['GET'])
@rate_limit_decorator(max_requests=20, window_minutes=1)
@cached(ttl=30)  # تخزين مؤقت لمدة 30 ثانية
def api_vnc_detailed_status():
    """حالة خادم VNC المفصلة"""
    try:
        # فحص حالة المنفذ
        vnc_running = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5900))
                vnc_running = result == 0
        except:
            pass
        
        # معلومات العمليات النشطة
        processes = []
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if any(proc in line.lower() for proc in ['x11vnc', 'xvfb', 'vnc']):
                    processes.append(line.strip())
        except:
            pass
        
        # آخر جلسة نشطة
        session = VNCSession.query.order_by(VNCSession.last_accessed.desc()).first()
        
        return jsonify({
            'status': 'success',
            'data': {
                'vnc_running': vnc_running,
                'port': 5900,
                'processes_count': len(processes),
                'processes': processes,
                'session_info': {
                    'name': session.session_name if session else None,
                    'last_accessed': session.last_accessed.isoformat() if session and session.last_accessed else None,
                    'resolution': session.screen_resolution if session else '1024x768',
                    'is_active': session.is_active if session else False
                } if session else None,
                'connection_info': {
                    'host': request.host.split(':')[0],
                    'external_url': f"{request.host.split(':')[0]}:5900",
                    'password_protected': True
                }
            }
        })
        
    except Exception as e:
        app.logger.error(f"VNC status check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'فشل في فحص حالة VNC',
            'error': str(e)
        }), 500

@app.route('/api/v1/vnc/start', methods=['POST'])
@rate_limit_decorator(max_requests=5, window_minutes=1)
@monitor_request_performance
def api_start_vnc():
    """بدء تشغيل خادم VNC - API"""
    try:
        data = request.get_json() or {}
        
        # إيقاف أي عمليات VNC سابقة
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        
        # بدء تشغيل VNC الجديد
        vnc_process = subprocess.Popen([
            'python3', 'vnc_replit_solution.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # انتظار قصير للتأكد من بدء التشغيل
        import time
        time.sleep(3)
        
        # فحص النجاح
        vnc_running = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5900))
                vnc_running = result == 0
        except:
            pass
        
        if vnc_running:
            # تحديث قاعدة البيانات
            session = VNCSession.query.first()
            if not session:
                session = VNCSession()
                session.session_name = data.get('session_name', 'Desktop Session')
                session.vnc_port = 5900
                session.screen_resolution = data.get('resolution', '1024x768')
                db.session.add(session)
            
            session.is_active = True
            session.last_accessed = datetime.utcnow()
            db.session.commit()
            
            log_security_event('vnc_start', 'VNC server started successfully', success=True)
            
            return jsonify({
                'status': 'success',
                'message': 'تم بدء تشغيل خادم VNC بنجاح',
                'data': {
                    'port': 5900,
                    'session_id': session.id if session else None,
                    'connection_url': f"{request.host.split(':')[0]}:5900"
                }
            })
        else:
            log_security_event('vnc_start', 'VNC server failed to start', success=False)
            return jsonify({
                'status': 'error',
                'message': 'فشل في بدء تشغيل خادم VNC'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Failed to start VNC: {e}")
        log_security_event('vnc_start', f'VNC start error: {e}', success=False)
        return jsonify({
            'status': 'error',
            'message': 'خطأ في بدء تشغيل خادم VNC',
            'error': str(e)
        }), 500

@app.route('/api/v1/vnc/stop', methods=['POST'])
@rate_limit_decorator(max_requests=5, window_minutes=1)
@monitor_request_performance
def api_stop_vnc():
    """إيقاف خادم VNC - API"""
    try:
        # إيقاف عمليات VNC
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        
        # تحديث قاعدة البيانات
        session = VNCSession.query.first()
        if session:
            session.is_active = False
            db.session.commit()
        
        log_security_event('vnc_stop', 'VNC server stopped successfully', success=True)
        
        return jsonify({
            'status': 'success',
            'message': 'تم إيقاف خادم VNC بنجاح'
        })
        
    except Exception as e:
        app.logger.error(f"Failed to stop VNC: {e}")
        log_security_event('vnc_stop', f'VNC stop error: {e}', success=False)
        return jsonify({
            'status': 'error',
            'message': 'خطأ في إيقاف خادم VNC',
            'error': str(e)
        }), 500

@app.route('/api/v1/settings/vnc', methods=['POST'])
@rate_limit_decorator(max_requests=3, window_minutes=1)
@monitor_request_performance
def api_update_vnc_settings():
    """تحديث إعدادات VNC - API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'بيانات الطلب مطلوبة'
            }), 400
        
        updates = {}
        
        # التحقق من كلمة المرور الجديدة
        if 'password' in data:
            is_valid, message = validate_vnc_password(data['password'])
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            updates['password'] = data['password']
        
        # التحقق من دقة الشاشة الجديدة
        if 'resolution' in data:
            is_valid, message = validate_screen_resolution(data['resolution'])
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            updates['resolution'] = data['resolution']
        
        # تحديث قاعدة البيانات
        session = VNCSession.query.first()
        if not session:
            session = VNCSession()
            session.session_name = "Desktop Session"
            db.session.add(session)
        
        if 'resolution' in updates:
            session.screen_resolution = updates['resolution']
        
        db.session.commit()
        
        log_security_event('settings_update', f'VNC settings updated: {list(updates.keys())}', success=True)
        
        return jsonify({
            'status': 'success',
            'message': 'تم تحديث الإعدادات بنجاح',
            'data': {
                'updated_fields': list(updates.keys()),
                'requires_restart': len(updates) > 0
            }
        })
        
    except Exception as e:
        app.logger.error(f"Failed to update settings: {e}")
        log_security_event('settings_update', f'Settings update error: {e}', success=False)
        return jsonify({
            'status': 'error',
            'message': 'خطأ في تحديث الإعدادات',
            'error': str(e)
        }), 500

@app.route('/api/v1/analytics/dashboard', methods=['GET'])
@rate_limit_decorator(max_requests=10, window_minutes=1)
@cached(ttl=60)  # تخزين مؤقت لمدة دقيقة
def api_analytics_dashboard():
    """بيانات التحليلات للوحة التحكم"""
    try:
        # إحصائيات عامة
        total_sessions = VNCSession.query.count()
        active_sessions = VNCSession.query.filter_by(is_active=True).count()
        
        # إحصائيات الاتصالات
        last_24h = datetime.utcnow() - timedelta(days=1)
        recent_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h
        ).count()
        
        successful_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h,
            ConnectionLog.success == True
        ).count()
        
        # معدل النجاح
        success_rate = (successful_connections / max(recent_connections, 1)) * 100
        
        # الأنشطة الأخيرة
        recent_logs = ConnectionLog.query.order_by(
            ConnectionLog.timestamp.desc()
        ).limit(10).all()
        
        # بيانات الاستخدام اليومي (آخر 7 أيام)
        usage_data = []
        usage_labels = []
        
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_connections = ConnectionLog.query.filter(
                ConnectionLog.timestamp >= day_start,
                ConnectionLog.timestamp < day_end
            ).count()
            
            usage_data.append(day_connections)
            usage_labels.append(date.strftime('%m/%d'))
        
        # عكس القوائم لعرض الأيام من القديم إلى الحديث
        usage_data.reverse()
        usage_labels.reverse()
        
        # معلومات الأداء
        metrics = performance_monitor.get_current_metrics()
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'connections_24h': recent_connections,
                    'success_rate': round(success_rate, 1),
                    'uptime_hours': round(metrics.get('application', {}).get('uptime_seconds', 0) / 3600, 1)
                },
                'usage_chart': {
                    'labels': usage_labels,
                    'data': usage_data
                },
                'recent_activities': [{
                    'id': log.id,
                    'action': log.action,
                    'timestamp': log.timestamp.isoformat(),
                    'success': log.success,
                    'message': log.message,
                    'client_ip': log.client_ip
                } for log in recent_logs],
                'performance': {
                    'cpu_usage': metrics.get('cpu', {}).get('current', 0),
                    'memory_usage': metrics.get('memory', {}).get('percent', 0),
                    'disk_usage': metrics.get('disk', {}).get('percent', 0),
                    'avg_response_time': metrics.get('application', {}).get('avg_response_time', 0)
                }
            }
        })
        
    except Exception as e:
        app.logger.error(f"Analytics dashboard failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'خطأ في جلب بيانات التحليلات',
            'error': str(e)
        }), 500

@app.route('/api/v1/logs/cleanup', methods=['POST'])
@rate_limit_decorator(max_requests=1, window_minutes=5)
@monitor_request_performance
def api_cleanup_logs():
    """تنظيف السجلات القديمة"""
    try:
        data = request.get_json() or {}
        days_to_keep = data.get('days', 7)  # الافتراضي: الاحتفاظ بسجلات آخر 7 أيام
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # حذف السجلات القديمة
        old_logs = ConnectionLog.query.filter(
            ConnectionLog.timestamp < cutoff_date
        ).all()
        
        deleted_count = len(old_logs)
        
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        
        log_security_event('logs_cleanup', f'Cleaned up {deleted_count} old log entries', success=True)
        
        return jsonify({
            'status': 'success',
            'message': f'تم حذف {deleted_count} سجل قديم',
            'data': {
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat()
            }
        })
        
    except Exception as e:
        app.logger.error(f"Log cleanup failed: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({
            'status': 'error',
            'message': 'خطأ في تنظيف السجلات',
            'error': str(e)
        }), 500

# معالج الأخطاء العام للـ API
@app.errorhandler(404)
def api_not_found(error):
    """معالج الخطأ 404 للـ API"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'API endpoint not found',
            'error': 'المسار المطلوب غير موجود'
        }), 404
    return error

@app.errorhandler(429)
def api_rate_limit(error):
    """معالج تجاوز الحد المسموح للطلبات"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Rate limit exceeded',
            'error': 'تم تجاوز الحد المسموح من الطلبات، حاول مرة أخرى لاحقاً'
        }), 429
    return error