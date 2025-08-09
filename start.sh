#!/bin/bash

echo "==== بدء تشغيل Ubuntu Desktop عبر المتصفح $(date) ===="

# 🔎 فحص التبعيات المطلوبة
echo "🔍 [1/15] فحص التبعيات المطلوبة..."
MISSING_DEPS=""

if ! command -v docker >/dev/null 2>&1; then
    MISSING_DEPS="$MISSING_DEPS docker"
fi

if [[ -n "$MISSING_DEPS" ]]; then
    echo "❌ التبعيات المفقودة: $MISSING_DEPS"
    echo "🐳 [2/15] استخدام Docker لتشغيل المشروع..."
    
    if ! command -v docker >/dev/null 2>&1; then
        echo "⚠️ Docker غير مثبت. سيتم استخدام الحاوية المبنية مسبقاً..."
        echo "🚀 يمكنك تشغيل المشروع باستخدام:"
        echo "   docker build -t ubuntu-desktop ."
        echo "   docker run -p 5000:5000 -p 6080:6080 ubuntu-desktop"
        echo ""
        echo "أو استخدام حاوية جاهزة من الملفات المرفقة."
        exit 1
    fi
    
    echo "🔨 [3/15] بناء حاوية Docker..."
    docker build -t ubuntu-desktop-vnc .
    
    echo "🚀 [4/15] تشغيل الحاوية..."
    docker run -d -p 5000:5000 -p 6080:6080 --name ubuntu-desktop ubuntu-desktop-vnc
    
    echo "✅ [5/15] تم تشغيل الحاوية بنجاح!"
    echo "🌐 يمكنك الوصول عبر: http://localhost:5000/vnc.html"
    echo "🔐 كلمة المرور: 123456"
    exit 0
fi

# ✅ التأكد من وجود مجلد X11 الوهمي لتفادي خطأ euid != 0
echo "📁 [2/15] إنشاء /tmp/.X11-unix ..."
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix 2>/dev/null || true

# ✅ التأكد من وجود أمر nc (netcat) لتجنب فشل التحقق من noVNC
echo "🛠️ [3/15] التأكد من وجود أمر nc ..."
if command -v nc >/dev/null 2>&1; then
    NC_CMD="nc"
elif command -v netcat >/dev/null 2>&1; then
    NC_CMD="netcat"
else
    echo "⚠️ netcat غير متوفر، سيتم تجاهل فحص المنافذ"
    NC_CMD=""
fi

# 🖥️ تشغيل الشاشة الوهمية
echo "🖥️ [4/15] تشغيل Xvfb ..."
if command -v Xvfb >/dev/null 2>&1; then
    Xvfb :1 -screen 0 1024x768x16 > ./logs/xvfb.log 2>&1 &
    export DISPLAY=:1
    sleep 2
    echo "✅ Xvfb يعمل على :1"
else
    echo "❌ Xvfb غير متوفر. يرجى تشغيل المشروع باستخدام Docker"
    exit 1
fi

# ⚙️ تشغيل سطح المكتب LXDE
echo "🧠 [5/15] تشغيل LXDE ..."
if command -v startlxde >/dev/null 2>&1; then
    startlxde > ./logs/lxde.log 2>&1 &
    sleep 3
    echo "✅ LXDE يعمل"
else
    echo "❌ LXDE غير متوفر. يرجى تشغيل المشروع باستخدام Docker"
    exit 1
fi

# 🌐 [6/15] تشغيل Chromium
echo "🌐 [6/15] تشغيل Chromium ..."
# البحث عن الأمر chromium أو chromium-browser
if command -v chromium >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium-browser"
elif command -v google-chrome >/dev/null 2>&1; then
    CHROMIUM_CMD="google-chrome"
else
    echo "❌ لم يتم العثور على أمر Chromium!"
    CHROMIUM_CMD=""
fi

if [[ -n "$CHROMIUM_CMD" ]]; then
    $CHROMIUM_CMD --no-sandbox --disable-gpu > ./logs/chromium.log 2>&1 &
    sleep 5
    if pgrep -x "$CHROMIUM_CMD" > /dev/null; then
        echo "✅ Chromium يعمل."
    else
        echo "❌ Chromium لم يعمل! عرض السجل:"
        cat ./logs/chromium.log
    fi
fi

# 🖥️ [7/15] تشغيل تطبيقات مرئية داخل سطح المكتب
echo "📦 [7/15] تشغيل lxterminal داخل الجلسة ..."
lxterminal > ./logs/lxterminal.log 2>&1 &
sleep 1

# 🔐 تشغيل x11vnc
echo "🔐 [8/15] تشغيل x11vnc ..."
if command -v x11vnc >/dev/null 2>&1; then
    x11vnc -display :1 -passwd 123456 -forever -shared > ./logs/x11vnc.log 2>&1 &
    sleep 2
    echo "✅ x11vnc يعمل"
else
    echo "❌ x11vnc غير متوفر. يرجى تشغيل المشروع باستخدام Docker"
    exit 1
fi

# 🌐 تشغيل websockify (جسر VNC إلى WebSocket)
echo "🌐 [9/15] تشغيل websockify ..."
# Check if noVNC is installed, if not use the local installation
if [ -d "/opt/noVNC" ]; then
    NOVNC_PATH="/opt/noVNC"
elif [ -d "./noVNC" ]; then
    NOVNC_PATH="./noVNC"
else
    echo "❌ noVNC غير موجود! قم بتشغيل setup.sh أولاً"
    exit 1
fi

$NOVNC_PATH/utils/websockify/run --web $NOVNC_PATH --wrap-mode=ignore 6080 0.0.0.0:5900 > ./logs/novnc.log 2>&1 &
sleep 2

# 🌍 تشغيل خادم HTTP على المنفذ 5000 (المطلوب للواجهة الأمامية)
echo "🌍 [10/15] تشغيل خادم HTTP على المنفذ 5000 ..."
cd $NOVNC_PATH && python3 -m http.server 5000 --bind 0.0.0.0 > ../logs/http.log 2>&1 &
cd - > /dev/null
sleep 2

# ✅ التحقق من تشغيل noVNC (websockify)
echo "🧪 [11/15] التحقق من تشغيل noVNC على المنفذ 6080 ..."
if [[ -n "$NC_CMD" ]] && $NC_CMD -z localhost 6080; then
    echo "✅ noVNC يعمل على المنفذ 6080"
else
    echo "❌ noVNC لا يعمل! عرض السجل:"
    cat ./logs/novnc.log
    echo "--- سجل x11vnc ---"
    cat ./logs/x11vnc.log
    exit 1
fi

# ☁️ تشغيل cloudflared على منفذ 6080 لتوفير WebSocket
echo "☁️ [12/15] تشغيل cloudflared ..."
if command -v cloudflared >/dev/null 2>&1; then
    cloudflared tunnel --url http://localhost:6080 --no-autoupdate --metrics localhost:0 > ./logs/cloudflared.log 2>&1 &
    sleep 10
    
    # 🌐 طباعة رابط Cloudflare
    echo "🔗 [13/15] استخراج رابط Cloudflare ..."
    CLOUDFLARE_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' ./logs/cloudflared.log | head -n 1)
    
    if [[ -n "$CLOUDFLARE_URL" ]]; then
        echo "📡 رابط سطح المكتب عبر Cloudflare:"
        echo "$CLOUDFLARE_URL"
        echo ""
        echo "🖥️ رابط vnc.html الجاهز (انسخه وافتحه في المتصفح):"
        echo "$CLOUDFLARE_URL/vnc.html?host=$(echo $CLOUDFLARE_URL | sed 's|https://||')&port=443&encrypt=1"
    else
        echo "❌ لم يتم العثور على الرابط في Cloudflare"
    fi
else
    echo "⚠️ cloudflared غير مثبت. يمكن الوصول محلياً على:"
    echo "http://localhost:5000/vnc.html"
fi

# 📊 عرض معلومات الاتصال
echo ""
echo "🌐 [14/15] معلومات الاتصال:"
echo "- المنفذ المحلي للـ HTTP Server: http://0.0.0.0:5000"
echo "- المنفذ المحلي للـ noVNC WebSocket: ws://0.0.0.0:6080"
echo "- رابط VNC المباشر: http://localhost:5000/vnc.html"
echo "- كلمة مرور VNC: 123456"

# 🔁 إبقاء التطبيق يعمل
echo "🔁 [15/15] إبقاء التطبيق يعمل ..."
echo "للإيقاف اضغط Ctrl+C"

# إنشاء وظيفة لتنظيف العمليات عند الخروج
cleanup() {
    echo ""
    echo "🛑 إيقاف جميع العمليات..."
    pkill -f "Xvfb :1"
    pkill -f "startlxde"
    pkill -f "x11vnc"
    pkill -f "websockify"
    pkill -f "python3 -m http.server"
    pkill -f "cloudflared"
    echo "✅ تم إيقاف جميع العمليات"
    exit 0
}

trap cleanup SIGINT SIGTERM

# إبقاء السكريبت يعمل
tail -f /dev/null
