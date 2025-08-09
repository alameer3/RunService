#!/usr/bin/env python3
"""
خادم VNC Desktop للعمل في بيئة Replit
يوفر بيئة سطح مكتب كاملة مع متصفح عبر VNC
"""

import os
import sys
import subprocess
import time
import socket
import threading
import signal
import logging
from pathlib import Path

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VNCDesktopServer:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.home_dir = Path.home()
        self.vnc_dir = self.home_dir / ".vnc"
        
        # إعدادات الخادم
        self.vnc_port = 5901
        self.display_num = ":1"
        self.screen_resolution = "1024x768"
        self.vnc_password = "vnc123456"
        
        # إعدادات Replit الخارجية
        self.repl_host = "0.0.0.0"  # الاستماع على جميع الواجهات
        
        # متغيرات العمليات
        self.processes = []
        self.running = False
        
        # إنشاء المجلدات المطلوبة
        self.vnc_dir.mkdir(exist_ok=True)
        
        logger.info(f"تم تهيئة خادم VNC Desktop")
        logger.info(f"المنفذ: {self.vnc_port}")
        logger.info(f"دقة الشاشة: {self.screen_resolution}")
    
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
            passwd_file = self.vnc_dir / "passwd"
            result = subprocess.run([
                "x11vnc", "-storepasswd", self.vnc_password, str(passwd_file)
            ], capture_output=True, text=True, input=self.vnc_password)
            
            if result.returncode == 0:
                logger.info("✅ تم إعداد كلمة مرور VNC")
                return True
            else:
                logger.warning("⚠️ فشل في إعداد كلمة مرور VNC، سيتم التشغيل بدون حماية")
                return False
        except Exception as e:
            logger.warning(f"⚠️ خطأ في إعداد كلمة المرور: {e}")
            return False
    
    def create_xstartup_script(self):
        """إنشاء سكريبت بدء سطح المكتب"""
        xstartup_file = self.vnc_dir / "xstartup"
        
        xstartup_content = f"""#!/bin/bash
export USER={os.getenv('USER', 'user')}
export HOME={self.home_dir}
export DISPLAY={self.display_num}

# بدء خدمة dbus إذا كانت متوفرة
if command -v dbus-launch >/dev/null 2>&1; then
    eval $(dbus-launch --sh-syntax) >/dev/null 2>&1 || true
fi

# بدء مدير النوافذ
if command -v openbox >/dev/null 2>&1; then
    openbox &
elif command -v fluxbox >/dev/null 2>&1; then
    fluxbox &
elif command -v icewm >/dev/null 2>&1; then
    icewm &
elif command -v twm >/dev/null 2>&1; then
    twm &
fi

# بدء شريط المهام
if command -v lxpanel >/dev/null 2>&1; then
    lxpanel &
elif command -v tint2 >/dev/null 2>&1; then
    tint2 &
fi

# بدء مدير الملفات
if command -v pcmanfm >/dev/null 2>&1; then
    pcmanfm --desktop &
elif command -v nautilus >/dev/null 2>&1; then
    nautilus --no-default-window &
fi

# انتظار قليل لبدء البيئة
sleep 3

# تشغيل Firefox تلقائياً
if command -v firefox >/dev/null 2>&1; then
    firefox --new-instance --no-remote "https://www.google.com" >/dev/null 2>&1 &
elif command -v firefox-esr >/dev/null 2>&1; then
    firefox-esr --new-instance --no-remote "https://www.google.com" >/dev/null 2>&1 &
elif command -v chromium >/dev/null 2>&1; then
    chromium --no-sandbox --disable-gpu "https://www.google.com" >/dev/null 2>&1 &
elif command -v chromium-browser >/dev/null 2>&1; then
    chromium-browser --no-sandbox --disable-gpu "https://www.google.com" >/dev/null 2>&1 &
fi

# تشغيل محطة طرفية
if command -v lxterminal >/dev/null 2>&1; then
    lxterminal --geometry=80x24+100+100 &
elif command -v xterm >/dev/null 2>&1; then
    xterm -geometry 80x24+100+100 -title "VNC Desktop Terminal" &
fi

# إبقاء الجلسة نشطة
while true; do
    sleep 1000
done
"""
        
        with open(xstartup_file, 'w') as f:
            f.write(xstartup_content)
        
        xstartup_file.chmod(0o755)
        logger.info("✅ تم إنشاء سكريبت بدء سطح المكتب")
    
    def start_xvfb(self):
        """بدء خادم العرض الافتراضي"""
        logger.info("🖥️ بدء تشغيل خادم العرض الافتراضي...")
        
        try:
            # إيقاف أي عمليات سابقة
            subprocess.run(["pkill", "-f", f"Xvfb.*{self.display_num}"], 
                         capture_output=True)
            time.sleep(1)
            
            # بدء Xvfb
            xvfb_cmd = [
                "Xvfb", self.display_num,
                "-screen", "0", f"{self.screen_resolution}x24",
                "-ac", "+extension", "GLX", "+render", "-noreset"
            ]
            
            xvfb_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.processes.append(xvfb_process)
            
            # انتظار بدء الخادم
            time.sleep(3)
            
            # تعيين متغير البيئة
            os.environ["DISPLAY"] = self.display_num
            
            # فحص حالة العملية
            if xvfb_process.poll() is None:
                logger.info(f"✅ تم بدء خادم العرض الافتراضي (PID: {xvfb_process.pid})")
                return True
            else:
                logger.error("❌ فشل في بدء خادم العرض الافتراضي")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في بدء خادم العرض: {e}")
            return False
    
    def start_desktop_environment(self):
        """بدء بيئة سطح المكتب"""
        logger.info("🏠 بدء تشغيل بيئة سطح المكتب...")
        
        try:
            # تشغيل سكريبت بدء سطح المكتب
            desktop_env = dict(os.environ)
            desktop_env["DISPLAY"] = self.display_num
            
            desktop_process = subprocess.Popen([
                "bash", str(self.vnc_dir / "xstartup")
            ], env=desktop_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.processes.append(desktop_process)
            
            # انتظار بدء البيئة
            time.sleep(5)
            
            logger.info("✅ تم بدء بيئة سطح المكتب")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء بيئة سطح المكتب: {e}")
            return False
    
    def start_vnc_server(self):
        """بدء خادم VNC"""
        logger.info("🌐 بدء تشغيل خادم VNC...")
        
        try:
            # إيقاف أي خوادم VNC سابقة
            subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
            time.sleep(1)
            
            # بناء أمر x11vnc للوصول الخارجي
            vnc_cmd = [
                "x11vnc",
                "-display", self.display_num,
                "-rfbport", str(self.vnc_port),
                "-forever",
                "-shared",
                "-noxdamage",
                "-noxrecord",
                "-listen", self.repl_host,  # الاستماع على جميع الواجهات
                "-permitfiletransfer"  # السماح بنقل الملفات
            ]
            
            # إضافة كلمة المرور إذا كانت متوفرة
            passwd_file = self.vnc_dir / "passwd"
            if passwd_file.exists():
                vnc_cmd.extend(["-rfbauth", str(passwd_file)])
                logger.info("🔐 استخدام كلمة مرور VNC")
            else:
                vnc_cmd.append("-nopw")
                logger.warning("⚠️ تشغيل VNC بدون كلمة مرور")
            
            # بدء خادم VNC
            vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.processes.append(vnc_process)
            
            # انتظار بدء الخادم
            time.sleep(3)
            
            # فحص حالة الخادم
            if vnc_process.poll() is None:
                logger.info(f"✅ تم بدء خادم VNC (PID: {vnc_process.pid})")
                return True
            else:
                logger.error("❌ فشل في بدء خادم VNC")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في بدء خادم VNC: {e}")
            return False
    
    def check_port_status(self):
        """فحص حالة المنفذ"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', self.vnc_port))
                if result == 0:
                    logger.info(f"✅ المنفذ {self.vnc_port} متاح ويستمع")
                    return True
                else:
                    logger.warning(f"⚠️ المنفذ {self.vnc_port} غير متاح")
                    return False
        except Exception as e:
            logger.error(f"❌ خطأ في فحص المنفذ: {e}")
            return False
    
    def show_connection_info(self):
        """عرض معلومات الاتصال"""
        logger.info("=" * 50)
        logger.info("🎉 تم بدء خادم VNC Desktop بنجاح!")
        logger.info("=" * 50)
        logger.info(f"🖥️ العنوان: localhost:{self.vnc_port}")
        logger.info(f"🔑 كلمة المرور: {self.vnc_password}")
        logger.info(f"📺 دقة الشاشة: {self.screen_resolution}")
        logger.info("")
        logger.info("للاتصال بسطح المكتب:")
        logger.info("1. افتح برنامج VNC Viewer")
        logger.info(f"2. أدخل العنوان: localhost:{self.vnc_port}")
        logger.info(f"3. أدخل كلمة المرور: {self.vnc_password}")
        logger.info("")
        logger.info("برامج VNC المُوصى بها:")
        logger.info("• VNC Viewer (RealVNC)")
        logger.info("• TigerVNC Viewer")
        logger.info("• TightVNC Viewer")
        logger.info("=" * 50)
    
    def cleanup(self):
        """تنظيف العمليات عند الإغلاق"""
        logger.info("🛑 إيقاف خادم VNC Desktop...")
        self.running = False
        
        # إيقاف جميع العمليات
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # إيقاف العمليات بالاسم
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-f", f"Xvfb.*{self.display_num}"], capture_output=True)
        
        logger.info("✅ تم إيقاف جميع العمليات")
    
    def signal_handler(self, signum, frame):
        """معالج إشارات النظام"""
        logger.info(f"تم استقبال إشارة {signum}")
        self.cleanup()
        sys.exit(0)
    
    def monitor_processes(self):
        """مراقب العمليات للتأكد من استمرار العمل"""
        while self.running:
            time.sleep(30)  # فحص كل 30 ثانية
            
            # فحص حالة العمليات
            dead_processes = []
            for i, process in enumerate(self.processes):
                if process.poll() is not None:
                    dead_processes.append(i)
            
            # إعادة تشغيل العمليات المتوقفة
            if dead_processes:
                logger.warning("⚠️ تم اكتشاف توقف في بعض العمليات")
                for i in reversed(dead_processes):
                    self.processes.pop(i)
                
                # إعادة تشغيل النظام
                logger.info("🔄 إعادة تشغيل الخدمات...")
                self.start_services()
    
    def start_services(self):
        """بدء جميع الخدمات"""
        success = True
        
        # بدء خادم العرض
        if not self.start_xvfb():
            success = False
        
        # بدء بيئة سطح المكتب
        if success and not self.start_desktop_environment():
            success = False
        
        # بدء خادم VNC
        if success and not self.start_vnc_server():
            success = False
        
        return success
    
    def run(self):
        """تشغيل خادم VNC Desktop"""
        logger.info("🚀 بدء تشغيل خادم VNC Desktop...")
        
        # إعداد معالجات الإشارات
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # إعداد كلمة المرور
        self.setup_vnc_password()
        
        # إنشاء سكريبت بدء سطح المكتب
        self.create_xstartup_script()
        
        # بدء الخدمات
        if not self.start_services():
            logger.error("❌ فشل في بدء الخدمات")
            self.cleanup()
            return False
        
        # فحص حالة المنفذ
        time.sleep(2)
        self.check_port_status()
        
        # عرض معلومات الاتصال
        self.show_connection_info()
        
        # تشغيل مراقب العمليات
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # إبقاء الخادم يعمل
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("تم استقبال إشارة إيقاف من المستخدم")
        finally:
            self.cleanup()
        
        return True

def main():
    """النقطة الرئيسية للبرنامج"""
    server = VNCDesktopServer()
    
    try:
        server.run()
    except Exception as e:
        logger.error(f"خطأ في تشغيل الخادم: {e}")
        server.cleanup()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())