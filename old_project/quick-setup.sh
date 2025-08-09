#!/bin/bash

# سكريبت الإعداد السريع - للاستخدام في بيئة Replit أو البيئات المحدودة
# يعمل بدون صلاحيات root ويستخدم المكونات المتاحة فقط

set -e

# الألوان
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=====================================
      الإعداد السريع لبيئة VNC
=====================================${NC}"
}

# التحقق من البيئة
check_environment() {
    print_status "فحص البيئة المتاحة..."
    
    # فحص المتطلبات الأساسية
    PYTHON_OK=$(python3 --version >/dev/null 2>&1 && echo "✅" || echo "❌")
    X11VNC_OK=$(command -v x11vnc >/dev/null 2>&1 && echo "✅" || echo "❌")
    XVFB_OK=$(command -v Xvfb >/dev/null 2>&1 && echo "✅" || echo "❌")
    FIREFOX_OK=$(command -v firefox >/dev/null 2>&1 || command -v firefox-esr >/dev/null 2>&1 && echo "✅" || echo "❌")
    
    echo "Python3: $PYTHON_OK"
    echo "x11vnc: $X11VNC_OK"
    echo "Xvfb: $XVFB_OK"
    echo "Firefox: $FIREFOX_OK"
    
    # تحقق من إمكانية التشغيل
    if [[ "$PYTHON_OK" == "❌" ]]; then
        print_error "Python3 مطلوب لتشغيل النظام"
        return 1
    fi
    
    print_success "البيئة جاهزة للإعداد"
}

# إعداد المجلدات
setup_directories() {
    print_status "إعداد المجلدات المطلوبة..."
    
    mkdir -p ~/.vnc
    mkdir -p ~/Desktop
    mkdir -p ~/logs
    
    print_success "تم إنشاء المجلدات"
}

# إعداد كلمة مرور VNC
setup_vnc_password() {
    print_status "إعداد كلمة مرور VNC..."
    
    VNC_PASSWORD="vnc123456"
    
    if command -v x11vnc >/dev/null 2>&1; then
        echo "$VNC_PASSWORD" | x11vnc -storepasswd ~/.vnc/passwd 2>/dev/null || {
            print_warning "فشل في إعداد كلمة مرور VNC، سيتم التشغيل بدون حماية"
            return 1
        }
        print_success "تم إعداد كلمة مرور VNC: $VNC_PASSWORD"
    else
        print_warning "x11vnc غير متوفر"
        return 1
    fi
}

# إنشاء سكريبت بدء سطح المكتب
create_desktop_script() {
    print_status "إنشاء سكريپت بدء سطح المكتب..."
    
    cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
export USER=$(whoami)
export HOME=$HOME

# بدء خدمة dbus إذا كانت متوفرة
if command -v dbus-launch >/dev/null 2>&1; then
    eval $(dbus-launch --sh-syntax) >/dev/null 2>&1 || true
fi

# بدء مدير النوافذ البسيط
if command -v openbox >/dev/null 2>&1; then
    openbox &
elif command -v fluxbox >/dev/null 2>&1; then
    fluxbox &
elif command -v icewm >/dev/null 2>&1; then
    icewm &
fi

# بدء شريط المهام إذا كان متوفراً
if command -v lxpanel >/dev/null 2>&1; then
    lxpanel &
elif command -v tint2 >/dev/null 2>&1; then
    tint2 &
fi

# تشغيل Firefox تلقائياً
sleep 3
if command -v firefox >/dev/null 2>&1; then
    firefox --new-instance --no-remote >/dev/null 2>&1 &
elif command -v firefox-esr >/dev/null 2>&1; then
    firefox-esr --new-instance --no-remote >/dev/null 2>&1 &
fi

# تشغيل محطة طرفية
if command -v xterm >/dev/null 2>&1; then
    exec xterm -geometry 80x24+0+0 -title "VNC Desktop"
else
    # إبقاء الجلسة مفتوحة
    while true; do
        sleep 1000
    done
fi
EOF
    
    chmod +x ~/.vnc/xstartup
    print_success "تم إنشاء سكريبت سطح المكتب"
}

# إنشاء سكريپت Python للخادم VNC المحاكي
create_vnc_simulator() {
    print_status "إنشاء خادم VNC محاكي..."
    
    cat > ~/vnc_server.py << 'EOF'
#!/usr/bin/env python3
"""
خادم VNC مبسط للبيئات المحدودة
"""
import socket
import threading
import time
import struct
import os
import subprocess
import signal
import sys

class SimpleVNCServer:
    def __init__(self, port=5901):
        self.port = port
        self.running = False
        self.display = ":1"
        
    def start_xvfb(self):
        """بدء خادم العرض الافتراضي"""
        try:
            # إيقاف أي عمليات سابقة
            subprocess.run(["pkill", "-f", "Xvfb.*:1"], capture_output=True)
            time.sleep(1)
            
            # بدء Xvfb
            self.xvfb_process = subprocess.Popen([
                "Xvfb", ":1",
                "-screen", "0", "1024x768x24",
                "-ac", "+extension", "GLX",
                "+render", "-noreset"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # انتظار بدء الخادم
            time.sleep(2)
            
            # تعيين متغير البيئة
            os.environ["DISPLAY"] = ":1"
            
            print(f"✅ تم بدء Xvfb على {self.display}")
            return True
            
        except Exception as e:
            print(f"❌ فشل في بدء Xvfb: {e}")
            return False
    
    def start_desktop(self):
        """بدء بيئة سطح المكتب"""
        try:
            # تشغيل سكريبت سطح المكتب
            subprocess.Popen([
                "bash", os.path.expanduser("~/.vnc/xstartup")
            ], env=dict(os.environ, DISPLAY=":1"))
            
            print("✅ تم بدء بيئة سطح المكتب")
            return True
            
        except Exception as e:
            print(f"❌ فشل في بدء سطح المكتب: {e}")
            return False
    
    def start_vnc(self):
        """بدء خادم VNC"""
        try:
            # إيقاف أي عمليات VNC سابقة
            subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
            time.sleep(1)
            
            # بناء أمر x11vnc
            vnc_cmd = [
                "x11vnc",
                "-display", ":1",
                "-rfbport", str(self.port),
                "-forever",
                "-shared",
                "-noxdamage"
            ]
            
            # إضافة كلمة المرور إذا كانت متوفرة
            passwd_file = os.path.expanduser("~/.vnc/passwd")
            if os.path.exists(passwd_file):
                vnc_cmd.extend(["-rfbauth", passwd_file])
                print("🔐 استخدام كلمة مرور VNC")
            else:
                vnc_cmd.append("-nopw")
                print("⚠️  تشغيل VNC بدون كلمة مرور")
            
            # بدء x11vnc
            self.vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # انتظار بدء الخادم
            time.sleep(3)
            
            print(f"✅ تم بدء خادم VNC على المنفذ {self.port}")
            return True
            
        except Exception as e:
            print(f"❌ فشل في بدء خادم VNC: {e}")
            return False
    
    def check_port(self):
        """فحص المنفذ"""
        try:
            result = subprocess.run([
                "netstat", "-tlnp"
            ], capture_output=True, text=True)
            
            if f":{self.port}" in result.stdout:
                print(f"✅ المنفذ {self.port} متاح ويستمع")
                return True
            else:
                print(f"⚠️  المنفذ {self.port} غير متاح")
                return False
                
        except Exception:
            return False
    
    def show_info(self):
        """عرض معلومات الاتصال"""
        print("\n" + "="*40)
        print("   معلومات الاتصال بسطح المكتب")
        print("="*40)
        print(f"🖥️  المنفذ: {self.port}")
        print(f"🔑  كلمة المرور: vnc123456")
        print(f"📺  دقة الشاشة: 1024x768")
        print("\nللاتصال:")
        print("1. افتح برنامج VNC Viewer")
        print(f"2. أدخل العنوان: localhost:{self.port}")
        print("3. أدخل كلمة المرور: vnc123456")
        print("\n🎉 سطح المكتب VNC جاهز!")
        print("اضغط Ctrl+C للإيقاف...")
    
    def cleanup(self):
        """تنظيف العمليات"""
        print("\n🛑 إيقاف خادم VNC...")
        
        try:
            if hasattr(self, 'vnc_process'):
                self.vnc_process.terminate()
        except:
            pass
            
        try:
            if hasattr(self, 'xvfb_process'):
                self.xvfb_process.terminate()
        except:
            pass
        
        # إيقاف العمليات بالقوة
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-f", "Xvfb.*:1"], capture_output=True)
        
        print("✅ تم إيقاف جميع العمليات")
    
    def run(self):
        """تشغيل الخادم"""
        print("🚀 بدء تشغيل خادم VNC...")
        
        # معالجة إشارة الإيقاف
        def signal_handler(signum, frame):
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # بدء المكونات
        if not self.start_xvfb():
            return False
            
        if not self.start_desktop():
            return False
            
        if not self.start_vnc():
            return False
        
        # فحص الحالة
        time.sleep(2)
        self.check_port()
        self.show_info()
        
        # إبقاء الخادم يعمل
        try:
            while True:
                time.sleep(10)
                # فحص دوري للعمليات
                if hasattr(self, 'vnc_process') and self.vnc_process.poll() is not None:
                    print("⚠️  عملية VNC توقفت، إعادة التشغيل...")
                    self.start_vnc()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

if __name__ == "__main__":
    server = SimpleVNCServer(5901)
    server.run()
EOF
    
    chmod +x ~/vnc_server.py
    print_success "تم إنشاء خادم VNC المحاكي"
}

# إنشاء سكريبت التحكم
create_control_script() {
    print_status "إنشاء سكريپت التحكم..."
    
    cat > ~/control-vnc.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        echo "🚀 بدء تشغيل خادم VNC..."
        python3 ~/vnc_server.py &
        echo $! > ~/vnc_server.pid
        echo "✅ تم بدء الخادم"
        ;;
    stop)
        echo "🛑 إيقاف خادم VNC..."
        if [ -f ~/vnc_server.pid ]; then
            kill $(cat ~/vnc_server.pid) 2>/dev/null || true
            rm -f ~/vnc_server.pid
        fi
        pkill -f "vnc_server.py" 2>/dev/null || true
        pkill -f "x11vnc" 2>/dev/null || true
        pkill -f "Xvfb.*:1" 2>/dev/null || true
        echo "✅ تم إيقاف الخادم"
        ;;
    status)
        echo "📊 حالة خادم VNC:"
        if pgrep -f "vnc_server.py" > /dev/null; then
            echo "✅ خادم VNC يعمل"
        else
            echo "❌ خادم VNC متوقف"
        fi
        
        if pgrep -f "Xvfb.*:1" > /dev/null; then
            echo "✅ خادم العرض يعمل"
        else
            echo "❌ خادم العرض متوقف"
        fi
        
        netstat -tlnp 2>/dev/null | grep :5901 && echo "✅ المنفذ 5901 متاح" || echo "❌ المنفذ 5901 غير متاح"
        ;;
    info)
        echo "📋 معلومات الاتصال:"
        echo "   العنوان: localhost:5901"
        echo "   كلمة المرور: vnc123456"
        echo "   دقة الشاشة: 1024x768"
        ;;
    *)
        echo "الاستخدام: $0 {start|stop|status|info}"
        exit 1
        ;;
esac
EOF
    
    chmod +x ~/control-vnc.sh
    print_success "تم إنشاء سكريبت التحكم"
}

# عرض التعليمات النهائية
show_instructions() {
    print_header
    echo
    print_success "تم إكمال الإعداد السريع!"
    echo
    echo "🚀 لبدء خادم VNC:"
    echo "   ./control-vnc.sh start"
    echo
    echo "🛑 لإيقاف خادم VNC:"
    echo "   ./control-vnc.sh stop"
    echo
    echo "📊 لفحص الحالة:"
    echo "   ./control-vnc.sh status"
    echo
    echo "📋 لعرض معلومات الاتصال:"
    echo "   ./control-vnc.sh info"
    echo
    echo "🌐 للاتصال بسطح المكتب:"
    echo "   العنوان: localhost:5901"
    echo "   كلمة المرور: vnc123456"
    echo
    print_warning "ملاحظة: هذا الإعداد مخصص للبيئات المحدودة مثل Replit"
    print_warning "للحصول على إعداد كامل مع systemd، استخدم install.sh"
}

# الدالة الرئيسية
main() {
    print_header
    echo
    
    if ! check_environment; then
        print_error "البيئة غير مناسبة للإعداد"
        exit 1
    fi
    
    setup_directories
    setup_vnc_password
    create_desktop_script
    create_vnc_simulator
    create_control_script
    show_instructions
}

# تشغيل السكريپت
main "$@"