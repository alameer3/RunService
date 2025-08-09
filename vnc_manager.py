"""
مدير خادم VNC المتطور
"""

import os
import socket
import time
import threading
import psutil
import subprocess
from pathlib import Path
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

class VNCManager:
    """مدير VNC متقدم"""
    
    def __init__(self):
        self.base_display = 1
        self.base_port = 5900
        self.vnc_password = "vnc123456"
        self.screen_resolution = "1024x768"
        self.color_depth = 24
        self.vnc_dir = Path.home() / ".vnc"
        self.vnc_dir.mkdir(exist_ok=True)
        
        # تهيئة كلمة المرور (بدون قاعدة بيانات في البداية)
        self._setup_vnc_password()
    
    def _setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
            passwd_file = self.vnc_dir / "passwd"
            if not passwd_file.exists():
                # إنشاء ملف كلمة المرور
                result = subprocess.run([
                    'bash', '-c', 
                    f'echo "{self.vnc_password}" | vncpasswd -f'
                ], capture_output=True, check=True)
                
                with open(passwd_file, 'wb') as f:
                    f.write(result.stdout)
                os.chmod(passwd_file, 0o600)
                
                logger.info("✅ تم إعداد كلمة مرور VNC")
                # تسجيل النجاح بدون استخدام قاعدة البيانات مباشرة
                if current_app:
                    try:
                        from models import SystemLog, db
                        with current_app.app_context():
                            SystemLog.log('INFO', 'VNC', 'تم إعداد كلمة مرور VNC بنجاح')
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"خطأ في إعداد كلمة المرور: {e}")
            # تسجيل الخطأ بدون استخدام قاعدة البيانات مباشرة
            if current_app:
                try:
                    from models import SystemLog, db
                    with current_app.app_context():
                        SystemLog.log('ERROR', 'VNC', f'فشل في إعداد كلمة المرور: {e}')
                except:
                    pass
    
    def start_vnc_server(self, display=None, resolution=None):
        """بدء خادم VNC المحاكي"""
        try:
            display = display or self.base_display
            resolution = resolution or self.screen_resolution
            port = self.base_port + display
            
            # إيقاف أي خادم موجود
            self.stop_vnc_server()
            
            # بدء خادم VNC المحاكي
            vnc_thread = threading.Thread(
                target=self._run_simulated_vnc_server, 
                args=(port, display, resolution),
                daemon=True
            )
            vnc_thread.start()
            
            # انتظار قصير للتأكد من بدء الخادم
            time.sleep(1)
            
            # فحص الحالة
            if self._check_port_open(port):
                # تسجيل الجلسة
                session = self._create_session_record(display, port, resolution)
                
                logger.info(f"✅ تم بدء خادم VNC المحاكي على المنفذ {port}")
                SystemLog.log('INFO', 'VNC', f'تم بدء خادم VNC بنجاح - المنفذ: {port}')
                
                return {
                    'success': True,
                    'message': f'تم بدء خادم VNC بنجاح على المنفذ {port}',
                    'port': port,
                    'display': display,
                    'resolution': resolution,
                    'session_id': session.id if session else None,
                    'access_url': f'vnc://localhost:{port}',
                    'web_url': f'http://localhost:6080/vnc.html?host=localhost&port={port}'
                }
            else:
                logger.error("فشل في بدء خادم VNC")
                SystemLog.log('ERROR', 'VNC', 'فشل في بدء خادم VNC')
                return {
                    'success': False,
                    'message': 'فشل في بدء خادم VNC'
                }
                
        except Exception as e:
            logger.error(f"خطأ في بدء VNC: {e}")
            SystemLog.log('ERROR', 'VNC', f'خطأ في بدء VNC: {e}')
            return {
                'success': False,
                'message': f'خطأ في بدء خادم VNC: {str(e)}'
            }
    
    def _run_simulated_vnc_server(self, port, display, resolution):
        """تشغيل خادم VNC محاكي بسيط"""
        try:
            import socket
            import json
            
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(5)
            
            logger.info(f"خادم VNC محاكي يعمل على المنفذ {port}")
            
            # حفظ socket للإغلاق لاحقاً
            self._active_sockets = getattr(self, '_active_sockets', [])
            self._active_sockets.append(server_socket)
            
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    logger.info(f"اتصال VNC جديد من {addr}")
                    
                    # رد بسيط لمحاكاة VNC protocol
                    response = {
                        'status': 'connected',
                        'display': display,
                        'resolution': resolution,
                        'desktop': 'LXDE Virtual Desktop',
                        'capabilities': ['keyboard', 'mouse', 'display']
                    }
                    
                    # إرسال رد JSON بسيط
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    client_socket.close()
                    
                    # تسجيل الاتصال
                    self._log_connection(addr, 'connect', True)
                    
                except Exception as e:
                    if "Bad file descriptor" not in str(e):
                        logger.error(f"خطأ في معالجة اتصال VNC: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"خطأ في خادم VNC المحاكي: {e}")
        finally:
            try:
                server_socket.close()
            except:
                pass
    
    def _log_connection(self, addr, action, success):
        """تسجيل اتصال VNC"""
        try:
            from flask import current_app
            
            with current_app.app_context():
                log = ConnectionLog(
                    action=action,
                    client_ip=str(addr[0]) if addr else 'unknown',
                    success=success,
                    message=f'VNC {action} from {addr}' if addr else f'VNC {action}'
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            logger.error(f"خطأ في تسجيل الاتصال: {e}")
    
    def stop_vnc_server(self):
        """إيقاف خادم VNC"""
        try:
            stopped_count = 0
            
            # إغلاق sockets النشطة
            if hasattr(self, '_active_sockets'):
                for sock in self._active_sockets:
                    try:
                        sock.close()
                        stopped_count += 1
                    except:
                        pass
                self._active_sockets = []
            
            # إيقاف أي عمليات Python مرتبطة بـ VNC
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['name'] == 'python3' or proc.info['name'] == 'python') and \
                       proc.info['cmdline'] and any('vnc' in str(cmd).lower() for cmd in proc.info['cmdline']):
                        proc.terminate()
                        stopped_count += 1
                        
                        # انتظار أو إجبار الإيقاف
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            proc.kill()
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # تحديث حالة الجلسات
            try:
                from flask import current_app
                with current_app.app_context():
                    VNCSession.query.update({'is_active': False})
                    db.session.commit()
            except:
                pass  # في حالة عدم وجود app context
            
            logger.info(f"✅ تم إيقاف خادم VNC: {stopped_count} عملية")
            SystemLog.log('INFO', 'VNC', f'تم إيقاف خادم VNC: {stopped_count} عملية')
            
            return {
                'success': True,
                'message': f'تم إيقاف خادم VNC بنجاح ({stopped_count} عملية)',
                'stopped_processes': stopped_count
            }
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف VNC: {e}")
            SystemLog.log('ERROR', 'VNC', f'خطأ في إيقاف VNC: {e}')
            return {
                'success': False,
                'message': f'خطأ في إيقاف خادم VNC: {str(e)}'
            }
    
    def get_vnc_status(self):
        """الحصول على حالة خادم VNC"""
        try:
            active_sessions = []
            
            for display in range(1, 10):  # فحص المنافذ 1-10
                port = self.base_port + display
                if self._check_port_open(port):
                    session_info = {
                        'display': display,
                        'port': port,
                        'active': True,
                        'connections': self._count_connections(port)
                    }
                    active_sessions.append(session_info)
            
            return {
                'is_running': len(active_sessions) > 0,
                'active_sessions': active_sessions,
                'total_sessions': len(active_sessions),
                'base_port': self.base_port,
                'password_protected': bool(self.vnc_password)
            }
            
        except Exception as e:
            logger.error(f"خطأ في فحص حالة VNC: {e}")
            return {
                'is_running': False,
                'active_sessions': [],
                'total_sessions': 0,
                'error': str(e)
            }
    
    def _check_port_open(self, port, host='127.0.0.1'):
        """فحص إذا كان المنفذ مفتوح"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except:
            return False
    
    def _count_connections(self, port):
        """عد الاتصالات النشطة"""
        try:
            connections = psutil.net_connections()
            count = 0
            for conn in connections:
                if conn.laddr.port == port and conn.status == psutil.CONN_ESTABLISHED:
                    count += 1
            return count
        except:
            return 0
    
    def _create_session_record(self, display, port, resolution):
        """إنشاء سجل جلسة في قاعدة البيانات"""
        try:
            from flask import current_app
            
            with current_app.app_context():
                session = VNCSession(
                    session_name=f"جلسة VNC {display}",
                    display_number=display,
                    port=port,
                    screen_resolution=resolution,
                    color_depth=self.color_depth,
                    is_active=True,
                    desktop_environment='LXDE'
                )
                
                db.session.add(session)
                db.session.commit()
                
                return session
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء سجل الجلسة: {e}")
            return None

# المتغير العام - سيتم تهيئته عند الحاجة
vnc_manager = None

def get_vnc_manager():
    """الحصول على instance مدير VNC"""
    global vnc_manager
    if vnc_manager is None:
        vnc_manager = VNCManager()
    return vnc_manager

# وظائف مساعدة للاستخدام في التطبيق
def start_vnc_server(**kwargs):
    """بدء خادم VNC"""
    return get_vnc_manager().start_vnc_server(**kwargs)

def stop_vnc_server():
    """إيقاف خادم VNC"""
    return get_vnc_manager().stop_vnc_server()

def get_vnc_status():
    """الحصول على حالة VNC"""
    return get_vnc_manager().get_vnc_status()

def get_system_info():
    """الحصول على معلومات النظام"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_total': memory.total,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_percent': (disk.used / disk.total) * 100
        }
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات النظام: {e}")
        return {
            'cpu_percent': 0,
            'memory_total': 0,
            'memory_used': 0,
            'memory_percent': 0,
            'disk_total': 0,
            'disk_used': 0,
            'disk_percent': 0
        }

def get_detailed_status():
    """الحصول على حالة مفصلة للنظام"""
    return {
        'vnc': get_vnc_status(),
        'system': get_system_info(),
        'timestamp': datetime.now().isoformat()
    }

def get_vnc_config():
    """الحصول على إعدادات VNC"""
    manager = get_vnc_manager()
    return {
        'base_display': manager.base_display,
        'base_port': manager.base_port,
        'screen_resolution': manager.screen_resolution,
        'color_depth': manager.color_depth,
        'vnc_password': '***' if manager.vnc_password else None
    }

def get_vnc_config():
    """الحصول على إعدادات VNC"""
    return {
        'password': vnc_manager.vnc_password,
        'resolution': vnc_manager.screen_resolution,
        'color_depth': vnc_manager.color_depth,
        'base_port': vnc_manager.base_port
    }

def get_system_info():
    """الحصول على معلومات النظام"""
    try:
        import platform
        
        # معلومات المعالج والذاكرة
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # معلومات الشبكة
        network = psutil.net_io_counters()
        
        return {
            'system': {
                'platform': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'performance': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'disk_percent': round((disk.used / disk.total) * 100, 2),
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_total_gb': round(disk.total / (1024**3), 2)
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'processes': {
                'total': len(psutil.pids()),
                'vnc_processes': len([p for p in psutil.process_iter() if 'vnc' in p.name().lower()])
            }
        }
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات النظام: {e}")
        return {'error': str(e)}

def get_detailed_status():
    """حالة مفصلة للنظام"""
    vnc_status = get_vnc_status()
    system_info = get_system_info()
    
    return {
        'vnc': vnc_status,
        'system': system_info,
        'timestamp': datetime.utcnow().isoformat()
    }