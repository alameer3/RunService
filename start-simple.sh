#!/bin/bash

echo "==== بدء تشغيل عرض Ubuntu Desktop التوضيحي $(date) ===="

# 📁 إنشاء مجلد السجلات
echo "📁 [1/4] إنشاء مجلد السجلات..."
mkdir -p logs

# 🌐 إنشاء صفحة ترحيب تفاعلية
echo "🌐 [2/4] إنشاء الصفحة التفاعلية..."
if [ ! -f "simple-vnc-demo.html" ]; then
    echo "❌ ملف العرض التوضيحي غير موجود!"
    exit 1
fi

# 🐍 تشغيل خادم HTTP للعرض التوضيحي على المنفذ 5000
echo "🐍 [3/4] تشغيل خادم HTTP للعرض التوضيحي على المنفذ 5000..."
python3 -m http.server 5000 --bind 0.0.0.0 > ./logs/http-demo.log 2>&1 &
HTTP_PID=$!
sleep 2

# ✅ التحقق من تشغيل خادم HTTP
echo "✅ [4/4] التحقق من تشغيل الخادم..."
if ps -p $HTTP_PID > /dev/null; then
    echo "✅ خادم العرض التوضيحي يعمل على المنفذ 5000"
else
    echo "❌ فشل في تشغيل خادم HTTP"
    cat ./logs/http-demo.log
    exit 1
fi

# 📊 عرض معلومات الاتصال
echo ""
echo "🌐 معلومات الاتصال:"
echo "================================="
echo "🎯 رابط العرض التوضيحي: http://localhost:5000/simple-vnc-demo.html"
echo "📋 صفحة المشروع: http://localhost:5000"
echo ""
echo "📖 ملاحظات هامة:"
echo "• هذا عرض توضيحي تفاعلي لمشروع Ubuntu Desktop"
echo "• للحصول على سطح مكتب حقيقي، تحتاج لتشغيل Docker"
echo "• تحتوي الصفحة على تعليمات التشغيل الكاملة"
echo ""
echo "🚀 للتشغيل الفعلي:"
echo "  docker build -t ubuntu-desktop ."
echo "  docker run -p 5000:5000 -p 6080:6080 ubuntu-desktop"

# 🔁 إبقاء التطبيق يعمل
echo ""
echo "🔁 الخادم يعمل... للإيقاف اضغط Ctrl+C"

# إنشاء وظيفة لتنظيف العمليات عند الخروج
cleanup() {
    echo ""
    echo "🛑 إيقاف خادم HTTP..."
    kill $HTTP_PID 2>/dev/null
    echo "✅ تم إيقاف جميع العمليات"
    exit 0
}

trap cleanup SIGINT SIGTERM

# إبقاء السكريبت يعمل
tail -f /dev/null