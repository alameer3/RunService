"""
Advanced administrative features for VNC Desktop management
مزايا إدارية متقدمة لإدارة سطح مكتب VNC
"""
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from app import app, db
from models import VNCSession, ConnectionLog
from security import rate_limit_decorator, log_security_event, SecurityHeaders
from performance import performance_monitor, cache_manager
from datetime import datetime, timedelta
import subprocess
import json
import os

def requires_admin():
    """فحص صلاحيات الإدارة"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # في بيئة التطوير، السماح لجميع المستخدمين
            if os.getenv('REPLIT_DEV_DOMAIN'):
                return f(*args, **kwargs)
            
            # فحص الجلسة الإدارية
            if 'admin_authenticated' not in session:
                return redirect(url_for('admin_login'))
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/admin')
@requires_admin()
def admin_dashboard():
    """لوحة التحكم الإدارية الرئيسية"""
    try:
        # إحصائيات عامة
        total_sessions = VNCSession.query.count()
        active_sessions = VNCSession.query.filter_by(is_active=True).count()
        
        # إحصائيات آخر 24 ساعة
        last_24h = datetime.utcnow() - timedelta(days=1)
        recent_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h
        ).count()
        
        successful_connections = ConnectionLog.query.filter(
            ConnectionLog.timestamp >= last_24h,
            ConnectionLog.success == True
        ).count()
        
        error_connections = recent_connections - successful_connections
        success_rate = (successful_connections / max(recent_connections, 1)) * 100
        
        # أحدث الأنشطة
        recent_activities = ConnectionLog.query.order_by(
            ConnectionLog.timestamp.desc()
        ).limit(15).all()
        
        # معلومات الأداء
        metrics = performance_monitor.get_current_metrics()
        alerts = performance_monitor.get_performance_alerts()
        
        # إحصائيات التخزين المؤقت
        cache_stats = cache_manager.get_stats()
        
        return render_template('admin/dashboard.html',
                             total_sessions=total_sessions,
                             active_sessions=active_sessions,
                             recent_connections=recent_connections,
                             successful_connections=successful_connections,
                             error_connections=error_connections,
                             success_rate=round(success_rate, 1),
                             recent_activities=recent_activities,
                             metrics=metrics,
                             alerts=alerts,
                             cache_stats=cache_stats)
        
    except Exception as e:
        app.logger.error(f"Admin dashboard error: {e}")
        flash(f'خطأ في تحميل لوحة التحكم: {e}', 'error')
        return redirect(url_for('home'))

@app.route('/admin/analytics')
@requires_admin()
def admin_analytics():
    """صفحة التحليلات المتقدمة"""
    try:
        # بيانات الاستخدام اليومي (آخر 30 يوم)
        usage_data = []
        usage_labels = []
        
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_connections = ConnectionLog.query.filter(
                ConnectionLog.timestamp >= day_start,
                ConnectionLog.timestamp < day_end
            ).count()
            
            usage_data.append(day_connections)
            usage_labels.append(date.strftime('%m/%d'))
        
        # عكس القوائم لعرض التواريخ بشكل صحيح
        usage_data.reverse()
        usage_labels.reverse()
        
        # إحصائيات متقدمة
        metrics = performance_monitor.get_current_metrics()
        uptime_hours = round(metrics.get('application', {}).get('uptime_seconds', 0) / 3600, 1)
        
        # أكثر الأنشطة شيوعاً
        activity_stats = db.session.query(
            ConnectionLog.action,
            db.func.count(ConnectionLog.action).label('count')
        ).group_by(ConnectionLog.action).order_by(
            db.func.count(ConnectionLog.action).desc()
        ).limit(10).all()
        
        # أوقات الذروة
        hour_stats = db.session.query(
            db.func.extract('hour', ConnectionLog.timestamp).label('hour'),
            db.func.count(ConnectionLog.id).label('count')
        ).group_by(
            db.func.extract('hour', ConnectionLog.timestamp)
        ).order_by(
            db.func.count(ConnectionLog.id).desc()
        ).limit(5).all()
        
        peak_usage_time = f"{int(hour_stats[0].hour):02d}:00" if hour_stats else "غير متوفر"
        
        return render_template('analytics.html',
                             total_sessions=VNCSession.query.count(),
                             active_connections=VNCSession.query.filter_by(is_active=True).count(),
                             uptime_hours=uptime_hours,
                             avg_response_time=round(metrics.get('application', {}).get('avg_response_time', 0)),
                             connection_success_rate=round(metrics.get('application', {}).get('error_rate', 0)),
                             avg_session_duration=30,  # يمكن حسابها بدقة أكثر
                             peak_usage_time=peak_usage_time,
                             memory_usage=round(metrics.get('memory', {}).get('percent', 0)),
                             usage_labels=usage_labels,
                             usage_data=usage_data)
        
    except Exception as e:
        app.logger.error(f"Analytics page error: {e}")
        flash(f'خطأ في تحميل صفحة التحليلات: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/system', methods=['GET'])
@requires_admin()
def admin_system():
    """إدارة النظام"""
    try:
        # معلومات النظام التفصيلية
        metrics = performance_monitor.get_current_metrics()
        alerts = performance_monitor.get_performance_alerts()
        
        # معلومات العمليات النشطة
        processes = []
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if any(proc in line.lower() for proc in ['vnc', 'python', 'gunicorn']):
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            'pid': parts[1],
                            'cpu': parts[2],
                            'memory': parts[3],
                            'command': ' '.join(parts[10:])[:80] + '...' if len(' '.join(parts[10:])) > 80 else ' '.join(parts[10:])
                        })
        except Exception as e:
            app.logger.error(f"Failed to get processes: {e}")
        
        # معلومات قاعدة البيانات
        db_stats = {
            'sessions_count': VNCSession.query.count(),
            'logs_count': ConnectionLog.query.count(),
            'logs_size_mb': 0  # يمكن حسابها بدقة أكثر
        }
        
        return render_template('admin/system.html',
                             metrics=metrics,
                             alerts=alerts,
                             processes=processes,
                             db_stats=db_stats)
        
    except Exception as e:
        app.logger.error(f"System page error: {e}")
        flash(f'خطأ في تحميل صفحة النظام: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/system/cleanup', methods=['POST'])
@requires_admin()
@rate_limit_decorator(max_requests=3, window_minutes=5)
def admin_system_cleanup():
    """تنظيف النظام"""
    try:
        data = request.get_json() or {}
        cleanup_type = data.get('type', 'logs')
        
        if cleanup_type == 'logs':
            # تنظيف السجلات القديمة
            days_to_keep = data.get('days', 7)
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            old_logs = ConnectionLog.query.filter(
                ConnectionLog.timestamp < cutoff_date
            ).all()
            
            deleted_count = len(old_logs)
            for log in old_logs:
                db.session.delete(log)
            
            db.session.commit()
            
            log_security_event('admin_cleanup', f'Cleaned {deleted_count} old logs', success=True)
            
            return jsonify({
                'success': True,
                'message': f'تم حذف {deleted_count} سجل قديم'
            })
            
        elif cleanup_type == 'cache':
            # تنظيف التخزين المؤقت
            cache_manager.clear()
            
            log_security_event('admin_cleanup', 'Cache cleared', success=True)
            
            return jsonify({
                'success': True,
                'message': 'تم مسح التخزين المؤقت'
            })
            
        elif cleanup_type == 'performance':
            # إعادة تعيين مراقب الأداء
            performance_monitor.cleanup_old_data()
            
            log_security_event('admin_cleanup', 'Performance data cleaned', success=True)
            
            return jsonify({
                'success': True,
                'message': 'تم تنظيف بيانات الأداء'
            })
        
        else:
            return jsonify({
                'success': False,
                'message': 'نوع التنظيف غير مدعوم'
            })
        
    except Exception as e:
        app.logger.error(f"System cleanup error: {e}")
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'success': False,
            'message': f'خطأ في تنظيف النظام: {e}'
        })

@app.route('/admin/sessions', methods=['GET'])
@requires_admin()
def admin_sessions():
    """إدارة الجلسات"""
    try:
        sessions = VNCSession.query.order_by(VNCSession.last_accessed.desc()).all()
        
        # إحصائيات الجلسات
        active_count = len([s for s in sessions if s.is_active])
        inactive_count = len(sessions) - active_count
        
        return render_template('admin/sessions.html',
                             sessions=sessions,
                             active_count=active_count,
                             inactive_count=inactive_count)
        
    except Exception as e:
        app.logger.error(f"Sessions page error: {e}")
        flash(f'خطأ في تحميل صفحة الجلسات: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/export', methods=['GET'])
@requires_admin()
def admin_export():
    """تصدير البيانات"""
    try:
        export_type = request.args.get('type', 'logs')
        
        if export_type == 'logs':
            # تصدير السجلات
            logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(1000).all()
            
            data = [{
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'success': log.success,
                'message': log.message,
                'client_ip': log.client_ip
            } for log in logs]
            
            response = jsonify(data)
            response.headers['Content-Disposition'] = f'attachment; filename=vnc_logs_{datetime.now().strftime("%Y%m%d")}.json'
            
        elif export_type == 'sessions':
            # تصدير الجلسات
            sessions = VNCSession.query.all()
            
            data = [{
                'id': session.id,
                'session_name': session.session_name,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'last_accessed': session.last_accessed.isoformat() if session.last_accessed else None,
                'is_active': session.is_active,
                'vnc_port': session.vnc_port,
                'screen_resolution': session.screen_resolution
            } for session in sessions]
            
            response = jsonify(data)
            response.headers['Content-Disposition'] = f'attachment; filename=vnc_sessions_{datetime.now().strftime("%Y%m%d")}.json'
            
        elif export_type == 'system':
            # تصدير معلومات النظام
            metrics = performance_monitor.get_current_metrics()
            
            data = {
                'export_date': datetime.now().isoformat(),
                'system_metrics': metrics,
                'database_stats': {
                    'sessions_count': VNCSession.query.count(),
                    'logs_count': ConnectionLog.query.count()
                }
            }
            
            response = jsonify(data)
            response.headers['Content-Disposition'] = f'attachment; filename=vnc_system_{datetime.now().strftime("%Y%m%d")}.json'
            
        else:
            flash('نوع التصدير غير مدعوم', 'error')
            return redirect(url_for('admin_dashboard'))
        
        log_security_event('admin_export', f'Data exported: {export_type}', success=True)
        
        return response
        
    except Exception as e:
        app.logger.error(f"Export error: {e}")
        flash(f'خطأ في تصدير البيانات: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """تسجيل دخول الإدارة"""
    if request.method == 'POST':
        # في بيئة التطوير، تسجيل دخول مبسط
        if os.getenv('REPLIT_DEV_DOMAIN'):
            session['admin_authenticated'] = True
            log_security_event('admin_login', 'Admin login successful (dev mode)', success=True)
            return redirect(url_for('admin_dashboard'))
        
        # يمكن إضافة نظام تسجيل دخول حقيقي لاحقاً
        flash('نظام تسجيل الدخول غير مُفعل', 'warning')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج الإدارة"""
    session.pop('admin_authenticated', None)
    log_security_event('admin_logout', 'Admin logout', success=True)
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('home'))