#!/bin/bash

# سكريبت التثبيت التلقائي لبيئة سطح مكتب VNC
# يعمل على Ubuntu/Debian مع ذاكرة 1 جيجا رام

set -e  # إيقاف السكريبت عند أي خطأ

# الألوان للعرض
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دالة لطباعة الرسائل الملونة
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
    إعداد بيئة سطح مكتب VNC
=====================================${NC}"
}

# التحقق من صلاحيات الجذر
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "يتم تشغيل السكريبت كمستخدم root"
    else
        print_error "يجب تشغيل السكريبت بصلاحيات sudo"
        exit 1
    fi
}

# التحقق من نوع نظام التشغيل
check_os() {
    if [[ -f /etc/debian_version ]]; then
        OS="debian"
        print_success "تم اكتشاف نظام Debian/Ubuntu"
    elif [[ -f /etc/redhat-release ]]; then
        OS="redhat"
        print_success "تم اكتشاف نظام RedHat/CentOS"
    else
        print_error "نظام التشغيل غير مدعوم"
        exit 1
    fi
}

# تحديث النظام
update_system() {
    print_status "تحديث قوائم الحزم..."
    if [[ "$OS" == "debian" ]]; then
        export DEBIAN_FRONTEND=noninteractive
        apt update
        apt upgrade -y
    elif [[ "$OS" == "redhat" ]]; then
        yum update -y
    fi
    print_success "تم تحديث النظام"
}

# تثبيت الحزم الأساسية
install_base_packages() {
    print_status "تثبيت الحزم الأساسية..."
    
    if [[ "$OS" == "debian" ]]; then
        apt install -y \
            curl \
            wget \
            git \
            htop \
            nano \
            unzip \
            software-properties-common \
            ca-certificates \
            gnupg \
            lsb-release
    elif [[ "$OS" == "redhat" ]]; then
        yum install -y \
            curl \
            wget \
            git \
            htop \
            nano \
            unzip \
            ca-certificates
    fi
    
    print_success "تم تثبيت الحزم الأساسية"
}

# تثبيت بيئة سطح المكتب LXDE
install_desktop() {
    print_status "تثبيت بيئة سطح مكتب LXDE..."
    
    if [[ "$OS" == "debian" ]]; then
        apt install -y \
            lxde-core \
            lxterminal \
            lxappearance \
            lxsession-logout \
            xorg \
            xserver-xorg-core \
            xfonts-base \
            fonts-liberation \
            fonts-dejavu-core \
            dbus-x11
    elif [[ "$OS" == "redhat" ]]; then
        yum groupinstall -y "LXDE Desktop"
        yum install -y \
            xorg-x11-server-Xorg \
            xorg-x11-xauth \
            xorg-x11-fonts-base \
            dejavu-fonts-common
    fi
    
    print_success "تم تثبيت بيئة سطح المكتب"
}

# تثبيت VNC Server
install_vnc() {
    print_status "تثبيت VNC Server..."
    
    if [[ "$OS" == "debian" ]]; then
        apt install -y \
            x11vnc \
            xvfb \
            net-tools
    elif [[ "$OS" == "redhat" ]]; then
        yum install -y \
            tigervnc-server \
            xorg-x11-server-Xvfb \
            net-tools
    fi
    
    print_success "تم تثبيت VNC Server"
}

# تثبيت المتصفحات
install_browsers() {
    print_status "تثبيت المتصفحات..."
    
    if [[ "$OS" == "debian" ]]; then
        # تثبيت Firefox ESR
        apt install -y firefox-esr
        
        # تثبيت Chromium
        apt install -y chromium-browser || apt install -y chromium
        
    elif [[ "$OS" == "redhat" ]]; then
        # تثبيت Firefox
        yum install -y firefox
        
        # تثبيت Chromium
        yum install -y chromium
    fi
    
    print_success "تم تثبيت المتصفحات"
}

# إعداد مستخدم VNC
setup_vnc_user() {
    print_status "إعداد مستخدم VNC..."
    
    VNC_USER="vncuser"
    VNC_PASS="vnc123456"
    
    # إنشاء مستخدم VNC إذا لم يكن موجوداً
    if ! id "$VNC_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$VNC_USER"
        echo "$VNC_USER:$VNC_PASS" | chpasswd
        print_success "تم إنشاء مستخدم VNC: $VNC_USER"
    fi
    
    # إعداد مجلد VNC
    sudo -u "$VNC_USER" mkdir -p "/home/$VNC_USER/.vnc"
    
    # إعداد كلمة مرور VNC
    echo "$VNC_PASS" | sudo -u "$VNC_USER" x11vnc -storepasswd "/home/$VNC_USER/.vnc/passwd" 2>/dev/null || true
    
    # إعداد ملف xstartup
    cat > "/home/$VNC_USER/.vnc/xstartup" << 'EOF'
#!/bin/bash
export USER="vncuser"
export HOME="/home/vncuser"

# بدء خدمة dbus
eval `dbus-launch --sh-syntax`

# تشغيل بيئة سطح المكتب LXDE
/usr/bin/lxsession -s LXDE &

# تشغيل Firefox تلقائياً
sleep 5
firefox-esr > /dev/null 2>&1 &

# إبقاء النافذة مفتوحة
exec /usr/bin/lxterminal
EOF
    
    chmod +x "/home/$VNC_USER/.vnc/xstartup"
    chown -R "$VNC_USER:$VNC_USER" "/home/$VNC_USER/.vnc"
    
    print_success "تم إعداد مستخدم VNC"
}

# إعداد خدمة systemd
setup_systemd() {
    print_status "إعداد خدمة systemd للتشغيل التلقائي..."
    
    cat > "/etc/systemd/system/vncserver.service" << 'EOF'
[Unit]
Description=Remote desktop service (VNC)
After=syslog.target network.target

[Service]
Type=simple
User=vncuser
PAMName=login
PIDFile=/home/vncuser/.vnc/%H:1.pid
ExecStartPre=/bin/bash -c '/usr/bin/x11vnc -kill :1 > /dev/null 2>&1 || :'
ExecStart=/usr/bin/x11vnc -auth guess -forever -loop -noxdamage -repeat -rfbauth /home/vncuser/.vnc/passwd -rfbport 5901 -shared -display :1
ExecStop=/usr/bin/x11vnc -kill :1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    cat > "/etc/systemd/system/xvfb.service" << 'EOF'
[Unit]
Description=X Virtual Frame Buffer Service
After=syslog.target network.target

[Service]
Type=simple
User=vncuser
ExecStart=/usr/bin/Xvfb :1 -screen 0 1024x768x24
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # تفعيل الخدمات
    systemctl daemon-reload
    systemctl enable xvfb.service
    systemctl enable vncserver.service
    
    print_success "تم إعداد خدمات systemd"
}

# بدء الخدمات
start_services() {
    print_status "بدء تشغيل الخدمات..."
    
    systemctl start xvfb.service
    sleep 2
    systemctl start vncserver.service
    
    print_success "تم بدء تشغيل الخدمات"
}

# عرض المعلومات النهائية
show_info() {
    print_header
    echo -e "${GREEN}تم إعداد بيئة سطح مكتب VNC بنجاح!${NC}"
    echo
    echo "معلومات الاتصال:"
    echo "- عنوان الخادم: $(hostname -I | awk '{print $1}'):5901"
    echo "- كلمة المرور: vnc123456"
    echo "- المستخدم: vncuser"
    echo
    echo "برامج VNC المدعومة:"
    echo "- VNC Viewer (RealVNC)"
    echo "- TigerVNC Viewer"
    echo "- TightVNC Viewer"
    echo
    echo "الأوامر المفيدة:"
    echo "- فحص حالة الخدمة: systemctl status vncserver"
    echo "- إعادة تشغيل الخدمة: sudo systemctl restart vncserver"
    echo "- إيقاف الخدمة: sudo systemctl stop vncserver"
    echo
    print_success "النظام جاهز للاستخدام!"
}

# الدالة الرئيسية
main() {
    print_header
    check_root
    check_os
    update_system
    install_base_packages
    install_desktop
    install_vnc
    install_browsers
    setup_vnc_user
    setup_systemd
    start_services
    show_info
}

# تشغيل السكريبت
main "$@"