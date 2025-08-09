#!/usr/bin/env python3
"""
VNC Server optimized for Replit Networking visibility
خادم VNC محسن لضمان الظهور في قسم الشبكة
"""
import os
import sys
import time
import subprocess
import socket
from pathlib import Path

def setup_display():
    """إعداد العرض الافتراضي"""
    os.environ['DISPLAY'] = ':1'
    return True

def setup_vnc_password():
    """إعداد كلمة مرور VNC"""
    vnc_dir = Path.home() / ".vnc"
    vnc_dir.mkdir(exist_ok=True)
    
    passwd_file = vnc_dir / "passwd"
    
    # استخدام vncpasswd بطريقة مبسطة
    try:
        result = subprocess.run([
            'bash', '-c', 
            'echo "vnc123456" | vncpasswd -f'
        ], capture_output=True, check=True)
        
        with open(passwd_file, 'wb') as f:
            f.write(result.stdout)
        
        os.chmod(passwd_file, 0o600)
        print("VNC password configured successfully")
        return True
        
    except Exception as e:
        print(f"Password setup failed: {e}")
        return False

def start_xvfb():
    """تشغيل Xvfb"""
    cmd = [
        "Xvfb", ":1",
        "-screen", "0", "1024x768x24",
        "-ac", "-nolisten", "tcp"
    ]
    
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("Xvfb started successfully")
        return True
    except Exception as e:
        print(f"Xvfb failed: {e}")
        return False

def start_window_manager():
    """تشغيل مدير النوافذ"""
    env = os.environ.copy()
    env['DISPLAY'] = ':1'
    
    try:
        subprocess.Popen(['openbox'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("Window manager started")
        return True
    except Exception as e:
        print(f"Window manager failed: {e}")
        return False

def start_vnc_server():
    """تشغيل خادم VNC مع ربط صريح للمنفذ"""
    vnc_passwd_file = Path.home() / ".vnc" / "passwd"
    
    if not vnc_passwd_file.exists():
        print("VNC password file missing")
        return False
    
    # استخدام x11vnc مع إعدادات محسنة للشبكة
    cmd = [
        "x11vnc",
        "-display", ":1",
        "-rfbport", "5900",
        "-rfbauth", str(vnc_passwd_file),
        "-listen", "0.0.0.0",  # الاستماع على جميع الواجهات
        "-forever",
        "-shared",
        "-solid",
        "-noxdamage"
    ]
    
    try:
        # تشغيل في المقدمة لضمان الرؤية
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # انتظار للتأكد من بدء التشغيل
        time.sleep(5)
        
        # فحص المنفذ
        if is_port_open(5900):
            print("VNC Server is running on port 5900")
            return process
        else:
            print("VNC Server failed to bind to port")
            return None
            
    except Exception as e:
        print(f"VNC Server startup failed: {e}")
        return None

def is_port_open(port):
    """فحص المنفذ"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0  # 0 means connection successful
    except Exception:
        return False

def start_firefox():
    """تشغيل Firefox"""
    env = os.environ.copy()
    env['DISPLAY'] = ':1'
    
    try:
        subprocess.Popen(['firefox'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Firefox started")
        return True
    except Exception as e:
        print(f"Firefox warning: {e}")
        return True  # لا نفشل العملية لأجل Firefox

def display_connection_info():
    """عرض معلومات الاتصال"""
    print("\n" + "="*50)
    print("VNC Server - Active and Ready")
    print("="*50)
    print("Port: 5900")
    print("Password: vnc123456")
    print("Resolution: 1024x768")
    print("="*50)
    print("The VNC port should now be visible in Replit's Networking tab")
    print("خادم VNC نشط ومرئي في قسم الشبكة")
    print("="*50)

def main():
    """التشغيل الرئيسي"""
    print("Starting VNC Server for Networking...")
    
    steps = [
        ("Setting up display", setup_display),
        ("Setting up VNC password", setup_vnc_password),
        ("Starting Xvfb", start_xvfb),
        ("Starting window manager", start_window_manager),
    ]
    
    # تنفيذ الخطوات الأساسية
    for step_name, step_func in steps:
        print(f"Step: {step_name}")
        if not step_func():
            print(f"Failed: {step_name}")
            sys.exit(1)
    
    # تشغيل خادم VNC
    print("Step: Starting VNC Server")
    vnc_process = start_vnc_server()
    
    if vnc_process is None:
        print("Failed to start VNC Server")
        sys.exit(1)
    
    # تشغيل Firefox
    start_firefox()
    
    # عرض معلومات الاتصال
    display_connection_info()
    
    # البقاء نشطاً
    try:
        print("VNC Server is running. Press Ctrl+C to stop.")
        while True:
            if vnc_process and vnc_process.poll() is not None:
                print("VNC process has stopped")
                break
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nShutting down VNC Server...")
        if vnc_process:
            vnc_process.terminate()

if __name__ == "__main__":
    main()