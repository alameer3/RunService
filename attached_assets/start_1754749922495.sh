#!/bin/bash

echo "==== Application Startup at $(date) ===="

# ✅ التأكد من وجود مجلد X11 الوهمي لتفادي خطأ euid != 0
echo "📁 [1/12] إنشاء /tmp/.X11-unix ..."
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix 2>/dev/null || true

# ✅ التأكد من وجود أمر nc (netcat) لتجنب فشل التحقق من noVNC
echo "🛠️ [2/12] التأكد من وجود أمر nc ..."
command -v nc >/dev/null 2>&1 || alias nc=netcat

# 🖥️ تشغيل الشاشة الوهمية
echo "🖥️ [3/12] تشغيل Xvfb ..."
Xvfb :1 -screen 0 1024x768x16 &
export DISPLAY=:1
sleep 2

# ⚙️ تشغيل سطح المكتب LXDE
echo "🧠 [4/12] تشغيل LXDE ..."
startlxde > /tmp/lxde.log 2>&1 &
sleep 2

# 🌐 [4.5/12] تشغيل Chromium
echo "🌐 [4.5/12] تشغيل Chromium ..."
# البحث عن الأمر chromium أو chromium-browser
if command -v chromium >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium-browser"
else
    echo "❌ لم يتم العثور على أمر Chromium!"
    CHROMIUM_CMD=""
fi

if [[ -n "$CHROMIUM_CMD" ]]; then
    $CHROMIUM_CMD --no-sandbox --disable-gpu > /tmp/chromium.log 2>&1 &
    sleep 5
    if pgrep -x "$CHROMIUM_CMD" > /dev/null; then
        echo "✅ Chromium يعمل."
    else
        echo "❌ Chromium لم يعمل! عرض السجل:"
        cat /tmp/chromium.log
    fi
fi

# 🖥️ [4.6/12] تشغيل تطبيقات مرئية داخل سطح المكتب
echo "📦 [4.6/12] تشغيل lxterminal داخل الجلسة ..."
lxterminal > /tmp/lxterminal.log 2>&1 &
sleep 1

# 🔐 تشغيل x11vnc
echo "🔐 [5/12] تشغيل x11vnc ..."
x11vnc -display :1 -passwd 123456 -forever -shared > /tmp/x11vnc.log 2>&1 &
sleep 2

# 🌐 تشغيل websockify (جسر VNC إلى WebSocket)
echo "🌐 [6/12] تشغيل websockify ..."
/opt/noVNC/utils/websockify/run --web /opt/noVNC --wrap-mode=ignore 6080 0.0.0.0:5900 > /tmp/novnc.log 2>&1 &
sleep 2

# 🌍 تشغيل خادم HTTP على المنفذ 8080 (اختياري/احتياطي فقط)
echo "🌍 [7/12] تشغيل خادم HTTP على المنفذ 8080 ..."
cd /opt/noVNC && python3 -m http.server 8080 > /tmp/http.log 2>&1 &
sleep 2

# ✅ التحقق من تشغيل noVNC (websockify)
echo "🧪 [8/12] التحقق من تشغيل noVNC على المنفذ 6080 ..."
if nc -z localhost 6080; then
    echo "✅ noVNC يعمل على المنفذ 6080"
else
    echo "❌ noVNC لا يعمل! عرض السجل:"
    cat /tmp/novnc.log
    echo "--- سجل x11vnc ---"
    cat /tmp/x11vnc.log
    exit 1
fi

# ☁️ تشغيل cloudflared على منفذ 6080 لتوفير WebSocket
echo "☁️ [9/12] تشغيل cloudflared ..."
cloudflared tunnel --url http://localhost:6080 --no-autoupdate --metrics localhost:0 > /tmp/cloudflared.log 2>&1 &
sleep 10

# 🌐 طباعة رابط Cloudflare
echo "🔗 [10/12] استخراج رابط Cloudflare ..."
CLOUDFLARE_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' /tmp/cloudflared.log | head -n 1)

if [[ -n "$CLOUDFLARE_URL" ]]; then
    echo "📡 رابط سطح المكتب عبر Cloudflare:"
    echo "$CLOUDFLARE_URL"
    echo ""
    echo "🖥️ رابط vnc.html الجاهز (انسخه وافتحه في المتصفح):"
    echo "$CLOUDFLARE_URL/vnc.html?host=$(echo $CLOUDFLARE_URL | sed 's|https://||')&port=443&encrypt=1"
else
    echo "❌ لم يتم العثور على الرابط"
fi

# 🔁 إبقاء الحاوية تعمل
echo "🔁 [11/12] إبقاء الحاوية تعمل ..."
tail -f /dev/null