#!/usr/bin/env python3
"""
Multi VNC Manager - مدير VNC متعدد الواجهات  
تشغيل عدة واجهات VNC على منافذ مختلفة لنفس سطح المكتب
"""

import os
import sys
import subprocess
import time
import signal
import logging
import threading
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiVNCManager:
    def __init__(self):
        self.display = ":1"
        self.screen_resolution = "1024x768"
        self.color_depth = 24
        self.vnc_password = "vnc123456"
        
        # تعريف المنافذ المختلفة
        self.vnc_configs = {
            'main': {'port': 5900, 'description': 'الواجهة الرئيسية'},
            'web': {'port': 5901, 'description': 'واجهة الويب'},
            'mobile': {'port': 5902, 'description': 'واجهة الموبايل'},
            'admin': {'port': 5903, 'description': 'واجهة الإدارة'},
        }
        
        # معرفات العمليات
        self.process_pids = {}
        self.xvfb_pid = None
        
        # إعداد مجلد VNC
        self.vnc_dir = Path.home() / ".vnc"
        self.vnc_dir.mkdir(exist_ok=True)
    
    def setup_vnc_password(self):
        """إعداد كلمة مرور VNC"""
        try:
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
        """تشغيل الشاشة الوهمية المشتركة"""
        try:
            # إيقاف أي Xvfb موجود
            subprocess.run(["pkill", "-f", "Xvfb"], capture_output=True)
            time.sleep(1)
            
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
    
    def start_vnc_server(self, config_name, port, description):
        """تشغيل خادم VNC على منفذ محدد"""
        try:
            logger.info(f"🚀 تشغيل {description} على المنفذ {port}")
            
            # إيقاف أي خدمة VNC على نفس المنفذ
            subprocess.run(["pkill", "-f", f"rfbport {port}"], capture_output=True)
            time.sleep(1)
            
            cmd = [
                "x11vnc",
                "-display", self.display,
                "-rfbport", str(port),
                "-passwd", self.vnc_password,
                "-forever",
                "-shared",
                "-noxdamage",
                "-noxfixes", 
                "-noscr",
                "-quiet"
            ]
            
            # إضافة معاملات خاصة حسب نوع الواجهة
            if config_name == 'web':
                cmd.extend(["-http", f"{port + 100}"])  # HTTP على منفذ أعلى
            elif config_name == 'mobile':
                cmd.extend(["-scale", "0.8"])  # تصغير للموبايل
            elif config_name == 'admin':
                cmd.extend(["-viewonly"])  # للعرض فقط
            
            cmd.append("-bg")  # تشغيل في الخلفية
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            time.sleep(2)
            
            # التحقق من تشغيل VNC
            check_result = subprocess.run(
                ["pgrep", "-f", f"rfbport {port}"], 
                capture_output=True
            )
            
            if check_result.returncode == 0:
                self.process_pids[config_name] = check_result.stdout.strip().split('\n')[0]
                logger.info(f"✅ تم تشغيل {description} بنجاح على المنفذ {port}")
                return True
            else:
                logger.error(f"❌ فشل في تشغيل {description} على المنفذ {port}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل {description}: {e}")
            return False
    
    def start_desktop_applications(self):
        """تشغيل التطبيقات على سطح المكتب المشترك"""
        try:
            logger.info("📱 تشغيل تطبيقات سطح المكتب...")
            
            # قائمة التطبيقات للتشغيل
            apps = [
                ["openbox", "--config-file", "/dev/null"],  # مدير النوافذ
                ["xterm", "-geometry", "80x24+10+10", "-title", "Terminal Main"],
                ["xterm", "-geometry", "80x24+400+10", "-title", "Terminal 2"],
                ["firefox-esr", "--new-instance", "--profile", "/tmp/firefox-vnc"],
                ["chromium", "--no-sandbox", "--disable-gpu", "--app=http://localhost:5000"]
            ]
            
            # إنشاء ملف تعريف Firefox مؤقت
            subprocess.run(["mkdir", "-p", "/tmp/firefox-vnc"], capture_output=True)
            
            launched_count = 0
            for app_cmd in apps:
                try:
                    subprocess.Popen(
                        app_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=dict(os.environ, DISPLAY=self.display)
                    )
                    launched_count += 1
                    logger.info(f"✅ تم تشغيل {app_cmd[0]}")
                    time.sleep(1)  # انتظار قصير بين التطبيقات
                except FileNotFoundError:
                    logger.warning(f"⚠️ التطبيق غير موجود: {app_cmd[0]}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ فشل في تشغيل {app_cmd[0]}: {e}")
                    continue
            
            logger.info(f"✅ تم تشغيل {launched_count} تطبيق من أصل {len(apps)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل التطبيقات: {e}")
            return False
    
    def start_all_vnc_servers(self):
        """تشغيل جميع خوادم VNC"""
        success_count = 0
        
        for config_name, config in self.vnc_configs.items():
            if self.start_vnc_server(config_name, config['port'], config['description']):
                success_count += 1
        
        return success_count > 0
    
    def get_status(self):
        """الحصول على حالة جميع الخدمات"""
        status = {
            'xvfb_running': self.is_process_running(self.xvfb_pid),
            'display': self.display,
            'vnc_servers': {}
        }
        
        for config_name, config in self.vnc_configs.items():
            pid = self.process_pids.get(config_name)
            status['vnc_servers'][config_name] = {
                'port': config['port'],
                'description': config['description'],
                'running': self.is_port_open(config['port']),
                'pid': pid
            }
        
        return status
    
    def is_process_running(self, pid):
        """التحقق من تشغيل عملية معينة"""
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (OSError, ValueError):
            return False
    
    def is_port_open(self, port):
        """التحقق من أن المنفذ مفتوح"""
        try:
            result = subprocess.run(
                ["netcat", "-z", "localhost", str(port)],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def start_monitoring_thread(self):
        """بدء خيط مراقبة الخدمات"""
        def monitor():
            while True:
                time.sleep(30)  # فحص كل 30 ثانية
                
                # فحص وإعادة تشغيل الخدمات المتوقفة
                for config_name, config in self.vnc_configs.items():
                    if not self.is_port_open(config['port']):
                        logger.warning(f"⚠️ إعادة تشغيل {config['description']} على المنفذ {config['port']}")
                        self.start_vnc_server(config_name, config['port'], config['description'])
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("✅ تم بدء خيط مراقبة الخدمات")
    
    def start_all(self):
        """تشغيل النظام الكامل"""
        logger.info("🚀 بدء تشغيل نظام VNC متعدد الواجهات...")
        
        # إعداد كلمة المرور
        if not self.setup_vnc_password():
            return False
        
        # تشغيل الشاشة الوهمية
        if not self.start_xvfb():
            return False
        
        # تشغيل التطبيقات
        self.start_desktop_applications()
        
        # تشغيل خوادم VNC
        if not self.start_all_vnc_servers():
            logger.error("❌ فشل في تشغيل خوادم VNC")
            return False
        
        # بدء مراقبة الخدمات
        self.start_monitoring_thread()
        
        logger.info("✅ تم تشغيل نظام VNC متعدد الواجهات بنجاح!")
        self.print_connection_info()
        return True
    
    def print_connection_info(self):
        """طباعة معلومات الاتصال"""
        logger.info("\n" + "="*50)
        logger.info("📡 معلومات الاتصال بخوادم VNC:")
        logger.info("="*50)
        
        for config_name, config in self.vnc_configs.items():
            if self.is_port_open(config['port']):
                logger.info(f"✅ {config['description']}: localhost:{config['port']}")
            else:
                logger.info(f"❌ {config['description']}: غير متاح")
        
        logger.info(f"🔑 كلمة المرور: {self.vnc_password}")
        logger.info("="*50)
    
    def stop_all(self):
        """إيقاف جميع الخدمات"""
        logger.info("🛑 إيقاف خدمات VNC...")
        
        # إيقاف خوادم VNC
        for pid in self.process_pids.values():
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    os.kill(int(pid), signal.SIGKILL)
                except (OSError, ValueError):
                    pass
        
        # إيقاف Xvfb
        if self.xvfb_pid:
            try:
                os.kill(self.xvfb_pid, signal.SIGTERM)
                time.sleep(1)
                os.kill(self.xvfb_pid, signal.SIGKILL)
            except OSError:
                pass
        
        # قتل العمليات بالقوة
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-f", "Xvfb"], capture_output=True)
        
        logger.info("✅ تم إيقاف جميع خدمات VNC")

def main():
    """البرنامج الرئيسي"""
    vnc_manager = MultiVNCManager()
    
    try:
        if vnc_manager.start_all():
            logger.info("🎯 النظام يعمل، يمكنك الاتصال بالواجهات المختلفة")
            
            # إبقاء البرنامج يعمل
            while True:
                time.sleep(60)
                status = vnc_manager.get_status()
                running_servers = sum(1 for server in status['vnc_servers'].values() if server['running'])
                logger.info(f"📊 الحالة: {running_servers}/{len(vnc_manager.vnc_configs)} خوادم تعمل")
                
        else:
            logger.error("❌ فشل في تشغيل النظام")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("تم استلام إشارة الإيقاف...")
        vnc_manager.stop_all()
    except Exception as e:
        logger.error(f"خطأ عام: {e}")
        vnc_manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()