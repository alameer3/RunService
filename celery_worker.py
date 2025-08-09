"""
Celery Background Worker for VNC Desktop
عامل الخلفية Celery لسطح مكتب VNC
"""
from celery import Celery
import os
import logging
from datetime import datetime, timedelta
from redis_manager import redis_manager
from performance import performance_monitor

# إعداد Celery
def make_celery():
    """إنشاء تطبيق Celery"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        'vnc_worker',
        broker=redis_url,
        backend=redis_url,
        include=['celery_worker']
    )
    
    # إعداد Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # إعدادات المهام
        task_routes={
            'vnc_worker.cleanup_old_data': {'queue': 'maintenance'},
            'vnc_worker.system_health_check': {'queue': 'monitoring'},
            'vnc_worker.backup_database': {'queue': 'backup'},
            'vnc_worker.send_metrics_to_cloud': {'queue': 'cloud'}
        },
        
        # جدولة المهام الدورية
        beat_schedule={
            # تنظيف البيانات القديمة كل ساعة
            'cleanup-old-data': {
                'task': 'vnc_worker.cleanup_old_data',
                'schedule': 3600.0,  # كل ساعة
            },
            
            # فحص صحة النظام كل 5 دقائق
            'system-health-check': {
                'task': 'vnc_worker.system_health_check',
                'schedule': 300.0,  # كل 5 دقائق
            },
            
            # نسخة احتياطية يومية
            'daily-backup': {
                'task': 'vnc_worker.backup_database',
                'schedule': 86400.0,  # كل 24 ساعة
            },
            
            # إرسال المقاييس للسحابة كل 10 دقائق
            'send-metrics-to-cloud': {
                'task': 'vnc_worker.send_metrics_to_cloud',
                'schedule': 600.0,  # كل 10 دقائق
            }
        }
    )
    
    return celery

# إنشاء تطبيق Celery
celery = make_celery()

@celery.task(bind=True)
def cleanup_old_data(self):
    """مهمة تنظيف البيانات القديمة"""
    try:
        from app import app, db
        from models import ConnectionLog
        
        with app.app_context():
            # حذف السجلات الأقدم من 30 يوم
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_logs = ConnectionLog.query.filter(
                ConnectionLog.timestamp < cutoff_date
            ).all()
            
            deleted_count = len(old_logs)
            
            for log in old_logs:
                db.session.delete(log)
            
            db.session.commit()
            
            # تنظيف Redis cache
            expired_count = 0
            if redis_manager.is_connected():
                from redis_manager import cache_manager
                expired_count = cache_manager.cleanup_expired()
            
            # تنظيف بيانات الأداء القديمة
            performance_monitor.cleanup_old_data()
            
            result = {
                'task': 'cleanup_old_data',
                'deleted_logs': deleted_count,
                'cleaned_cache_items': expired_count,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            logging.info(f"Cleanup completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Cleanup task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery.task(bind=True)
def system_health_check(self):
    """مهمة فحص صحة النظام"""
    try:
        # فحص مقاييس الأداء
        metrics = performance_monitor.get_current_metrics()
        alerts = performance_monitor.get_performance_alerts()
        
        # فحص اتصال قاعدة البيانات
        database_healthy = False
        try:
            from app import app, db
            with app.app_context():
                db.session.execute('SELECT 1')
                database_healthy = True
        except:
            database_healthy = False
        
        # فحص Redis
        redis_healthy = redis_manager.is_connected()
        
        # فحص VNC Server
        vnc_healthy = False
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5900))
                vnc_healthy = result == 0
        except:
            vnc_healthy = False
        
        health_status = {
            'task': 'system_health_check',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': database_healthy,
                'redis': redis_healthy,
                'vnc_server': vnc_healthy
            },
            'metrics': {
                'cpu_usage': metrics.get('cpu', {}).get('current', 0),
                'memory_usage': metrics.get('memory', {}).get('percent', 0),
                'disk_usage': metrics.get('disk', {}).get('percent', 0)
            },
            'alerts_count': len(alerts),
            'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical'])
        }
        
        # حفظ في Redis للمراقبة
        if redis_manager.is_connected():
            redis_manager.set_cache('system:health_status', health_status, ttl=900)  # 15 دقيقة
        
        # إرسال تنبيه في حالة وجود مشاكل حرجة
        critical_issues = []
        if not database_healthy:
            critical_issues.append('Database connection failed')
        if health_status['metrics']['cpu_usage'] > 90:
            critical_issues.append(f"High CPU usage: {health_status['metrics']['cpu_usage']}%")
        if health_status['metrics']['memory_usage'] > 95:
            critical_issues.append(f"High memory usage: {health_status['metrics']['memory_usage']}%")
        
        if critical_issues:
            # إرسال تنبيه للسحابة
            send_critical_alert.delay('system_health', '; '.join(critical_issues))
        
        logging.info(f"Health check completed: {len(critical_issues)} issues found")
        return health_status
        
    except Exception as e:
        logging.error(f"Health check task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery.task(bind=True)
def backup_database(self):
    """مهمة النسخ الاحتياطي لقاعدة البيانات"""
    try:
        from cloud_integration import aws_manager
        
        if not aws_manager.is_connected():
            logging.warning("AWS not connected, skipping backup")
            return {'status': 'skipped', 'reason': 'AWS not connected'}
        
        # إنشاء نسخة احتياطية
        backup_name = f"scheduled_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        result = aws_manager.backup_database(backup_name)
        
        if result['success']:
            # تنظيف النسخ القديمة (الاحتفاظ بآخر 10 نسخ)
            backups = aws_manager.list_backups()
            if len(backups) > 10:
                old_backups = backups[10:]  # النسخ الأقدم
                for backup in old_backups:
                    try:
                        aws_manager.s3_client.delete_object(
                            Bucket=aws_manager.bucket_name,
                            Key=backup['key']
                        )
                        logging.info(f"Deleted old backup: {backup['name']}")
                    except Exception as e:
                        logging.error(f"Failed to delete old backup {backup['name']}: {e}")
            
            logging.info(f"Backup completed successfully: {backup_name}")
        else:
            logging.error(f"Backup failed: {result['message']}")
            raise Exception(result['message'])
        
        return result
        
    except Exception as e:
        logging.error(f"Backup task failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)  # إعادة المحاولة كل 5 دقائق

@celery.task(bind=True)
def send_metrics_to_cloud(self):
    """مهمة إرسال المقاييس للسحابة"""
    try:
        from cloud_integration import aws_manager
        
        if not aws_manager.is_connected():
            return {'status': 'skipped', 'reason': 'AWS not connected'}
        
        # جمع المقاييس
        metrics = performance_monitor.get_current_metrics()
        
        # إرسال إلى CloudWatch
        success = aws_manager.send_system_metrics(metrics)
        
        result = {
            'task': 'send_metrics_to_cloud',
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_sent': len(metrics) if success else 0
        }
        
        logging.info(f"Metrics sent to cloud: {success}")
        return result
        
    except Exception as e:
        logging.error(f"Send metrics task failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)

@celery.task(bind=True)
def send_critical_alert(self, alert_type, message, severity='CRITICAL'):
    """مهمة إرسال تنبيه حرج"""
    try:
        from cloud_integration import aws_manager
        
        if aws_manager.is_connected():
            success = aws_manager.send_alert_notification(alert_type, message, severity)
            if success:
                logging.info(f"Critical alert sent: {alert_type}")
            else:
                logging.error(f"Failed to send critical alert: {alert_type}")
        
        # حفظ التنبيه في Redis أيضاً
        if redis_manager.is_connected():
            alert_data = {
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            }
            redis_manager.add_to_list('system:critical_alerts', alert_data, max_length=50)
        
        return {'alert_sent': True, 'type': alert_type}
        
    except Exception as e:
        logging.error(f"Critical alert task failed: {e}")
        return {'alert_sent': False, 'error': str(e)}

@celery.task(bind=True)
def process_vnc_session_analytics(self):
    """معالجة تحليلات جلسات VNC"""
    try:
        from app import app, db
        from models import VNCSession, ConnectionLog
        
        with app.app_context():
            # تحليل استخدام الجلسات
            total_sessions = VNCSession.query.count()
            active_sessions = VNCSession.query.filter_by(is_active=True).count()
            
            # تحليل السجلات (آخر 24 ساعة)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_connections = ConnectionLog.query.filter(
                ConnectionLog.timestamp >= last_24h
            ).count()
            
            successful_connections = ConnectionLog.query.filter(
                ConnectionLog.timestamp >= last_24h,
                ConnectionLog.success == True
            ).count()
            
            # حساب المقاييس
            success_rate = (successful_connections / max(recent_connections, 1)) * 100
            
            analytics_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'connections_24h': recent_connections,
                'success_rate': round(success_rate, 2),
                'error_rate': round(100 - success_rate, 2)
            }
            
            # حفظ التحليلات في Redis
            if redis_manager.is_connected():
                redis_manager.set_cache('analytics:session_summary', analytics_data, ttl=3600)
                redis_manager.add_to_list('analytics:daily_stats', analytics_data, max_length=30)
            
            logging.info(f"Session analytics processed: {analytics_data}")
            return analytics_data
            
    except Exception as e:
        logging.error(f"Analytics processing failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

# تشغيل العامل
if __name__ == '__main__':
    celery.start()