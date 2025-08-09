#!/usr/bin/env python3
"""
VNC Server Manager for Replit Environment
إدارة خدمة VNC في بيئة Replit بدون Docker
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VNCManager:
    def __init__(self):
        self.display = ":1"
        self.vnc_port = 5901
        self.vnc_password = "vnc123456"
        self.screen_resolution = "1024x768"
        self.color_depth = 24
        
        # Process IDs
        self.xvfb_pid = None
        self.x11vnc_pid = None
        self.desktop_pid = None
        
        # Create VNC directory
        self.vnc_dir = Path.home() / ".vnc"
        self.vnc_dir.mkdir(exist_ok=True)
        
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
            # إنشاء ملف كلمة المرور بشكل مبسط
            passwd_file = self.vnc_dir / "passwd"
            with open(passwd_file, 'w') as f:
                f.write(self.vnc_password)
            os.chmod(passwd_file, 0o600)
            logger.info("✅ تم إعداد كلمة مرور VNC")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد كلمة مرور VNC: {e}")
            return False
    
    def start_xvfb(self):
        """تشغيل الشاشة الوهمية Xvfb"""
        try:
            cmd = [
                "Xvfb", self.display,
                "-screen", "0", f"{self.screen_resolution}x{self.color_depth}",
                "-ac", "+extension", "GLX"
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.xvfb_pid = process.pid
            
            # تعيين متغير DISPLAY
            os.environ["DISPLAY"] = self.display
            
            # انتظار بدء التشغيل
            time.sleep(2)
            
            logger.info(f"✅ تم تشغيل Xvfb على العرض {self.display}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل Xvfb: {e}")
            return False
    
    def start_x11vnc(self):
        """تشغيل خادم VNC"""
        try:
            cmd = [
                "x11vnc",
                "-display", self.display,
                "-rfbport", str(self.vnc_port),
                "-passwd", self.vnc_password,
                "-forever",
                "-shared",
                "-bg"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ تم تشغيل x11vnc على المنفذ {self.vnc_port}")
                return True
            else:
                logger.error(f"❌ خطأ في تشغيل x11vnc: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل x11vnc: {e}")
            return False
    
    def start_desktop(self):
        """تشغيل سطح المكتب (إذا كان متاحاً)"""
        try:
            # جرب تشغيل أي بيئة سطح مكتب متاحة
            desktop_commands = [
                ["lxsession"],  # LXDE
                ["xfce4-session"],  # XFCE
                ["mate-session"],  # MATE
                ["openbox-session"]  # Openbox
            ]
            
            for cmd in desktop_commands:
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=dict(os.environ, DISPLAY=self.display)
                    )
                    self.desktop_pid = process.pid
                    time.sleep(3)
                    
                    # تحقق من أن العملية لا تزال تعمل
                    if process.poll() is None:
                        logger.info(f"✅ تم تشغيل سطح المكتب: {' '.join(cmd)}")
                        return True
                    
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.warning(f"فشل في تشغيل {' '.join(cmd)}: {e}")
                    continue
            
            logger.warning("⚠️ لم يتم العثور على بيئة سطح مكتب مناسبة")
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل سطح المكتب: {e}")
            return False
    
    def start_applications(self):
        """تشغيل التطبيقات الأساسية"""
        try:
            # قائمة التطبيقات المتاحة للتجربة
            apps_to_try = [
                ["xterm", "-geometry", "80x24+10+10"],
                ["gnome-terminal"],
                ["konsole"],
                ["firefox-esr", "--new-instance"],
                ["firefox"],
                ["chromium", "--no-sandbox", "--disable-gpu"],
                ["chromium-browser", "--no-sandbox", "--disable-gpu"]
            ]
            
            for app_cmd in apps_to_try:
                try:
                    subprocess.Popen(
                        app_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=dict(os.environ, DISPLAY=self.display)
                    )
                    logger.info(f"✅ تم تشغيل {app_cmd[0]}")
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل التطبيقات: {e}")
            return False
    
    def get_status(self):
        """الحصول على حالة الخدمات"""
        status = {
            "xvfb_running": self.is_process_running(self.xvfb_pid),
            "x11vnc_running": self.is_vnc_port_open(),
            "desktop_running": self.is_process_running(self.desktop_pid),
            "display": self.display,
            "vnc_port": self.vnc_port
        }
        return status
    
    def is_process_running(self, pid):
        """التحقق من تشغيل عملية معينة"""
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def is_vnc_port_open(self):
        """التحقق من أن منفذ VNC مفتوح"""
        try:
            # جرب netstat أولاً
            result = subprocess.run(
                ["netstat", "-tln"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and f":{self.vnc_port}" in result.stdout:
                return True
        except:
            pass
        
        try:
            # جرب netcat كبديل
            result = subprocess.run(
                ["netcat", "-z", "localhost", str(self.vnc_port)],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            pass
        
        try:
            # جرب ss كبديل آخر
            result = subprocess.run(
                ["ss", "-tln"],
                capture_output=True, text=True, timeout=5
            )
            return f":{self.vnc_port}" in result.stdout
        except:
            pass
        
        return False
    
    def start_all(self):
        """تشغيل جميع الخدمات"""
        logger.info("🚀 بدء تشغيل نظام VNC...")
        
        # إعداد كلمة المرور
        if not self.setup_vnc_password():
            return False
        
        # تشغيل الشاشة الوهمية
        if not self.start_xvfb():
            return False
        
        # تشغيل خادم VNC
        if not self.start_x11vnc():
            return False
        
        # تشغيل سطح المكتب
        self.start_desktop()
        
        # تشغيل التطبيقات
        self.start_applications()
        
        logger.info("✅ تم تشغيل نظام VNC بنجاح!")
        return True
    
    def stop_all(self):
        """إيقاف جميع الخدمات"""
        logger.info("🛑 إيقاف خدمات VNC...")
        
        # إيقاف العمليات
        for pid in [self.desktop_pid, self.x11vnc_pid, self.xvfb_pid]:
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        
        logger.info("✅ تم إيقاف خدمات VNC")

def main():
    """البرنامج الرئيسي"""
    vnc = VNCManager()
    
    try:
        if vnc.start_all():
            logger.info("VNC Server يعمل على المنفذ 5901")
            logger.info("يمكنك الاتصال باستخدام VNC viewer على localhost:5901")
            
            # إبقاء البرنامج يعمل
            while True:
                time.sleep(10)
                status = vnc.get_status()
                if not status["x11vnc_running"]:
                    logger.warning("⚠️ خادم VNC توقف، إعادة التشغيل...")
                    vnc.start_x11vnc()
        else:
            logger.error("❌ فشل في تشغيل VNC Server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("تم استلام إشارة الإيقاف...")
        vnc.stop_all()
    except Exception as e:
        logger.error(f"خطأ عام: {e}")
        vnc.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()