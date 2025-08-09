#!/bin/bash

# سكريبت إدارة خدمات VNC
# للتحكم في بدء وإيقاف وإعادة تشغيل خدمات VNC

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=====================================
       إدارة خدمات VNC
=====================================${NC}"
}

# عرض حالة الخدمات
status() {
    print_header
    echo
    print_status "حالة خدمة Xvfb:"
    systemctl status xvfb.service --no-pager -l
    echo
    print_status "حالة خدمة VNC Server:"
    systemctl status vncserver.service --no-pager -l
    echo
    print_status "المنافذ المفتوحة:"
    netstat -tlnp | grep :590 || echo "لا توجد منافذ VNC مفتوحة"
    echo
    print_status "العمليات الجارية:"
    ps aux | grep -E "(vnc|Xvfb)" | grep -v grep || echo "لا توجد عمليات VNC"
}

# بدء الخدمات
start() {
    print_status "بدء تشغيل خدمات VNC..."
    
    systemctl start xvfb.service
    sleep 2
    systemctl start vncserver.service
    
    if systemctl is-active --quiet vncserver.service; then
        print_success "تم بدء خدمات VNC بنجاح"
    else
        print_error "فشل في بدء خدمات VNC"
        return 1
    fi
}

# إيقاف الخدمات
stop() {
    print_status "إيقاف خدمات VNC..."
    
    systemctl stop vncserver.service
    systemctl stop xvfb.service
    
    # إيقاف أي عمليات متبقية
    pkill -f "x11vnc"
    pkill -f "Xvfb"
    
    print_success "تم إيقاف خدمات VNC"
}

# إعادة تشغيل الخدمات
restart() {
    print_status "إعادة تشغيل خدمات VNC..."
    stop
    sleep 3
    start
}

# تفعيل التشغيل التلقائي
enable() {
    print_status "تفعيل التشغيل التلقائي لخدمات VNC..."
    systemctl enable xvfb.service
    systemctl enable vncserver.service
    print_success "تم تفعيل التشغيل التلقائي"
}

# إلغاء التشغيل التلقائي
disable() {
    print_status "إلغاء التشغيل التلقائي لخدمات VNC..."
    systemctl disable xvfb.service
    systemctl disable vncserver.service
    print_success "تم إلغاء التشغيل التلقائي"
}

# عرض السجلات
logs() {
    echo "سجلات Xvfb:"
    echo "============="
    journalctl -u xvfb.service --no-pager -l
    echo
    echo "سجلات VNC Server:"
    echo "=================="
    journalctl -u vncserver.service --no-pager -l
}

# تغيير كلمة مرور VNC
change_password() {
    print_status "تغيير كلمة مرور VNC..."
    
    read -s -p "أدخل كلمة المرور الجديدة: " new_pass
    echo
    read -s -p "أكد كلمة المرور الجديدة: " confirm_pass
    echo
    
    if [[ "$new_pass" != "$confirm_pass" ]]; then
        print_error "كلمات المرور غير متطابقة"
        return 1
    fi
    
    # تحديث كلمة مرور VNC
    echo "$new_pass" | sudo -u vncuser x11vnc -storepasswd /home/vncuser/.vnc/passwd
    
    # إعادة تشغيل الخدمة
    systemctl restart vncserver.service
    
    print_success "تم تغيير كلمة مرور VNC"
}

# عرض معلومات الاتصال
info() {
    print_header
    echo
    echo "معلومات الاتصال بـ VNC:"
    echo "======================="
    echo "- عنوان الخادم: $(hostname -I | awk '{print $1}'):5901"
    echo "- المنفذ: 5901"
    echo "- المستخدم: vncuser"
    echo
    echo "برامج VNC المدعومة:"
    echo "- VNC Viewer (RealVNC)"
    echo "- TigerVNC Viewer"
    echo "- TightVNC Viewer"
    echo "- NoVNC (متصفح ويب)"
    echo
    echo "استكشاف الأخطاء:"
    echo "================"
    echo "- للتحقق من حالة الخدمات: $0 status"
    echo "- لعرض السجلات: $0 logs"
    echo "- لإعادة التشغيل: $0 restart"
}

# عرض المساعدة
help() {
    print_header
    echo
    echo "الأوامر المتاحة:"
    echo "================="
    echo "  start      - بدء تشغيل خدمات VNC"
    echo "  stop       - إيقاف خدمات VNC"
    echo "  restart    - إعادة تشغيل خدمات VNC"
    echo "  status     - عرض حالة الخدمات"
    echo "  enable     - تفعيل التشغيل التلقائي"
    echo "  disable    - إلغاء التشغيل التلقائي"
    echo "  logs       - عرض سجلات الخدمات"
    echo "  password   - تغيير كلمة مرور VNC"
    echo "  info       - عرض معلومات الاتصال"
    echo "  help       - عرض هذه المساعدة"
    echo
    echo "مثال: $0 start"
}

# الدالة الرئيسية
main() {
    case "$1" in
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        enable)
            enable
            ;;
        disable)
            disable
            ;;
        logs)
            logs
            ;;
        password)
            change_password
            ;;
        info)
            info
            ;;
        help|--help|-h)
            help
            ;;
        *)
            print_error "أمر غير صحيح: $1"
            echo
            help
            exit 1
            ;;
    esac
}

# التحقق من وجود معاملات
if [[ $# -eq 0 ]]; then
    help
    exit 1
fi

# تشغيل الدالة الرئيسية
main "$@"