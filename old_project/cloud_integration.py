"""
Cloud Services Integration for VNC Desktop
تكامل الخدمات السحابية لسطح مكتب VNC
"""
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import tempfile
import zipfile
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app

class AWSManager:
    """مدير خدمات Amazon Web Services"""
    
    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'vnc-desktop-backups')
        
        self.s3_client = None
        self.cloudwatch_client = None
        self.sns_client = None
        self.connected = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """تهيئة عملاء AWS"""
        try:
            if self.aws_access_key and self.aws_secret_key:
                session = boto3.Session(
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )
                
                self.s3_client = session.client('s3')
                self.cloudwatch_client = session.client('cloudwatch')
                self.sns_client = session.client('sns')
                
                # فحص الاتصال
                self.s3_client.head_bucket(Bucket='us-east-1')  # Test call
                self.connected = True
                logging.info("AWS services initialized successfully")
                
        except (NoCredentialsError, ClientError) as e:
            logging.warning(f"AWS initialization failed: {e}")
            self.connected = False
        except Exception as e:
            logging.error(f"Unexpected AWS error: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """فحص الاتصال بـ AWS"""
        return self.connected and self.s3_client is not None
    
    def backup_database(self, backup_name: str = None) -> Dict[str, Any]:
        """نسخ احتياطي لقاعدة البيانات على S3"""
        if not self.is_connected():
            return {'success': False, 'message': 'AWS not connected'}
        
        try:
            from app import db
            from models import VNCSession, ConnectionLog
            
            # إنشاء اسم النسخة الاحتياطية
            if not backup_name:
                backup_name = f"vnc_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # تصدير البيانات
            data = {
                'metadata': {
                    'backup_name': backup_name,
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'sessions': [],
                'logs': []
            }
            
            # نسخ الجلسات
            sessions = VNCSession.query.all()
            for session in sessions:
                data['sessions'].append({
                    'id': session.id,
                    'session_name': session.session_name,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'last_accessed': session.last_accessed.isoformat() if session.last_accessed else None,
                    'is_active': session.is_active,
                    'vnc_port': session.vnc_port,
                    'screen_resolution': session.screen_resolution
                })
            
            # نسخ السجلات (آخر 1000)
            logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(1000).all()
            for log in logs:
                data['logs'].append({
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'success': log.success,
                    'message': log.message,
                    'client_ip': log.client_ip
                })
            
            # رفع إلى S3
            backup_key = f"database_backups/{backup_name}.json"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=backup_key,
                Body=json.dumps(data, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={
                    'backup-type': 'database',
                    'created-by': 'vnc-desktop-server'
                }
            )
            
            return {
                'success': True,
                'message': f'Backup created successfully: {backup_name}',
                'backup_key': backup_key,
                'size': len(json.dumps(data)),
                'sessions_count': len(data['sessions']),
                'logs_count': len(data['logs'])
            }
            
        except Exception as e:
            logging.error(f"Database backup failed: {e}")
            return {'success': False, 'message': str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """قائمة النسخ الاحتياطية المتاحة"""
        if not self.is_connected():
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='database_backups/'
            )
            
            backups = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'name': obj['Key'].split('/')[-1].replace('.json', ''),
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })
            
            # ترتيب حسب التاريخ (الأحدث أولاً)
            backups.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return backups
            
        except Exception as e:
            logging.error(f"Failed to list backups: {e}")
            return []
    
    def restore_backup(self, backup_key: str) -> Dict[str, Any]:
        """استعادة نسخة احتياطية"""
        if not self.is_connected():
            return {'success': False, 'message': 'AWS not connected'}
        
        try:
            from app import db
            from models import VNCSession, ConnectionLog
            
            # تحميل النسخة الاحتياطية من S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=backup_key)
            backup_data = json.loads(response['Body'].read())
            
            restored_sessions = 0
            restored_logs = 0
            
            # استعادة الجلسات
            for session_data in backup_data.get('sessions', []):
                # فحص وجود الجلسة
                existing_session = VNCSession.query.filter_by(id=session_data['id']).first()
                if not existing_session:
                    session = VNCSession()
                    session.id = session_data['id']
                    session.session_name = session_data['session_name']
                    session.created_at = datetime.fromisoformat(session_data['created_at']) if session_data['created_at'] else None
                    session.last_accessed = datetime.fromisoformat(session_data['last_accessed']) if session_data['last_accessed'] else None
                    session.is_active = session_data['is_active']
                    session.vnc_port = session_data['vnc_port']
                    session.screen_resolution = session_data['screen_resolution']
                    
                    db.session.add(session)
                    restored_sessions += 1
            
            # استعادة السجلات
            for log_data in backup_data.get('logs', []):
                # فحص وجود السجل
                existing_log = ConnectionLog.query.filter_by(id=log_data['id']).first()
                if not existing_log:
                    log = ConnectionLog()
                    log.id = log_data['id']
                    log.timestamp = datetime.fromisoformat(log_data['timestamp'])
                    log.action = log_data['action']
                    log.success = log_data['success']
                    log.message = log_data['message']
                    log.client_ip = log_data['client_ip']
                    
                    db.session.add(log)
                    restored_logs += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Backup restored successfully',
                'restored_sessions': restored_sessions,
                'restored_logs': restored_logs,
                'backup_metadata': backup_data.get('metadata', {})
            }
            
        except Exception as e:
            logging.error(f"Backup restore failed: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return {'success': False, 'message': str(e)}
    
    def send_system_metrics(self, metrics: Dict[str, Any]) -> bool:
        """إرسال مقاييس النظام إلى CloudWatch"""
        if not self.is_connected():
            return False
        
        try:
            metric_data = []
            
            # مقاييس الأداء
            if 'cpu' in metrics:
                metric_data.append({
                    'MetricName': 'CPUUtilization',
                    'Value': metrics['cpu'].get('current', 0),
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                })
            
            if 'memory' in metrics:
                metric_data.append({
                    'MetricName': 'MemoryUtilization',
                    'Value': metrics['memory'].get('percent', 0),
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                })
            
            if 'application' in metrics:
                app_metrics = metrics['application']
                
                # عدد الطلبات
                if 'total_requests' in app_metrics:
                    metric_data.append({
                        'MetricName': 'TotalRequests',
                        'Value': app_metrics['total_requests'],
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    })
                
                # معدل الأخطاء
                if 'error_rate' in app_metrics:
                    metric_data.append({
                        'MetricName': 'ErrorRate',
                        'Value': app_metrics['error_rate'],
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    })
                
                # متوسط وقت الاستجابة
                if 'avg_response_time' in app_metrics:
                    metric_data.append({
                        'MetricName': 'AverageResponseTime',
                        'Value': app_metrics['avg_response_time'],
                        'Unit': 'Milliseconds',
                        'Timestamp': datetime.utcnow()
                    })
            
            # إرسال المقاييس
            if metric_data:
                self.cloudwatch_client.put_metric_data(
                    Namespace='VNC-Desktop/Application',
                    MetricData=metric_data
                )
                
                logging.info(f"Sent {len(metric_data)} metrics to CloudWatch")
                return True
            
        except Exception as e:
            logging.error(f"Failed to send metrics to CloudWatch: {e}")
        
        return False
    
    def send_alert_notification(self, alert_type: str, message: str, severity: str = 'INFO') -> bool:
        """إرسال تنبيه عبر SNS"""
        if not self.is_connected():
            return False
        
        topic_arn = os.getenv('AWS_SNS_TOPIC_ARN')
        if not topic_arn:
            return False
        
        try:
            # تحضير الرسالة
            alert_message = {
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'VNC Desktop Server'
            }
            
            # إرسال عبر SNS
            response = self.sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(alert_message, ensure_ascii=False, indent=2),
                Subject=f'VNC Alert: {alert_type} ({severity})',
                MessageAttributes={
                    'severity': {
                        'DataType': 'String',
                        'StringValue': severity
                    },
                    'alert_type': {
                        'DataType': 'String',
                        'StringValue': alert_type
                    }
                }
            )
            
            logging.info(f"Alert sent via SNS: {alert_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send SNS notification: {e}")
            return False
    
    def get_cloud_stats(self) -> Dict[str, Any]:
        """إحصائيات الخدمات السحابية"""
        if not self.is_connected():
            return {'connected': False}
        
        try:
            stats = {
                'connected': True,
                'region': self.aws_region,
                'bucket_name': self.bucket_name,
                'services': {
                    's3': True,
                    'cloudwatch': True,
                    'sns': bool(os.getenv('AWS_SNS_TOPIC_ARN'))
                }
            }
            
            # إحصائيات S3
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix='database_backups/'
                )
                stats['backups_count'] = response.get('KeyCount', 0)
                
                if 'Contents' in response:
                    total_size = sum(obj['Size'] for obj in response['Contents'])
                    stats['total_backup_size'] = total_size
            except:
                stats['backups_count'] = 0
                stats['total_backup_size'] = 0
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get cloud stats: {e}")
            return {'connected': False, 'error': str(e)}

class LoadBalancerManager:
    """مدير توزيع الأحمال والتوسع"""
    
    def __init__(self):
        self.servers = []
        self.current_server = 0
        self.health_checks = {}
        
    def add_server(self, host: str, port: int, weight: int = 1):
        """إضافة خادم جديد"""
        server = {
            'host': host,
            'port': port,
            'weight': weight,
            'active': True,
            'connections': 0,
            'last_check': datetime.now()
        }
        self.servers.append(server)
        logging.info(f"Added server {host}:{port} to load balancer")
    
    def get_next_server(self) -> Optional[Dict[str, Any]]:
        """الحصول على الخادم التالي (Round Robin)"""
        if not self.servers:
            return None
        
        # فلترة الخوادم النشطة
        active_servers = [s for s in self.servers if s['active']]
        if not active_servers:
            return None
        
        # اختيار الخادم حسب أقل عدد اتصالات
        server = min(active_servers, key=lambda s: s['connections'])
        server['connections'] += 1
        
        return server
    
    def health_check(self):
        """فحص صحة الخوادم"""
        for server in self.servers:
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    result = sock.connect_ex((server['host'], server['port']))
                    server['active'] = result == 0
                    server['last_check'] = datetime.now()
                    
            except Exception as e:
                server['active'] = False
                logging.error(f"Health check failed for {server['host']}:{server['port']}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات توزيع الأحمال"""
        active_count = len([s for s in self.servers if s['active']])
        total_connections = sum(s['connections'] for s in self.servers)
        
        return {
            'total_servers': len(self.servers),
            'active_servers': active_count,
            'total_connections': total_connections,
            'servers': self.servers.copy()
        }

# مثيلات عامة
aws_manager = AWSManager()
load_balancer = LoadBalancerManager()

def init_cloud_services(app=None):
    """تهيئة الخدمات السحابية"""
    if app:
        app.aws_manager = aws_manager
        app.load_balancer = load_balancer
    
    # إعداد Load Balancer الأساسي
    load_balancer.add_server('127.0.0.1', 5000, weight=1)
    
    logging.info("Cloud services initialized")
    return aws_manager.is_connected()

def schedule_cloud_backup():
    """جدولة النسخ الاحتياطية السحابية"""
    if aws_manager.is_connected():
        backup_result = aws_manager.backup_database()
        if backup_result['success']:
            logging.info(f"Scheduled backup completed: {backup_result['backup_key']}")
        else:
            logging.error(f"Scheduled backup failed: {backup_result['message']}")
    else:
        logging.warning("AWS not connected, skipping scheduled backup")

def monitor_and_alert():
    """مراقبة النظام وإرسال التنبيهات"""
    try:
        from performance import performance_monitor
        metrics = performance_monitor.get_current_metrics()
        alerts = performance_monitor.get_performance_alerts()
        
        # إرسال المقاييس للسحابة
        aws_manager.send_system_metrics(metrics)
        
        # إرسال التنبيهات الحرجة
        for alert in alerts:
            if alert.get('severity') in ['high', 'critical']:
                aws_manager.send_alert_notification(
                    alert_type=alert.get('type', 'system_alert'),
                    message=alert.get('message', ''),
                    severity=alert.get('severity', 'INFO').upper()
                )
        
    except Exception as e:
        logging.error(f"Monitoring and alerting failed: {e}")