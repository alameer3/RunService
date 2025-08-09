#!/bin/bash

# سكريبت بدء تشغيل سطح المكتب VNC
# يستخدم لبدء سطح المكتب يدوياً أو من خلال Replit

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

# متغيرات التكوين
VNC_PORT=5901
VNC_USER="vncuser"
DISPLAY_NUM=1
SCREEN_RESOLUTION="1024x768"
VNC_PASSWORD="vnc123456"

# إنشاء مجلد VNC إذا لم يكن موجوداً
setup_vnc_dirs() {
    mkdir -p ~/.vnc
    mkdir -p ~/Desktop
}

# إنشاء ملف كلمة مرور VNC
setup_vnc_password() {
    echo "$VNC_PASSWORD" | x11vnc -storepasswd ~/.vnc/passwd 2>/dev/null || {
        print_warning "فشل في إعداد كلمة مرور VNC، سيتم التشغيل بدون كلمة مرور"
        return 1
    }
    print_success "تم إعداد كلمة مرور VNC"
}

# بدء خادم العرض الافتراضي
start_xvfb() {
    print_status "بدء تشغيل خادم العرض الافتراضي..."
    
    # إيقاف أي عمليات سابقة
    pkill -f "Xvfb :$DISPLAY_NUM" 2>/dev/null || true
    
    # بدء Xvfb
    Xvfb :$DISPLAY_NUM -screen 0 ${SCREEN_RESOLUTION}x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    
    # انتظار بدء الخادم
    sleep 2
    
    if kill -0 $XVFB_PID 2>/dev/null; then
        print_success "تم بدء خادم العرض الافتراضي (PID: $XVFB_PID)"
        export DISPLAY=:$DISPLAY_NUM
        return 0
    else
        print_error "فشل في بدء خادم العرض الافتراضي"
        return 1
    fi
}

# بدء بيئة سطح المكتب
start_desktop() {
    print_status "بدء تشغيل بيئة سطح المكتب..."
    
    export DISPLAY=:$DISPLAY_NUM
    export USER=$(whoami)
    export HOME=$HOME
    
    # بدء خدمة dbus
    if command -v dbus-launch >/dev/null 2>&1; then
        eval $(dbus-launch --sh-syntax) &>/dev/null
    fi
    
    # بدء بيئة LXDE
    if command -v lxsession >/dev/null 2>&1; then
        lxsession -s LXDE &
        print_success "تم بدء بيئة LXDE"
    elif command -v startlxde >/dev/null 2>&1; then
        startlxde &
        print_success "تم بدء بيئة LXDE"
    else
        print_warning "بيئة LXDE غير مثبتة، سيتم بدء xterm فقط"
        xterm &
    fi
    
    sleep 3
}

# بدء المتصفحات
start_browsers() {
    print_status "بدء تشغيل المتصفحات..."
    
    export DISPLAY=:$DISPLAY_NUM
    
    # محاولة بدء Firefox
    if command -v firefox >/dev/null 2>&1; then
        firefox --new-instance --no-remote &
        print_success "تم بدء Firefox"
    elif command -v firefox-esr >/dev/null 2>&1; then
        firefox-esr --new-instance --no-remote &
        print_success "تم بدء Firefox ESR"
    fi
    
    sleep 2
    
    # بدء محطة طرفية
    if command -v lxterminal >/dev/null 2>&1; then
        lxterminal &
    elif command -v xterm >/dev/null 2>&1; then
        xterm &
    fi
}

# بدء خادم VNC
start_vnc_server() {
    print_status "بدء تشغيل خادم VNC..."
    
    export DISPLAY=:$DISPLAY_NUM
    
    # إيقاف أي خوادم VNC سابقة
    pkill -f "x11vnc.*:$DISPLAY_NUM" 2>/dev/null || true
    
    # بناء أمر VNC
    VNC_CMD="x11vnc -display :$DISPLAY_NUM -rfbport $VNC_PORT -forever -shared -xrandr resize"
    
    # إضافة كلمة المرور إذا كانت متوفرة
    if [[ -f ~/.vnc/passwd ]]; then
        VNC_CMD="$VNC_CMD -rfbauth ~/.vnc/passwd"
        print_status "استخدام كلمة مرور VNC من ~/.vnc/passwd"
    else
        VNC_CMD="$VNC_CMD -nopw"
        print_warning "تشغيل VNC بدون كلمة مرور"
    fi
    
    # بدء خادم VNC
    $VNC_CMD &
    VNC_PID=$!
    
    # انتظار بدء الخادم
    sleep 3
    
    if kill -0 $VNC_PID 2>/dev/null; then
        print_success "تم بدء خادم VNC على المنفذ $VNC_PORT (PID: $VNC_PID)"
        return 0
    else
        print_error "فشل في بدء خادم VNC"
        return 1
    fi
}

# فحص المنافذ
check_ports() {
    print_status "فحص المنافذ المتاحة..."
    
    if command -v netstat >/dev/null 2>&1; then
        netstat -tlnp | grep :$VNC_PORT && print_success "المنفذ $VNC_PORT متاح" || print_warning "المنفذ $VNC_PORT غير متاح"
    elif command -v ss >/dev/null 2>&1; then
        ss -tlnp | grep :$VNC_PORT && print_success "المنفذ $VNC_PORT متاح" || print_warning "المنفذ $VNC_PORT غير متاح"
    fi
}

# عرض معلومات الاتصال
show_connection_info() {
    echo
    echo "======================================"
    echo "  معلومات الاتصال بسطح المكتب VNC"
    echo "======================================"
    echo
    
    # الحصول على عنوان IP
    if command -v hostname >/dev/null 2>&1; then
        IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
    fi
    
    if [[ -z "$IP" ]]; then
        IP="localhost"
    fi
    
    echo "🖥️  عنوان الخادم: $IP:$VNC_PORT"
    echo "🔑  كلمة المرور: $VNC_PASSWORD"
    echo "👤  المستخدم: $(whoami)"
    echo "📺  دقة الشاشة: $SCREEN_RESOLUTION"
    echo
    echo "برامج VNC المُوصى بها:"
    echo "• VNC Viewer (RealVNC)"
    echo "• TigerVNC Viewer"
    echo "• TightVNC Viewer"
    echo
    echo "للاتصال:"
    echo "1. افتح برنامج VNC Viewer"
    echo "2. أدخل العنوان: $IP:$VNC_PORT"
    echo "3. أدخل كلمة المرور: $VNC_PASSWORD"
    echo
    print_success "سطح المكتب VNC جاهز للاستخدام!"
}

# إيقاف الخدمات
cleanup() {
    print_status "إيقاف خدمات VNC..."
    pkill -f "x11vnc" 2>/dev/null || true
    pkill -f "Xvfb" 2>/dev/null || true
    print_success "تم إيقاف الخدمات"
    exit 0
}

# معالجة إشارة الإيقاف
trap cleanup SIGINT SIGTERM

# الدالة الرئيسية
main() {
    echo "🚀 بدء تشغيل سطح مكتب VNC..."
    echo
    
    setup_vnc_dirs
    setup_vnc_password
    
    if start_xvfb; then
        start_desktop
        start_browsers
        if start_vnc_server; then
            check_ports
            show_connection_info
            
            # إبقاء السكريبت يعمل
            print_status "الضغط على Ctrl+C لإيقاف الخدمات..."
            while true; do
                sleep 10
            done
        else
            print_error "فشل في بدء خادم VNC"
            cleanup
        fi
    else
        print_error "فشل في بدء خادم العرض الافتراضي"
        exit 1
    fi
}

# تشغيل الدالة الرئيسية
main "$@"