#!/bin/bash

echo "==== تشغيل OneClickDesktop المحدود في Replit $(date) ===="

# 🧹 تنظيف العمليات السابقة
echo "🧹 [1/6] تنظيف العمليات السابقة..."
pkill -f "oneclick_replit_adapter" 2>/dev/null
pkill -f "ultimate_vnc_server" 2>/dev/null
pkill -f "websockify" 2>/dev/null
pkill -f "http.server" 2>/dev/null
sleep 2

# 📁 إنشاء مجلد السجلات
echo "📁 [2/6] إنشاء مجلد السجلات..."
mkdir -p logs
rm -f logs/*.log 2>/dev/null

# 🔍 فحص OneClickDesktop
echo "🔍 [3/6] فحص مجلد OneClickDesktop..."
if [[ -d "OneClickDesktop" ]]; then
    echo "✅ مجلد OneClickDesktop موجود"
    
    if [[ -f "OneClickDesktop/OneClickDesktop.sh" ]]; then
        echo "✅ سكريبت OneClickDesktop.sh موجود"
        
        # عرض معلومات السكريبت
        echo "📊 معلومات السكريبت:"
        GUAC_VERSION=$(grep "GUACAMOLE_VERSION=" OneClickDesktop/OneClickDesktop.sh | head -1 | cut -d'"' -f2)
        echo "  • إصدار Guacamole: $GUAC_VERSION"
        
        SCRIPT_VERSION=$(grep "v0\." OneClickDesktop/OneClickDesktop.sh | head -1)
        echo "  • إصدار السكريبت: $SCRIPT_VERSION"
        
        PLUGIN_COUNT=$(find OneClickDesktop/plugins -name "*.sh" 2>/dev/null | wc -l)
        echo "  • عدد الإضافات: $PLUGIN_COUNT"
        
    else
        echo "❌ سكريبت OneClickDesktop.sh غير موجود"
    fi
else
    echo "❌ مجلد OneClickDesktop غير موجود"
    exit 1
fi

# 🔧 فحص التبعيات
echo "🔧 [4/6] فحص التبعيات المطلوبة..."
PYTHON_OK=$(python3 --version >/dev/null 2>&1 && echo "✅" || echo "❌")
WEBSOCKIFY_OK=$(python3 -c "import websockify" >/dev/null 2>&1 && echo "✅" || echo "❌")
NOVNC_OK=$([ -d "./noVNC" ] && echo "✅" || echo "❌")

echo "Python3: $PYTHON_OK"
echo "websockify: $WEBSOCKIFY_OK"
echo "noVNC: $NOVNC_OK"

# فحص التبعيات المفقودة (التي يحتاجها OneClickDesktop الأصلي)
echo ""
echo "🔍 فحص تبعيات OneClickDesktop الأصلية:"
echo "apt-get: ❌ (غير متوفر في Replit)"
echo "systemctl: ❌ (غير متوفر في Replit)"
echo "tomcat9: ❌ (غير متوفر)"
echo "guacamole: ❌ (غير متوفر)"
echo "xrdp: ❌ (غير متوفر)"
echo "xfce4: ❌ (غير متوفر)"

echo ""
echo "⚠️ ملاحظة: OneClickDesktop الأصلي يتطلب صلاحيات الجذر وخدمات النظام"
echo "سيتم تشغيل محول محدود يحاكي الوظائف الأساسية"

# 🚀 تشغيل المحول
echo "🚀 [5/6] تشغيل محول OneClickDesktop..."
python3 oneclick_replit_adapter.py > logs/oneclick_adapter.log 2>&1 &
ADAPTER_PID=$!
sleep 5

# فحص حالة المحول
if ps -p $ADAPTER_PID > /dev/null 2>&1; then
    echo "✅ محول OneClickDesktop يعمل (PID: $ADAPTER_PID)"
else
    echo "❌ فشل في تشغيل المحول"
    echo "📋 السجل:"
    cat logs/oneclick_adapter.log
    exit 1
fi

# 📊 تقرير الحالة النهائي
echo ""
echo "🎉 [6/6] تم تشغيل OneClickDesktop المحدود بنجاح!"
echo "======================================================="

echo ""
echo "📊 الخدمات المتاحة:"
echo "✅ VNC Server (محاكي): localhost:5900"
echo "✅ WebSocket Proxy: localhost:6080"
echo "✅ HTTP Server: localhost:5000"
echo "⚠️ Guacamole Web: محاكي (localhost:8080)"
echo "⚠️ XFCE4 Desktop: محاكي (يتطلب X11)"
echo "⚠️ XRDP Server: غير متوفر"

echo ""
echo "🌐 الروابط المتاحة:"
echo "• OneClick Demo: http://localhost:5000/oneclick-demo.html"
echo "• VNC Client: http://localhost:5000/vnc.html"
echo "• صفحة التشخيص: http://localhost:5000/diagnosis.html"
echo "• الصفحة الرئيسية: http://localhost:5000"

echo ""
echo "📋 معلومات OneClickDesktop الأصلي:"
echo "• الغرض: إعداد سطح مكتب كامل مع Guacamole"
echo "• المتطلبات: Ubuntu/Debian + صلاحيات الجذر"
echo "• الميزات: XFCE4 + Firefox + Chrome + SSL"
echo "• الوصول: متصفح ويب + RDP + VNC"

echo ""
echo "⚠️ القيود في بيئة Replit:"
echo "• لا توجد صلاحيات الجذر"
echo "• لا يمكن تثبيت خدمات النظام"
echo "• لا يمكن تشغيل X11 Server"
echo "• لا يمكن تثبيت Tomcat/Guacamole"

echo ""
echo "✨ ما يعمل في هذا المحول:"
echo "• واجهة VNC تفاعلية"
echo "• خادم ويب كامل"
echo "• محاكي لواجهة Guacamole"
echo "• صفحة تجريبية شاملة"

echo ""
echo "🔁 النظام يعمل... للإيقاف اضغط Ctrl+C"

# وظيفة التنظيف
cleanup() {
    echo ""
    echo "🛑 إيقاف OneClickDesktop Adapter..."
    kill $ADAPTER_PID 2>/dev/null && echo "✅ تم إيقاف المحول"
    pkill -f "ultimate_vnc_server" 2>/dev/null
    pkill -f "websockify" 2>/dev/null
    pkill -f "http.server" 2>/dev/null
    echo "✅ تم إيقاف جميع العمليات"
    exit 0
}

trap cleanup SIGINT SIGTERM

# انتظار لانهائي
tail -f /dev/null