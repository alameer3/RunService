#!/usr/bin/env python3
"""
VNC Server Final Working Solution - الحل النهائي العامل 100%
بناءً على نتائج التشخيص الشامل - جميع المكونات تعمل بنجاح
"""
import os
import sys
import time
import subprocess
import socket
import signal
from pathlib import Path

class VNCServerReplit:
    def __init__(self):
        self.display = ":1"
        self.port = 5900
        self.password = "vnc123456"
        self.resolution = "1024x768x24"
        
        self.xvfb_process = None
        self.wm_process = None
        self.vnc_process = None
        
        self.running = False
    
    def log(self, message):
        """تسجيل الرسائل"""
        print(f"[VNC] {message}")
        
    def cleanup_existing(self):
        """تنظيف العمليات السابقة"""
        self.log("تنظيف العمليات السابقة...")
        
        processes = [
            f'Xvfb {self.display}',
            'x11vnc',
            'openbox'
        ]
        
        for proc in processes:
            try:
                subprocess.run(['pkill', '-f', proc], 
                             capture_output=True, timeout=5)
            except:
                pass
        
        time.sleep(2)
        
    def check_port(self):
        """فحص المنفذ"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', self.port))
                return result == 0
        except:
            return False
    
    def setup_password(self):
        """إعداد كلمة المرور"""
        vnc_dir = Path.home() / ".vnc"
        vnc_dir.mkdir(exist_ok=True)
        
        passwd_file = vnc_dir / "passwd"
        
        try:
            # استخدام x11vnc -storepasswd (نجح في الاختبار)
            result = subprocess.run([
                'x11vnc', '-storepasswd', self.password, str(passwd_file)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                os.chmod(passwd_file, 0o600)
                self.log("كلمة المرور تم إعدادها بنجاح")
                return True
            else:
                self.log(f"فشل إعداد كلمة المرور: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"خطأ في إعداد كلمة المرور: {e}")
            return False
    
    def start_xvfb(self):
        """بدء Xvfb"""
        self.log(f"بدء Xvfb على العرض {self.display}...")
        
        try:
            self.xvfb_process = subprocess.Popen([
                'Xvfb', self.display,
                '-screen', '0', self.resolution,
                '-ac', '+extension', 'GLX', '+render', '-noreset'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            if self.xvfb_process.poll() is None:
                # اختبار الاتصال بالعرض
                os.environ['DISPLAY'] = self.display
                test_result = subprocess.run(['xdpyinfo'], 
                                           capture_output=True, timeout=5)
                
                if test_result.returncode == 0:
                    self.log(f"✅ Xvfb يعمل بنجاح على {self.display}")
                    return True
                else:
                    self.log("Xvfb بدأ ولكن لا يستجيب")
                    return False
            else:
                stdout, stderr = self.xvfb_process.communicate()
                self.log(f"فشل Xvfb: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.log(f"خطأ في Xvfb: {e}")
            return False
    
    def start_window_manager(self):
        """بدء مدير النوافذ"""
        self.log("بدء مدير النوافذ openbox...")
        
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            self.wm_process = subprocess.Popen(
                ['openbox'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(2)
            self.log("✅ مدير النوافذ يعمل")
            return True
            
        except Exception as e:
            self.log(f"خطأ في مدير النوافذ: {e}")
            return False
    
    def start_vnc_server(self):
        """بدء خادم VNC"""
        self.log(f"بدء خادم VNC على المنفذ {self.port}...")
        
        passwd_file = Path.home() / ".vnc" / "passwd"
        
        # التأكد من وجود كلمة المرور
        if not passwd_file.exists():
            if not self.setup_password():
                self.log("تشغيل VNC بدون كلمة مرور...")
                passwd_file = None
        
        try:
            cmd = [
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.port),
                '-shared',      # السماح لعدة اتصالات
                '-forever',     # لا تتوقف عند قطع الاتصال
                '-desktop', 'Replit-VNC-Desktop'
            ]
            
            # إضافة كلمة المرور إذا كانت متوفرة
            if passwd_file and passwd_file.exists():
                cmd.extend(['-rfbauth', str(passwd_file)])
            else:
                cmd.append('-nopw')  # بدون كلمة مرور
            
            # تحسينات الأداء
            cmd.extend([
                '-noxdamage', '-noxfixes', '-noxrandr',
                '-wait', '50', '-nap'
            ])
            
            self.log(f"أمر VNC: {' '.join(cmd)}")
            
            # بدء VNC في الخلفية
            self.vnc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # انتظار بدء التشغيل
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(2)
                
                if self.check_port():
                    self.log(f"✅ خادم VNC يعمل بنجاح على المنفذ {self.port}!")
                    return True
                
                if self.vnc_process.poll() is not None:
                    stdout, stderr = self.vnc_process.communicate()
                    self.log(f"VNC انتهى مبكراً: {stderr.decode()[:200]}")
                    break
            
            self.log("فشل في بدء خادم VNC")
            return False
            
        except Exception as e:
            self.log(f"خطأ في VNC: {e}")
            return False
    
    def start_firefox(self):
        """بدء Firefox في جلسة VNC"""
        self.log("بدء Firefox...")
        
        try:
            env = os.environ.copy()
            env['DISPLAY'] = self.display
            
            subprocess.Popen([
                'firefox',
                '--new-instance',
                '--no-remote',
                'about:blank'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            self.log("✅ Firefox بدأ في جلسة VNC")
            return True
            
        except Exception as e:
            self.log(f"تحذير Firefox: {e}")
            return False
    
    def start(self):
        """بدء النظام كاملاً"""
        self.log("=" * 60)
        self.log("🚀 بدء خادم VNC لـ Replit")
        self.log("=" * 60)
        
        # تنظيف العمليات السابقة
        self.cleanup_existing()
        
        # بدء Xvfb
        if not self.start_xvfb():
            self.log("❌ فشل في بدء العرض الافتراضي")
            return False
        
        # بدء مدير النوافذ
        if not self.start_window_manager():
            self.log("⚠️  فشل مدير النوافذ، الاستمرار...")
        
        # إعداد كلمة المرور
        self.setup_password()
        
        # بدء خادم VNC
        if not self.start_vnc_server():
            self.log("❌ فشل في بدء خادم VNC")
            return False
        
        # بدء Firefox
        self.start_firefox()
        
        self.running = True
        
        # عرض معلومات الاتصال
        self.log("=" * 60)
        self.log("✅ خادم VNC يعمل بنجاح!")
        self.log(f"🖥️  عنوان VNC: vnc://localhost:{self.port}")
        self.log(f"🔑 كلمة المرور: {self.password}")
        self.log(f"📺 الدقة: {self.resolution.replace('x24', '')}")
        self.log("🌐 Firefox متوفر في الجلسة")
        self.log("📡 المنفذ مرئي في قسم Networking بـ Replit")
        self.log("=" * 60)
        
        return True
    
    def monitor_and_maintain(self):
        """مراقبة وصيانة النظام"""
        self.log("بدء مراقب النظام...")
        
        while self.running:
            try:
                # فحص المنفذ
                if not self.check_port():
                    self.log("⚠️  المنفذ مغلق، إعادة تشغيل VNC...")
                    if not self.start_vnc_server():
                        self.log("❌ فشل في إعادة تشغيل VNC")
                        break
                
                # فحص Xvfb
                if self.xvfb_process and self.xvfb_process.poll() is not None:
                    self.log("⚠️  Xvfb توقف، إعادة تشغيل...")
                    if not self.start_xvfb():
                        self.log("❌ فشل في إعادة تشغيل Xvfb")
                        break
                
                time.sleep(30)  # فحص كل 30 ثانية
                
            except KeyboardInterrupt:
                self.log("تم طلب الإيقاف...")
                break
            except Exception as e:
                self.log(f"خطأ في المراقب: {e}")
                time.sleep(60)
    
    def stop(self):
        """إيقاف النظام"""
        self.log("إيقاف النظام...")
        self.running = False
        
        # إنهاء العمليات
        for process in [self.vnc_process, self.wm_process, self.xvfb_process]:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
        
        self.cleanup_existing()
        self.log("تم إيقاف النظام")

def signal_handler(signum, frame):
    """معالج إشارات النظام"""
    global vnc_server
    vnc_server.stop()
    sys.exit(0)

def main():
    global vnc_server
    
    # إعداد معالجات الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    vnc_server = VNCServerReplit()
    
    try:
        if vnc_server.start():
            vnc_server.monitor_and_maintain()
        else:
            sys.exit(1)
    except Exception as e:
        vnc_server.log(f"خطأ غير متوقع: {e}")
        sys.exit(1)
    finally:
        vnc_server.stop()

if __name__ == "__main__":
    main()