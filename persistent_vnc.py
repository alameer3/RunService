#!/usr/bin/env python3
"""
Persistent VNC Server - يبقى نشط دائماً 
خادم VNC مستمر - لا يُغلق مع إعادة التشغيل
"""
import os
import sys
import time
import subprocess
import signal
import socket
from pathlib import Path
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PersistentVNCServer:
    def __init__(self):
        self.vnc_process = None
        self.xvfb_process = None
        self.window_manager_process = None
        self.running = False
        self.display = ":1"
        self.port = 5900
        
    def setup_environment(self):
        """إعداد البيئة"""
        os.environ['DISPLAY'] = self.display
        
        # إنشاء مجلد VNC
        vnc_dir = Path.home() / ".vnc"
        vnc_dir.mkdir(exist_ok=True)
        
        # إعداد كلمة المرور
        passwd_file = vnc_dir / "passwd"
        try:
            # استخدام x11vnc لإنشاء ملف كلمة المرور
            subprocess.run([
                'x11vnc', '-storepasswd', 'vnc123456', str(passwd_file)
            ], check=True, capture_output=True)
            os.chmod(passwd_file, 0o600)
            logging.info("VNC password configured")
            return True
        except Exception as e:
            logging.error(f"Password setup failed: {e}")
            return False
    
    def start_xvfb(self):
        """تشغيل Xvfb"""
        try:
            # قتل أي عملية Xvfb موجودة
            subprocess.run(['pkill', '-f', f'Xvfb {self.display}'], capture_output=True)
            time.sleep(1)
            
            cmd = [
                "Xvfb", self.display,
                "-screen", "0", "1024x768x24",
                "-ac", "+extension", "GLX", "+render", "-noreset"
            ]
            
            self.xvfb_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            time.sleep(3)
            
            # فحص أن Xvfb يعمل
            if self.xvfb_process.poll() is None:
                logging.info(f"Xvfb started on {self.display}")
                return True
            else:
                logging.error("Xvfb failed to start")
                return False
                
        except Exception as e:
            logging.error(f"Xvfb error: {e}")
            return False
    
    def start_window_manager(self):
        """تشغيل مدير النوافذ"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            self.window_manager_process = subprocess.Popen(
                ['openbox'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            logging.info("Window manager started")
            return True
            
        except Exception as e:
            logging.error(f"Window manager error: {e}")
            return False
    
    def start_vnc_server(self):
        """تشغيل خادم VNC مستمر"""
        try:
            # قتل أي عملية VNC موجودة
            subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
            time.sleep(1)
            
            passwd_file = Path.home() / ".vnc" / "passwd"
            
            cmd = [
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.port),
                '-rfbauth', str(passwd_file),
                '-forever',  # لا تُغلق بعد قطع الاتصال
                '-shared',   # السماح لعدة عملاء
                '-bg',       # تشغيل في الخلفية
                '-o', '/tmp/x11vnc.log',  # ملف السجل
                '-noxdamage',
                '-noxfixes',
                '-noxrandr',
                '-wait', '50',
                '-nap'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                time.sleep(2)
                
                # التحقق من أن المنفذ مفتوح
                if self.check_vnc_port():
                    logging.info(f"VNC server started on port {self.port}")
                    return True
                else:
                    logging.error("VNC server started but port not accessible")
                    return False
            else:
                logging.error(f"VNC server failed: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"VNC server error: {e}")
            return False
    
    def check_vnc_port(self):
        """فحص أن منفذ VNC مفتوح"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', self.port))
                return result == 0
        except:
            return False
    
    def start_applications(self):
        """تشغيل التطبيقات داخل VNC"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            # تشغيل Firefox
            subprocess.Popen([
                'firefox', '--new-instance', '--no-remote'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logging.info("Applications started")
            return True
            
        except Exception as e:
            logging.error(f"Applications error: {e}")
            return False
    
    def monitor_processes(self):
        """مراقبة العمليات وإعادة التشغيل عند الحاجة"""
        while self.running:
            try:
                # فحص Xvfb
                if self.xvfb_process and self.xvfb_process.poll() is not None:
                    logging.warning("Xvfb died, restarting...")
                    self.start_xvfb()
                
                # فحص VNC port
                if not self.check_vnc_port():
                    logging.warning("VNC port closed, restarting VNC server...")
                    self.start_vnc_server()
                
                time.sleep(10)  # فحص كل 10 ثواني
                
            except Exception as e:
                logging.error(f"Monitor error: {e}")
                time.sleep(30)
    
    def start(self):
        """بدء الخادم"""
        logging.info("Starting Persistent VNC Server...")
        
        if not self.setup_environment():
            logging.error("Environment setup failed")
            return False
        
        if not self.start_xvfb():
            logging.error("Xvfb startup failed")
            return False
        
        if not self.start_window_manager():
            logging.error("Window manager startup failed")
            return False
        
        if not self.start_vnc_server():
            logging.error("VNC server startup failed")
            return False
        
        self.start_applications()
        
        self.running = True
        
        # بدء مراقب العمليات في thread منفصل
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        logging.info("=" * 50)
        logging.info("🚀 Persistent VNC Server Started Successfully!")
        logging.info(f"🖥️  VNC URL: vnc://localhost:{self.port}")
        logging.info("🔑 Password: vnc123456")
        logging.info("📺 Resolution: 1024x768")
        logging.info("🔄 Auto-restart: Enabled")
        logging.info("=" * 50)
        
        return True
    
    def stop(self):
        """إيقاف الخادم"""
        self.running = False
        
        logging.info("Stopping VNC Server...")
        
        # إنهاء العمليات
        for process_name in ['x11vnc', f'Xvfb {self.display}', 'openbox']:
            try:
                subprocess.run(['pkill', '-f', process_name], capture_output=True)
            except:
                pass
        
        # إنهاء العمليات المحفوظة
        for process in [self.vnc_process, self.xvfb_process, self.window_manager_process]:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
        
        logging.info("VNC Server stopped")
    
    def status(self):
        """حالة الخادم"""
        vnc_running = self.check_vnc_port()
        xvfb_running = self.xvfb_process and self.xvfb_process.poll() is None
        
        print("=" * 40)
        print("🖥️  VNC Server Status")
        print("=" * 40)
        print(f"VNC Port {self.port}: {'✅ Open' if vnc_running else '❌ Closed'}")
        print(f"Xvfb Display {self.display}: {'✅ Running' if xvfb_running else '❌ Stopped'}")
        print(f"Monitor Thread: {'✅ Active' if self.running else '❌ Inactive'}")
        
        if vnc_running:
            print(f"\n🔗 Connection Info:")
            print(f"   URL: vnc://localhost:{self.port}")
            print(f"   Password: vnc123456")
            print(f"   Resolution: 1024x768")
        
        print("=" * 40)
        return vnc_running

def signal_handler(signum, frame):
    """معالج إشارات النظام"""
    global vnc_server
    logging.info("Received shutdown signal")
    vnc_server.stop()
    sys.exit(0)

if __name__ == "__main__":
    # إعداد معالجات الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    vnc_server = PersistentVNCServer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "stop":
            vnc_server.stop()
            sys.exit(0)
        elif sys.argv[1] == "status":
            vnc_server.status()
            sys.exit(0)
        elif sys.argv[1] == "restart":
            vnc_server.stop()
            time.sleep(2)
    
    try:
        if vnc_server.start():
            # الحفاظ على البرنامج نشط
            while vnc_server.running:
                time.sleep(60)
                if vnc_server.running:
                    logging.info("VNC Server still running...")
        else:
            logging.error("Failed to start VNC Server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
        vnc_server.stop()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        vnc_server.stop()
        sys.exit(1)