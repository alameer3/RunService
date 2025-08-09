#!/usr/bin/env python3
"""
Simple VNC Server for Replit Networking
خادم VNC بسيط وموثوق لـ Replit
"""
import os
import sys
import time
import subprocess
import socket
from pathlib import Path

def setup_vnc_password():
    """إعداد كلمة مرور VNC بطريقة مبسطة"""
    vnc_dir = Path.home() / ".vnc"
    vnc_dir.mkdir(exist_ok=True)
    
    # إنشاء كلمة المرور باستخدام أسلوب أبسط
    passwd_file = vnc_dir / "passwd"
    
    # استخدام vncpasswd مع input مباشر
    cmd = f'echo "vnc123456" | vncpasswd -f > {passwd_file}'
    result = os.system(cmd)
    
    if result == 0 and passwd_file.exists():
        os.chmod(passwd_file, 0o600)
        print("✓ تم إعداد كلمة مرور VNC")
        return True
    
    # طريقة بديلة يدوية
    try:
        with open(passwd_file, 'wb') as f:
            # كلمة مرور VNC مُرمزة لـ "vnc123456" 
            vnc_encoded = b'\x17\x52\x6b\x06\x23\x4e\x58\x07'
            f.write(vnc_encoded)
        os.chmod(passwd_file, 0o600)
        print("✓ تم إعداد كلمة مرور VNC (البديلة)")
        return True
    except Exception as e:
        print(f"خطأ في إعداد كلمة المرور: {e}")
        return False

def is_port_free(port):
    """فحص توفر المنفذ"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except:
        return False

def main():
    VNC_PORT = 5901
    DISPLAY = ":1"
    
    print("🚀 تشغيل خادم VNC البسيط...")
    
    # تنظيف العمليات السابقة
    os.system("pkill -f x11vnc > /dev/null 2>&1")
    os.system("pkill -f Xvfb > /dev/null 2>&1")
    time.sleep(2)
    
    # إعداد كلمة المرور
    if not setup_vnc_password():
        print("❌ فشل في إعداد كلمة المرور")
        sys.exit(1)
    
    # تشغيل Xvfb
    print("▶️  تشغيل Xvfb...")
    xvfb_cmd = f"Xvfb {DISPLAY} -screen 0 1024x768x24 -ac &"
    os.system(xvfb_cmd)
    time.sleep(3)
    
    # تشغيل مدير النوافذ
    print("▶️  تشغيل مدير النوافذ...")
    os.environ["DISPLAY"] = DISPLAY
    wm_cmd = "DISPLAY=:1 openbox &"
    os.system(wm_cmd)
    time.sleep(2)
    
    # تشغيل خادم VNC
    print(f"▶️  تشغيل خادم VNC على المنفذ {VNC_PORT}...")
    vnc_passwd_file = Path.home() / ".vnc" / "passwd"
    
    vnc_cmd = f"""x11vnc -display {DISPLAY} \
        -rfbport {VNC_PORT} \
        -rfbauth {vnc_passwd_file} \
        -forever \
        -shared \
        -noxdamage \
        -solid"""
    
    print("تشغيل x11vnc...")
    os.system(f"{vnc_cmd} &")
    
    # انتظار وفحص الخادم
    time.sleep(5)
    
    # فحص المنفذ
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', VNC_PORT))
            if result == 0:
                print("✅ خادم VNC يعمل بنجاح!")
                
                # عرض معلومات الاتصال
                repl_url = os.getenv('REPLIT_URL', 'localhost')
                if 'http' in repl_url:
                    repl_url = repl_url.split('/')[-1]
                
                print("\n" + "="*50)
                print("🖥️  معلومات الاتصال")
                print("="*50)
                print(f"🔗 العنوان: {repl_url}:{VNC_PORT}")
                print(f"🔑 كلمة المرور: vnc123456")
                print(f"📺 دقة الشاشة: 1024x768")
                print("="*50)
                print("✨ الآن يمكنك رؤية المنفذ في قسم Networking")
                print("="*50)
                
                # تشغيل Firefox
                print("▶️  تشغيل Firefox...")
                os.system("DISPLAY=:1 firefox &")
                
                # البقاء نشطاً
                try:
                    print("\n⏳ الخادم نشط. اضغط Ctrl+C للإيقاف")
                    while True:
                        time.sleep(10)
                        
                except KeyboardInterrupt:
                    print("\n🛑 إيقاف الخادم...")
                    
            else:
                print("❌ فشل في تشغيل خادم VNC")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()