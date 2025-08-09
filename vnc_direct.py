#!/usr/bin/env python3
"""
VNC Server Direct Launch - منفذ مباشر لتشغيل VNC
يقوم بتشغيل خادم VNC مباشرة على منفذ 5901
"""
import os
import sys
import time
import signal
import subprocess
import socket
from pathlib import Path

# VNC Configuration
VNC_PORT = 5901
VNC_DISPLAY = ":1"
VNC_PASSWORD = "vnc123456"
SCREEN_RESOLUTION = "1024x768"
VNC_DEPTH = "24"

class VNCServer:
    def __init__(self):
        self.xvfb_process = None
        self.vnc_process = None
        self.wm_process = None
        self.firefox_process = None
        
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
            vnc_dir = Path.home() / ".vnc"
            vnc_dir.mkdir(exist_ok=True)
            
            # إنشاء كلمة مرور VNC
            passwd_cmd = f'echo "{VNC_PASSWORD}" | vncpasswd -f > {vnc_dir}/passwd'
            os.system(passwd_cmd)
            os.chmod(vnc_dir / "passwd", 0o600)
            
            print(f"✓ تم إعداد كلمة مرور VNC: {VNC_PASSWORD}")
            return True
        except Exception as e:
            print(f"✗ خطأ في إعداد كلمة المرور: {e}")
            return False
    
    def start_xvfb(self):
        """تشغيل Xvfb (X Virtual Framebuffer)"""
        try:
            cmd = [
                "Xvfb", VNC_DISPLAY,
                "-screen", "0", f"{SCREEN_RESOLUTION}x{VNC_DEPTH}",
                "-ac", "-nolisten", "tcp"
            ]
            
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # انتظار قصير للتأكد من بدء Xvfb
            time.sleep(2)
            
            if self.xvfb_process.poll() is None:
                print(f"✓ تم تشغيل Xvfb على العرض {VNC_DISPLAY}")
                return True
            else:
                print("✗ فشل في تشغيل Xvfb")
                return False
                
        except Exception as e:
            print(f"✗ خطأ في تشغيل Xvfb: {e}")
            return False
    
    def start_window_manager(self):
        """تشغيل مدير النوافذ (Openbox)"""
        try:
            env = os.environ.copy()
            env["DISPLAY"] = VNC_DISPLAY
            
            self.wm_process = subprocess.Popen(
                ["openbox"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(1)
            print("✓ تم تشغيل مدير النوافذ Openbox")
            return True
            
        except Exception as e:
            print(f"✗ خطأ في تشغيل مدير النوافذ: {e}")
            return False
    
    def start_vnc_server(self):
        """تشغيل خادم VNC"""
        try:
            vnc_passwd_file = Path.home() / ".vnc" / "passwd"
            
            cmd = [
                "x11vnc",
                "-display", VNC_DISPLAY,
                "-rfbport", str(VNC_PORT),
                "-rfbauth", str(vnc_passwd_file),
                "-forever",
                "-shared",
                "-allow", "0.0.0.0/0",
                "-noxdamage",
                "-noxfixes",
                "-noxinerama"
            ]
            
            self.vnc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # انتظار لضمان بدء الخادم
            time.sleep(3)
            
            if self.is_port_open(VNC_PORT):
                print(f"✓ خادم VNC يعمل على المنفذ {VNC_PORT}")
                return True
            else:
                print("✗ فشل في تشغيل خادم VNC")
                return False
                
        except Exception as e:
            print(f"✗ خطأ في تشغيل خادم VNC: {e}")
            return False
    
    def start_firefox(self):
        """تشغيل متصفح Firefox"""
        try:
            env = os.environ.copy()
            env["DISPLAY"] = VNC_DISPLAY
            
            self.firefox_process = subprocess.Popen(
                ["firefox", "--new-instance"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("✓ تم تشغيل متصفح Firefox")
            return True
            
        except Exception as e:
            print(f"✗ خطأ في تشغيل Firefox: {e}")
            return False
    
    def is_port_open(self, port):
        """فحص ما إذا كان المنفذ مفتوحاً"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def get_connection_info(self):
        """الحصول على معلومات الاتصال"""
        # جلب URL الخاص بـ Replit
        repl_url = os.getenv('REPLIT_URL', 'https://your-repl.replit.app')
        if repl_url.startswith('http://'):
            repl_url = repl_url.replace('http://', 'https://')
        
        print("\n" + "="*50)
        print("🖥️  معلومات الاتصال بـ VNC")
        print("="*50)
        print(f"🔗 العنوان الخارجي: {repl_url}:{VNC_PORT}")
        print(f"🔗 العنوان المحلي: localhost:{VNC_PORT}")
        print(f"🔑 كلمة المرور: {VNC_PASSWORD}")
        print(f"📺 دقة الشاشة: {SCREEN_RESOLUTION}")
        print("="*50)
        print("📱 للاتصال من برنامج VNC:")
        print(f"   - Server: {repl_url.replace('https://', '')}:{VNC_PORT}")
        print(f"   - Password: {VNC_PASSWORD}")
        print("="*50)
    
    def start_all(self):
        """تشغيل جميع الخدمات"""
        print("🚀 بدء تشغيل خادم VNC المباشر...")
        print("-" * 40)
        
        # إعداد كلمة المرور
        if not self.setup_vnc_password():
            return False
        
        # تشغيل Xvfb
        if not self.start_xvfb():
            return False
        
        # تشغيل مدير النوافذ
        if not self.start_window_manager():
            return False
        
        # تشغيل خادم VNC
        if not self.start_vnc_server():
            return False
        
        # تشغيل Firefox
        self.start_firefox()
        
        # عرض معلومات الاتصال
        self.get_connection_info()
        
        return True
    
    def stop_all(self):
        """إيقاف جميع الخدمات"""
        print("🛑 إيقاف خدمات VNC...")
        
        processes = [
            (self.firefox_process, "Firefox"),
            (self.vnc_process, "VNC Server"),
            (self.wm_process, "Window Manager"),
            (self.xvfb_process, "Xvfb")
        ]
        
        for process, name in processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✓ تم إيقاف {name}")
                except:
                    try:
                        process.kill()
                        print(f"✓ تم إنهاء {name} قسرياً")
                    except:
                        print(f"✗ فشل في إيقاف {name}")
    
    def signal_handler(self, sig, frame):
        """معالج الإشارات للإيقاف النظيف"""
        print("\n🛑 تم استلام إشارة الإيقاف...")
        self.stop_all()
        sys.exit(0)

def main():
    """الدالة الرئيسية"""
    vnc_server = VNCServer()
    
    # تسجيل معالجات الإشارات
    signal.signal(signal.SIGINT, vnc_server.signal_handler)
    signal.signal(signal.SIGTERM, vnc_server.signal_handler)
    
    # تشغيل الخادم
    if vnc_server.start_all():
        print("\n✅ تم تشغيل خادم VNC بنجاح!")
        print("⏳ اضغط Ctrl+C للإيقاف")
        
        # البقاء في حلقة لا نهائية
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("\n❌ فشل في تشغيل خادم VNC")
        sys.exit(1)

if __name__ == "__main__":
    main()