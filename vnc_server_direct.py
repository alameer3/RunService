#!/usr/bin/env python3
"""
VNC Server for Replit Networking
خادم VNC مُحسّن للعمل مع منافذ Replit
"""
import os
import sys
import time
import subprocess
import socket
import threading
from pathlib import Path
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعدادات VNC
VNC_PORT = 5901
VNC_DISPLAY = ":1"
VNC_PASSWORD = "vnc123456"
SCREEN_RESOLUTION = "1024x768"
VNC_DEPTH = "24"

class VNCServerReplit:
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
            vnc_dir = Path.home() / ".vnc"
            vnc_dir.mkdir(exist_ok=True)
            
            # إنشاء ملف كلمة المرور
            passwd_cmd = f'echo "{VNC_PASSWORD}" | vncpasswd -f'
            result = subprocess.run(passwd_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                passwd_file = vnc_dir / "passwd"
                with open(passwd_file, 'wb') as f:
                    f.write(result.stdout.encode())
                os.chmod(passwd_file, 0o600)
                logger.info(f"✓ VNC password configured: {VNC_PASSWORD}")
                return True
            else:
                logger.error(f"Failed to create VNC password: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up VNC password: {e}")
            return False

    def start_xvfb(self):
        """تشغيل Xvfb"""
        try:
            cmd = [
                "Xvfb", VNC_DISPLAY,
                "-screen", "0", f"{SCREEN_RESOLUTION}x{VNC_DEPTH}",
                "-ac", "-nolisten", "tcp", "-dpi", "96"
            ]
            
            logger.info("Starting Xvfb...")
            self.processes['xvfb'] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(2)  # انتظار للتأكد من بدء Xvfb
            
            if self.processes['xvfb'].poll() is None:
                logger.info(f"✓ Xvfb started on display {VNC_DISPLAY}")
                return True
            else:
                logger.error("Failed to start Xvfb")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Xvfb: {e}")
            return False

    def start_window_manager(self):
        """تشغيل مدير النوافذ"""
        try:
            env = os.environ.copy()
            env["DISPLAY"] = VNC_DISPLAY
            
            logger.info("Starting window manager...")
            self.processes['wm'] = subprocess.Popen(
                ["openbox", "--sm-disable"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(1)
            logger.info("✓ Window manager (Openbox) started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting window manager: {e}")
            return False

    def start_vnc_server(self):
        """تشغيل خادم VNC"""
        try:
            vnc_passwd_file = Path.home() / ".vnc" / "passwd"
            
            if not vnc_passwd_file.exists():
                logger.error("VNC password file not found")
                return False
            
            cmd = [
                "x11vnc",
                "-display", VNC_DISPLAY,
                "-rfbport", str(VNC_PORT),
                "-rfbauth", str(vnc_passwd_file),
                "-forever",
                "-shared",
                "-permitfiletransfer",
                "-tightfilexfer",
                "-noxdamage",
                "-noxfixes",
                "-noxinerama",
                "-noscroll",
                "-ncache", "10",
                "-ncache_cr",
                "-solid",
                "-bg"
            ]
            
            logger.info(f"Starting VNC server on port {VNC_PORT}...")
            self.processes['vnc'] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # انتظار وفحص المنفذ
            for _ in range(10):  # محاولة لمدة 10 ثوان
                time.sleep(1)
                if self.is_port_open(VNC_PORT):
                    logger.info(f"✓ VNC Server is running on port {VNC_PORT}")
                    return True
            
            logger.error("VNC server failed to start or bind to port")
            return False
            
        except Exception as e:
            logger.error(f"Error starting VNC server: {e}")
            return False

    def start_firefox(self):
        """تشغيل Firefox في الخلفية"""
        try:
            env = os.environ.copy()
            env["DISPLAY"] = VNC_DISPLAY
            env["HOME"] = str(Path.home())
            
            # إنشاء profile Firefox
            firefox_profile_dir = Path.home() / ".mozilla" / "firefox"
            firefox_profile_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Starting Firefox...")
            self.processes['firefox'] = subprocess.Popen(
                ["firefox", "--new-instance", "--no-remote"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info("✓ Firefox started")
            return True
            
        except Exception as e:
            logger.error(f"Warning: Failed to start Firefox: {e}")
            return True  # لا نُفشِل العملية بأكملها إذا لم يعمل Firefox

    def is_port_open(self, port):
        """فحص المنفذ"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False

    def get_connection_info(self):
        """عرض معلومات الاتصال"""
        # جلب معلومات Replit
        repl_url = os.getenv('REPLIT_URL', 'localhost')
        if repl_url.startswith('http://'):
            repl_url = repl_url.replace('http://', '')
        elif repl_url.startswith('https://'):
            repl_url = repl_url.replace('https://', '')
        
        print("\n" + "="*60)
        print("🖥️  VNC Server - Ready for Connections")
        print("="*60)
        print(f"🔗 Server Address: {repl_url}")
        print(f"🔌 VNC Port: {VNC_PORT}")
        print(f"🔑 Password: {VNC_PASSWORD}")
        print(f"📺 Screen: {SCREEN_RESOLUTION} @ {VNC_DEPTH}bit")
        print("="*60)
        print("📱 VNC Client Connection:")
        print(f"   Server: {repl_url}:{VNC_PORT}")
        print(f"   Password: {VNC_PASSWORD}")
        print("="*60)
        print("✨ The VNC server is now visible in Replit's Networking tab")
        print("✨ خادم VNC جاهز ومرئي في تبويب الشبكة في Replit")

    def start_all_services(self):
        """تشغيل جميع الخدمات"""
        logger.info("🚀 Starting VNC Server for Replit Networking...")
        
        # خطوات التشغيل
        steps = [
            ("Setting up VNC password", self.setup_vnc_password),
            ("Starting Xvfb", self.start_xvfb),
            ("Starting window manager", self.start_window_manager),
            ("Starting VNC server", self.start_vnc_server),
            ("Starting Firefox", self.start_firefox),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return False
        
        self.running = True
        self.get_connection_info()
        return True

    def cleanup(self):
        """تنظيف العمليات"""
        logger.info("Cleaning up processes...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"✓ Stopped {name}")
                except:
                    try:
                        process.kill()
                        logger.info(f"✓ Killed {name}")
                    except:
                        logger.warning(f"✗ Failed to stop {name}")

    def keep_alive(self):
        """إبقاء الخادم نشطاً"""
        logger.info("VNC Server is running. Press Ctrl+C to stop.")
        try:
            while self.running:
                time.sleep(5)
                # فحص العمليات
                for name, process in self.processes.items():
                    if process and process.poll() is not None:
                        logger.warning(f"Process {name} has stopped")
                        
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            self.cleanup()

def main():
    """الدالة الرئيسية"""
    vnc_server = VNCServerReplit()
    
    try:
        if vnc_server.start_all_services():
            vnc_server.keep_alive()
        else:
            logger.error("Failed to start VNC server")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        vnc_server.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()