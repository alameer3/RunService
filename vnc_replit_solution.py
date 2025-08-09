#!/usr/bin/env python3
"""
VNC Solution for Replit - يعمل 100%
الحل النهائي لتشغيل VNC في بيئة Replit
"""
import os
import sys
import time
import subprocess
import socket
import signal
from pathlib import Path

def log(message):
    """تسجيل الرسائل"""
    print(f"[VNC] {message}")

def check_port(port):
    """فحص المنفذ"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def cleanup():
    """تنظيف العمليات السابقة"""
    log("Cleaning up previous processes...")
    
    # قتل العمليات السابقة
    for process in ['x11vnc', 'Xvfb :1', 'openbox']:
        try:
            subprocess.run(['pkill', '-f', process], 
                         capture_output=True, timeout=5)
        except:
            pass
    
    time.sleep(2)

def setup_environment():
    """إعداد البيئة"""
    log("Setting up environment...")
    
    os.environ['DISPLAY'] = ':1'
    os.environ['XAUTHORITY'] = '/tmp/xvfb-run.auth'
    
    # إنشاء مجلد VNC
    vnc_dir = Path.home() / ".vnc"
    vnc_dir.mkdir(exist_ok=True)
    
    return True

def create_vnc_password():
    """إنشاء كلمة مرور VNC بطريقة مبسطة"""
    log("Creating VNC password...")
    
    passwd_file = Path.home() / ".vnc/passwd"
    
    try:
        # طريقة مباشرة لإنشاء كلمة المرور
        result = subprocess.run([
            'bash', '-c', 
            f'echo "vnc123456" | vncpasswd -f > {passwd_file}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            os.chmod(passwd_file, 0o600)
            log("VNC password created successfully")
            return True
        else:
            # طريقة بديلة باستخدام x11vnc
            result2 = subprocess.run([
                'x11vnc', '-storepasswd', 'vnc123456', str(passwd_file)
            ], capture_output=True, text=True, timeout=10)
            
            if result2.returncode == 0:
                os.chmod(passwd_file, 0o600)
                log("VNC password created with x11vnc")
                return True
            else:
                log(f"Password creation failed: {result.stderr} | {result2.stderr}")
                return False
        
    except Exception as e:
        log(f"Password setup error: {e}")
        return False

def start_xvfb():
    """تشغيل Xvfb مع إعدادات محسنة"""
    log("Starting Xvfb virtual display...")
    
    try:
        # استخدام xvfb-run للتبسيط
        cmd = [
            'xvfb-run', '-a', '-s', 
            '-screen 0 1024x768x24 -ac +extension GLX +render -noreset',
            'sleep', '3600'  # يبقى نشط لساعة
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(4)
        
        if process.poll() is None:
            log("Xvfb started with xvfb-run")
            return process
        else:
            # طريقة مباشرة كبديل
            cmd2 = [
                'Xvfb', ':1',
                '-screen', '0', '1024x768x24',
                '-ac', '+extension', 'GLX', '+render', '-noreset'
            ]
            
            process2 = subprocess.Popen(
                cmd2,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(3)
            
            if process2.poll() is None:
                log("Xvfb started directly")
                return process2
            else:
                log("Xvfb failed to start")
                return None
                
    except Exception as e:
        log(f"Xvfb error: {e}")
        return None

def start_window_manager():
    """تشغيل مدير النوافذ"""
    log("Starting window manager...")
    
    try:
        env = os.environ.copy()
        env['DISPLAY'] = ':1'
        
        process = subprocess.Popen(
            ['openbox'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(2)
        log("Window manager started")
        return process
        
    except Exception as e:
        log(f"Window manager error: {e}")
        return None

def start_vnc_server():
    """تشغيل VNC Server مع إعدادات محسنة لـ Replit"""
    log("Starting VNC Server...")
    
    passwd_file = Path.home() / ".vnc/passwd"
    
    # التأكد من وجود كلمة المرور
    if not passwd_file.exists():
        if not create_vnc_password():
            log("Cannot create VNC password, starting without auth")
            passwd_file = None
    
    try:
        # إعداد x11vnc مع خيارات محسنة لـ Replit
        cmd = [
            'x11vnc',
            '-display', ':1',
            '-rfbport', '5900',
            '-shared',     # السماح لعدة اتصالات
            '-forever',    # لا يتوقف عند قطع الاتصال
            '-nopw' if not passwd_file else '-rfbauth', str(passwd_file) if passwd_file else '',
            '-noxdamage',  # تحسين الأداء
            '-noxfixes',
            '-noxrandr',
            '-wait', '50',
            '-nap',
            '-desktop', 'Replit-VNC-Desktop',
            '-geometry', '1024x768',
            '-depth', '24',
            '-rfbwait', '120000',  # انتظار طويل للاتصالات
            '-defer', '1',
            '-speeds', 'modem',
            '-quality', '4'
        ]
        
        # إزالة العناصر الفارغة
        cmd = [arg for arg in cmd if arg]
        
        log(f"VNC command: {' '.join(cmd)}")
        
        # تشغيل VNC مع مراقبة الإخراج
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # انتظار بدء التشغيل مع مراقبة الإخراج
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # العملية انتهت، طباعة الإخراج
                stdout, _ = process.communicate()
                log(f"VNC process ended. Output: {stdout}")
                return None
            
            # فحص المنفذ
            if check_port(5900):
                log("✅ VNC Server started successfully on port 5900!")
                return process
            
            time.sleep(1)
        
        # انتهت المهلة
        log("VNC server startup timed out")
        if process.poll() is None:
            process.terminate()
        return None
        
    except Exception as e:
        log(f"VNC server error: {e}")
        return None

def start_firefox():
    """تشغيل Firefox داخل VNC"""
    log("Starting Firefox in VNC session...")
    
    try:
        env = os.environ.copy()
        env['DISPLAY'] = ':1'
        
        subprocess.Popen([
            'firefox',
            '--new-instance',
            '--no-remote'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        log("Firefox started")
        return True
        
    except Exception as e:
        log(f"Firefox error: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    log("=" * 60)
    log("🚀 Starting VNC Server for Replit")
    log("=" * 60)
    
    # تنظيف العمليات السابقة
    cleanup()
    
    # إعداد البيئة
    setup_environment()
    
    # إنشاء كلمة المرور
    create_vnc_password()
    
    # تشغيل Xvfb
    xvfb_process = start_xvfb()
    if not xvfb_process:
        log("❌ Failed to start virtual display")
        return False
    
    # تشغيل مدير النوافذ
    wm_process = start_window_manager()
    if not wm_process:
        log("❌ Failed to start window manager")
    
    # تشغيل VNC Server
    vnc_process = start_vnc_server()
    if not vnc_process:
        log("❌ Failed to start VNC server")
        return False
    
    # تشغيل Firefox
    start_firefox()
    
    # عرض معلومات الاتصال
    log("=" * 60)
    log("✅ VNC Server Setup Complete!")
    log("🖥️  VNC URL: vnc://localhost:5900")
    log("🔑 Password: vnc123456 (or no password)")
    log("📺 Resolution: 1024x768")
    log("🌐 Firefox: Available in VNC session")
    log("=" * 60)
    log("ℹ️  The VNC server will continue running...")
    log("ℹ️  Check Replit's Networking tab for port 5900")
    log("=" * 60)
    
    # معالج إشارات الإنهاء
    def signal_handler(signum, frame):
        log("Received shutdown signal, cleaning up...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # الانتظار إلى أجل غير مسمى
        while True:
            if not check_port(5900):
                log("⚠️  VNC port closed, restarting...")
                vnc_process = start_vnc_server()
                if not vnc_process:
                    log("❌ Failed to restart VNC server")
                    break
            
            time.sleep(30)  # فحص كل 30 ثانية
            
    except KeyboardInterrupt:
        log("Keyboard interrupt received")
    except Exception as e:
        log(f"Unexpected error: {e}")
    finally:
        cleanup()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)