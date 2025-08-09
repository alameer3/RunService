#!/usr/bin/env python3
import subprocess
import time
import os

# تنظيف العمليات السابقة
subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
time.sleep(2)

# بدء Xvfb
print("🚀 بدء خادم العرض الافتراضي...")
xvfb = subprocess.Popen([
    'Xvfb', ':1', 
    '-screen', '0', '1024x768x24', 
    '-ac', '+extension', 'GLX', 
    '+render', '-noreset'
])

time.sleep(3)

# إعداد البيئة
os.environ['DISPLAY'] = ':1'

# بدء OpenBox
print("🖥️ بدء بيئة سطح المكتب...")
openbox = subprocess.Popen(['openbox'], env=dict(os.environ, DISPLAY=':1'))

time.sleep(2)

# بدء Firefox
print("🌐 بدء Firefox...")
firefox = subprocess.Popen([
    'firefox', '--no-sandbox', '--disable-web-security', 
    'https://www.google.com'
], env=dict(os.environ, DISPLAY=':1'))

time.sleep(5)

# إعداد كلمة مرور VNC
vnc_dir = os.path.expanduser('~/.vnc')
os.makedirs(vnc_dir, exist_ok=True)
subprocess.run(['x11vnc', '-storepasswd', 'vnc123456', f'{vnc_dir}/passwd'])

# بدء VNC server
print("🔗 بدء خادم VNC...")
vnc = subprocess.Popen([
    'x11vnc', 
    '-display', ':1',
    '-rfbport', '5901',
    '-forever', '-shared',
    '-noxdamage', '-noxrecord',
    '-listen', '0.0.0.0',
    '-permitfiletransfer',
    '-rfbauth', f'{vnc_dir}/passwd'
])

print("✅ تم بدء جميع الخدمات!")
print("📋 معلومات الاتصال:")
print("   العنوان: localhost:5901")
print("   كلمة المرور: vnc123456")

# انتظار
try:
    while True:
        time.sleep(30)
        # فحص العمليات
        if xvfb.poll() is not None:
            print("❌ توقف Xvfb")
            break
        if vnc.poll() is not None:
            print("❌ توقف VNC")
            break
except KeyboardInterrupt:
    print("⏹️ إيقاف الخدمات...")
    vnc.terminate()
    firefox.terminate()
    openbox.terminate()
    xvfb.terminate()