#!/bin/bash

echo "🚀 إعداد مشروع Ubuntu Desktop عبر المتصفح"
echo "============================================"

# التحقق من الصلاحيات
if [[ $EUID -eq 0 ]]; then
   echo "⚠️ تحذير: يتم تشغيل هذا السكريبت كـ root"
   echo "للأمان، يُفضل تشغيله كمستخدم عادي"
fi

# إنشاء مجلد السجلات
echo "📁 [1/8] إنشاء مجلد السجلات..."
mkdir -p logs

# تحديث قائمة الحزم
echo "📦 [2/8] تحديث قائمة الحزم..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update
elif command -v yum >/dev/null 2>&1; then
    sudo yum update
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy
else
    echo "❌ مدير الحزم غير مدعوم!"
    exit 1
fi

# تثبيت الحزم الأساسية
echo "📦 [3/8] تثبيت الحزم الأساسية..."
if command -v apt >/dev/null 2>&1; then
    sudo apt install -y \
        lxde \
        x11vnc \
        xvfb \
        git \
        python3 \
        python3-pip \
        curl \
        wget \
        net-tools \
        netcat \
        chromium-browser \
        lxterminal \
        || sudo apt install -y \
        lxde \
        x11vnc \
        xvfb \
        git \
        python3 \
        python3-pip \
        curl \
        wget \
        net-tools \
        netcat-openbsd \
        chromium \
        lxterminal
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y \
        @lxde-desktop \
        x11vnc \
        xorg-x11-server-Xvfb \
        git \
        python3 \
        python3-pip \
        curl \
        wget \
        net-tools \
        nmap-ncat \
        chromium \
        lxterminal
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm \
        lxde \
        x11vnc \
        xorg-server-xvfb \
        git \
        python \
        python-pip \
        curl \
        wget \
        net-tools \
        gnu-netcat \
        chromium \
        lxterminal
fi

# إعداد كلمة مرور VNC
echo "🔐 [4/8] إعداد كلمة مرور VNC..."
mkdir -p ~/.vnc
echo "123456" | x11vnc -storepasswd /dev/stdin ~/.vnc/passwd
cp ~/.vnc/passwd ./config/vnc-passwd 2>/dev/null || true

# تحميل noVNC
echo "🌐 [5/8] تحميل noVNC..."
if [ ! -d "./noVNC" ]; then
    git clone --branch v1.2.0 https://github.com/novnc/noVNC.git ./noVNC
    git clone https://github.com/novnc/websockify ./noVNC/utils/websockify
    chmod +x ./noVNC/utils/launch.sh
    echo "✅ تم تحميل noVNC بنجاح"
else
    echo "✅ noVNC موجود مسبقاً"
fi

# تحميل cloudflared
echo "☁️ [6/8] تحميل cloudflared..."
if ! command -v cloudflared >/dev/null 2>&1; then
    if [[ $(uname -m) == "x86_64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
    elif [[ $(uname -m) == "aarch64" ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -O cloudflared
    else
        echo "⚠️ معمارية غير مدعومة للـ cloudflared"
    fi
    
    if [ -f "cloudflared" ]; then
        chmod +x cloudflared
        sudo mv cloudflared /usr/local/bin/
        echo "✅ تم تثبيت cloudflared"
    fi
else
    echo "✅ cloudflared مثبت مسبقاً"
fi

# إعداد LXDE autostart
echo "⚙️ [7/8] إعداد LXDE autostart..."
mkdir -p ~/.config/lxsession/LXDE
if [ -f "./config/lxde-autostart" ]; then
    cp ./config/lxde-autostart ~/.config/lxsession/LXDE/autostart
else
    echo "@chromium-browser --no-sandbox --disable-gpu" > ~/.config/lxsession/LXDE/autostart
fi

# إعداد الصلاحيات
echo "🔧 [8/8] إعداد الصلاحيات..."
chmod +x start.sh
chmod +x install_deps.sh 2>/dev/null || true
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix 2>/dev/null || true

echo ""
echo "🎉 تم الإعداد بنجاح!"
echo "================================"
echo "لتشغيل المشروع، قم بتشغيل:"
echo "./start.sh"
echo ""
echo "أو لتثبيت المتطلبات الإضافية:"
echo "./install_deps.sh"
