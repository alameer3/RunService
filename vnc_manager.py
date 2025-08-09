#!/usr/bin/env python3
"""
VNC Manager - إدارة خادم VNC المستمر
إدارة متقدمة لخادم VNC مع مراقبة وإعادة التشغيل التلقائي
"""
import os
import sys
import json
import time
import subprocess
import socket
from pathlib import Path
from datetime import datetime

class VNCManager:
    def __init__(self):
        self.config_file = Path.home() / ".vnc_manager.json"
        self.log_file = Path("/tmp/vnc_manager.log")
        self.pid_file = Path("/tmp/vnc_server.pid")
        
        # الإعدادات الافتراضية
        self.default_config = {
            "display": ":1",
            "port": 5900,
            "password": "vnc123456",
            "resolution": "1024x768x24",
            "auto_restart": True,
            "max_restarts": 5,
            "restart_delay": 10
        }
        
        self.load_config()
    
    def load_config(self):
        """تحميل الإعدادات"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**self.default_config, **json.load(f)}
            except:
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """حفظ الإعدادات"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log(f"Failed to save config: {e}")
    
    def log(self, message):
        """تسجيل الرسائل"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + "\n")
        except:
            pass
    
    def check_port(self, port):
        """فحص أن المنفذ مفتوح"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def kill_existing_processes(self):
        """قتل العمليات الموجودة"""
        processes_to_kill = [
            f'Xvfb {self.config["display"]}',
            'x11vnc',
            'openbox'
        ]
        
        for process in processes_to_kill:
            try:
                subprocess.run(['pkill', '-f', process], 
                             capture_output=True, timeout=10)
                time.sleep(1)
            except:
                pass
    
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        vnc_dir = Path.home() / ".vnc"
        vnc_dir.mkdir(exist_ok=True)
        
        passwd_file = vnc_dir / "passwd"
        
        try:
            # استخدام x11vnc لإنشاء ملف كلمة المرور
            result = subprocess.run([
                'x11vnc', '-storepasswd', self.config["password"], str(passwd_file)
            ], capture_output=True, timeout=10)
            
            if result.returncode == 0:
                os.chmod(passwd_file, 0o600)
                self.log("VNC password configured successfully")
                return True
            else:
                self.log(f"Password setup failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            self.log(f"Password setup error: {e}")
            return False
    
    def start_xvfb(self):
        """تشغيل Xvfb"""
        try:
            cmd = [
                "Xvfb", self.config["display"],
                "-screen", "0", self.config["resolution"],
                "-ac", "+extension", "GLX", "+render", "-noreset"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # انتظار قصير للتأكد من بدء التشغيل
            time.sleep(3)
            
            if process.poll() is None:
                self.log(f"Xvfb started successfully on {self.config['display']}")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"Xvfb failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.log(f"Xvfb error: {e}")
            return False
    
    def start_window_manager(self):
        """تشغيل مدير النوافذ"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.config["display"]
            
            subprocess.Popen(
                ['openbox'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(2)
            self.log("Window manager (openbox) started")
            return True
            
        except Exception as e:
            self.log(f"Window manager error: {e}")
            return False
    
    def start_vnc_server(self):
        """تشغيل خادم VNC"""
        try:
            passwd_file = Path.home() / ".vnc" / "passwd"
            
            if not passwd_file.exists():
                if not self.setup_vnc_password():
                    return False
            
            cmd = [
                'x11vnc',
                '-display', self.config["display"],
                '-rfbport', str(self.config["port"]),
                '-rfbauth', str(passwd_file),
                '-forever',  # لا تُغلق بعد انقطاع الاتصال
                '-shared',   # السماح لعدة عملاء
                '-bg',       # تشغيل في الخلفية
                '-o', str(self.log_file),  # ملف السجل
                '-noxdamage',  # تحسينات الأداء
                '-noxfixes',
                '-noxrandr',
                '-wait', '50',
                '-nap',
                '-desktop', 'VNC-Desktop'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                time.sleep(2)
                
                # التحقق من أن المنفذ مفتوح
                if self.check_port(self.config["port"]):
                    self.log(f"VNC server started successfully on port {self.config['port']}")
                    return True
                else:
                    self.log("VNC server started but port not accessible")
                    return False
            else:
                self.log(f"VNC server failed to start: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("VNC server startup timed out")
            return False
        except Exception as e:
            self.log(f"VNC server error: {e}")
            return False
    
    def start_applications(self):
        """تشغيل التطبيقات داخل VNC"""
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.config["display"]
            
            # تشغيل Firefox
            subprocess.Popen([
                'firefox', '--new-instance', '--no-remote', '--display=' + self.config["display"]
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            self.log("Applications started in VNC session")
            return True
            
        except Exception as e:
            self.log(f"Applications startup error: {e}")
            return False
    
    def start(self):
        """بدء VNC Server كاملاً"""
        self.log("Starting VNC Server...")
        
        # قتل العمليات الموجودة
        self.kill_existing_processes()
        time.sleep(2)
        
        # إعداد كلمة المرور
        if not self.setup_vnc_password():
            self.log("Failed to setup VNC password")
            return False
        
        # تشغيل Xvfb
        if not self.start_xvfb():
            self.log("Failed to start Xvfb")
            return False
        
        # تشغيل مدير النوافذ
        if not self.start_window_manager():
            self.log("Failed to start window manager")
            return False
        
        # تشغيل VNC Server
        if not self.start_vnc_server():
            self.log("Failed to start VNC server")
            return False
        
        # تشغيل التطبيقات
        self.start_applications()
        
        # حفظ معرف العملية
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except:
            pass
        
        self.log("=" * 50)
        self.log("🚀 VNC Server Started Successfully!")
        self.log(f"🖥️  VNC URL: vnc://localhost:{self.config['port']}")
        self.log(f"🔑 Password: {self.config['password']}")
        self.log(f"📺 Resolution: {self.config['resolution'].replace('x24', '')}")
        self.log("=" * 50)
        
        return True
    
    def stop(self):
        """إيقاف VNC Server"""
        self.log("Stopping VNC Server...")
        
        self.kill_existing_processes()
        
        # حذف ملف PID
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except:
            pass
        
        self.log("VNC Server stopped")
        return True
    
    def status(self):
        """عرض حالة VNC Server"""
        vnc_running = self.check_port(self.config["port"])
        
        # فحص العمليات
        processes = {}
        for proc_name in ['Xvfb', 'x11vnc', 'openbox']:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', proc_name], 
                    capture_output=True, text=True
                )
                processes[proc_name] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            except:
                processes[proc_name] = 0
        
        print("=" * 50)
        print("🖥️  VNC Server Status")
        print("=" * 50)
        print(f"VNC Port {self.config['port']}: {'✅ Open' if vnc_running else '❌ Closed'}")
        print(f"Xvfb Display {self.config['display']}: {'✅ Running' if processes['Xvfb'] > 0 else '❌ Stopped'}")
        print(f"VNC Server: {'✅ Running' if processes['x11vnc'] > 0 else '❌ Stopped'}")
        print(f"Window Manager: {'✅ Running' if processes['openbox'] > 0 else '❌ Stopped'}")
        
        if vnc_running:
            print(f"\n🔗 Connection Info:")
            print(f"   URL: vnc://localhost:{self.config['port']}")
            print(f"   Password: {self.config['password']}")
            print(f"   Resolution: {self.config['resolution'].replace('x24', '')}")
        else:
            print(f"\n❗ To start VNC server, run: python3 {sys.argv[0]} start")
        
        print("=" * 50)
        
        # عرض السجلات الأخيرة
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print("\n📋 Recent logs (last 5):")
                        for line in lines[-5:]:
                            print(f"   {line.strip()}")
            except:
                pass
        
        return vnc_running
    
    def restart(self):
        """إعادة تشغيل VNC Server"""
        self.log("Restarting VNC Server...")
        self.stop()
        time.sleep(3)
        return self.start()

def main():
    """الدالة الرئيسية"""
    manager = VNCManager()
    
    if len(sys.argv) < 2:
        print("Usage: python3 vnc_manager.py [start|stop|restart|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = manager.start()
        sys.exit(0 if success else 1)
    elif command == "stop":
        success = manager.stop()
        sys.exit(0 if success else 1)
    elif command == "restart":
        success = manager.restart()
        sys.exit(0 if success else 1)
    elif command == "status":
        manager.status()
        sys.exit(0)
    else:
        print("Unknown command. Use: start|stop|restart|status")
        sys.exit(1)

if __name__ == "__main__":
    main()