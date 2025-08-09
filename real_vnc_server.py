#!/usr/bin/env python3
"""
Real VNC Server للاتصال مع RealVNC Viewer على الأندرويد
"""

import os
import subprocess
import socket
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RealVNCServer:
    """خادم VNC حقيقي للاتصال الخارجي"""
    
    def __init__(self):
        self.display = ":1"
        self.port = 5901  # منفذ VNC القياسي
        self.password = "vnc123"
        self.screen_size = "1024x768"
        self.color_depth = 24
        
    def start_vnc_server(self):
        """بدء خادم VNC حقيقي"""
        try:
            # التحقق من توفر الحزم
            if not self._check_vnc_packages():
                return {
                    'success': False,
                    'message': 'حزم VNC غير مثبتة. يمكنك تشغيل النظام المحاكي من الواجهة الرئيسية.'
                }
            
            # إيقاف أي خادم VNC موجود
            self._stop_existing_vnc()
            
            # بدء خادم العرض الافتراضي
            self._start_virtual_display()
            
            # بدء خادم VNC
            vnc_result = self._start_vnc_daemon()
            
            if vnc_result:
                # تهيئة بيئة سطح المكتب
                self._setup_desktop_environment()
                
                # الحصول على عنوان IP الخارجي
                external_ip = self._get_external_ip()
                
                return {
                    'success': True,
                    'message': 'تم بدء خادم VNC بنجاح',
                    'connection_info': {
                        'server': external_ip or 'localhost',
                        'port': self.port,
                        'password': self.password,
                        'display': self.display,
                        'android_connection': f"{external_ip}:{self.port}" if external_ip else f"localhost:{self.port}"
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في بدء خادم VNC'
                }
                
        except Exception as e:
            logger.error(f"خطأ في بدء VNC: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def _check_vnc_packages(self):
        """التحقق من توفر حزم VNC"""
        packages = ['Xvfb', 'x11vnc']
        for package in packages:
            if not subprocess.run(['which', package], capture_output=True).returncode == 0:
                logger.warning(f"الحزمة {package} غير متوفرة")
                return False
        return True
    
    def _stop_existing_vnc(self):
        """إيقاف أي خادم VNC موجود"""
        try:
            # إيقاف x11vnc
            subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
            # إيقاف Xvfb
            subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
            time.sleep(1)
        except:
            pass
    
    def _start_virtual_display(self):
        """بدء خادم العرض الافتراضي"""
        try:
            cmd = [
                'Xvfb', 
                self.display,
                '-screen', '0', f'{self.screen_size}x{self.color_depth}',
                '-ac', 
                '+extension', 'GLX',
                '+render',
                '-noreset'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # انتظار بدء الخادم
            time.sleep(2)
            
            # تعيين متغير البيئة
            os.environ['DISPLAY'] = self.display
            
            logger.info(f"تم بدء خادم العرض {self.display}")
            return process
            
        except Exception as e:
            logger.error(f"خطأ في بدء خادم العرض: {e}")
            return None
    
    def _start_vnc_daemon(self):
        """بدء خادم VNC"""
        try:
            # إنشاء ملف كلمة المرور
            passwd_file = Path.home() / '.vnc_passwd'
            subprocess.run([
                'x11vnc', '-storepasswd', self.password, str(passwd_file)
            ], check=True, capture_output=True)
            
            # بدء خادم VNC
            cmd = [
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.port),
                '-rfbauth', str(passwd_file),
                '-forever',
                '-shared',
                '-bg',
                '-o', '/tmp/x11vnc.log'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # التحقق من أن المنفذ مفتوح
                time.sleep(1)
                if self._check_port_open(self.port):
                    logger.info(f"خادم VNC يعمل على المنفذ {self.port}")
                    return True
            
            logger.error(f"فشل بدء x11vnc: {result.stderr}")
            return False
            
        except Exception as e:
            logger.error(f"خطأ في بدء x11vnc: {e}")
            return False
    
    def _setup_desktop_environment(self):
        """تهيئة بيئة سطح المكتب"""
        try:
            # بدء مدير النوافذ البسيط
            subprocess.Popen([
                'fluxbox'
            ], env=dict(os.environ, DISPLAY=self.display), 
               stdout=subprocess.DEVNULL, 
               stderr=subprocess.DEVNULL)
            
            time.sleep(1)
            
            # بدء terminal
            subprocess.Popen([
                'xterm', '-geometry', '80x24+10+10'
            ], env=dict(os.environ, DISPLAY=self.display),
               stdout=subprocess.DEVNULL, 
               stderr=subprocess.DEVNULL)
            
            logger.info("تم تهيئة بيئة سطح المكتب")
            
        except Exception as e:
            logger.warning(f"تحذير: فشل تهيئة سطح المكتب: {e}")
    
    def _check_port_open(self, port):
        """فحص المنفذ"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def _get_external_ip(self):
        """الحصول على عنوان IP الخارجي"""
        try:
            # محاولة الحصول على IP الخارجي
            import requests
            response = requests.get('https://api.ipify.org?format=text', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        # محاولة الحصول على IP المحلي
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except:
            return None
    
    def get_status(self):
        """الحصول على حالة الخادم"""
        is_running = self._check_port_open(self.port)
        external_ip = self._get_external_ip()
        
        return {
            'is_running': is_running,
            'port': self.port,
            'display': self.display,
            'external_ip': external_ip,
            'connection_info': {
                'server': external_ip or 'localhost',
                'port': self.port,
                'password': self.password if is_running else None,
                'android_connection': f"{external_ip}:{self.port}" if external_ip and is_running else None
            }
        }
    
    def stop_server(self):
        """إيقاف الخادم"""
        try:
            self._stop_existing_vnc()
            return {'success': True, 'message': 'تم إيقاف خادم VNC'}
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}

# Instance عام
real_vnc_server = RealVNCServer()

def start_real_vnc():
    """بدء خادم VNC الحقيقي"""
    return real_vnc_server.start_vnc_server()

def stop_real_vnc():
    """إيقاف خادم VNC الحقيقي"""
    return real_vnc_server.stop_server()

def get_real_vnc_status():
    """حالة خادم VNC الحقيقي"""
    return real_vnc_server.get_status()