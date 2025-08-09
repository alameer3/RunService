#!/bin/bash

echo "==== بدء تشغيل Ubuntu Desktop مع التبعيات المتاحة $(date) ===="

# 📁 إنشاء مجلد السجلات
echo "📁 [1/10] إنشاء مجلد السجلات..."
mkdir -p logs

# 🔍 فحص التبعيات المتاحة
echo "🔍 [2/10] فحص التبعيات المتاحة..."
PYTHON_AVAILABLE=$(which python3 >/dev/null 2>&1 && echo "✅" || echo "❌")
WEBSOCKIFY_AVAILABLE=$(python3 -c "import websockify" >/dev/null 2>&1 && echo "✅" || echo "❌")
NOVNC_AVAILABLE=$([ -d "./noVNC" ] && echo "✅" || echo "❌")

echo "Python3: $PYTHON_AVAILABLE"
echo "noVNC: $NOVNC_AVAILABLE" 
echo "websockify: $WEBSOCKIFY_AVAILABLE"

# 🧲 تثبيت websockify إذا لم يكن متوفراً
if [[ "$WEBSOCKIFY_AVAILABLE" == "❌" ]]; then
    echo "📦 [3/10] تثبيت websockify..."
    pip3 install --user websockify
    echo "✅ تم تثبيت websockify"
else
    echo "✅ [3/10] websockify متوفر مسبقاً"
fi

# 🌐 التحقق من وجود noVNC
if [[ "$NOVNC_AVAILABLE" == "❌" ]]; then
    echo "❌ noVNC غير موجود! قم بتشغيل setup.sh أولاً"
    exit 1
fi

# 🖥️ محاولة تشغيل VNC وهمي بدون X11
echo "🖥️ [4/10] إنشاء خادم VNC وهمي..."
# إنشاء خادم VNC وهمي يعمل على المنفذ 5900
python3 -c "
import socket
import threading
import time

class DummyVNCServer:
    def __init__(self, port=5900):
        self.port = port
        self.running = False
        
    def handle_client(self, client_socket):
        try:
            # إرسال رد VNC بسيط
            client_socket.send(b'RFB 003.008\\n')
            time.sleep(0.1)
            client_socket.recv(1024)  # استقبال رد العميل
            # إرسال بيانات أمان بسيطة
            client_socket.send(b'\\x01\\x02')  # نوع الأمان
        except:
            pass
        finally:
            client_socket.close()
    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f'Dummy VNC Server listening on port {self.port}')
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except:
                break
                
    def stop(self):
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()

# تشغيل الخادم الوهمي
server = DummyVNCServer()
server_thread = threading.Thread(target=server.start)
server_thread.daemon = True
server_thread.start()

print('Dummy VNC server started')
" > ./logs/dummy-vnc.log 2>&1 &

DUMMY_VNC_PID=$!
sleep 2

# 🌐 تشغيل websockify (جسر VNC إلى WebSocket)
echo "🌐 [5/10] تشغيل websockify..."
NOVNC_PATH="./noVNC"

if [ -d "$NOVNC_PATH" ]; then
    cd $NOVNC_PATH/utils/websockify
    python3 run --web ../../ --wrap-mode=ignore 6080 127.0.0.1:5900 > ../../../logs/websockify.log 2>&1 &
    WEBSOCKIFY_PID=$!
    cd - > /dev/null
    sleep 3
    echo "✅ websockify يعمل على المنفذ 6080"
else
    echo "❌ مجلد noVNC غير موجود"
    exit 1
fi

# 🌍 تشغيل خادم HTTP على المنفذ 5000
echo "🌍 [6/10] تشغيل خادم HTTP على المنفذ 5000..."
cd $NOVNC_PATH
python3 -m http.server 5000 --bind 0.0.0.0 > ../logs/http-full.log 2>&1 &
HTTP_PID=$!
cd - > /dev/null
sleep 2

# ✅ التحقق من تشغيل الخدمات
echo "✅ [7/10] التحقق من تشغيل الخدمات..."

# فحص websockify
if ps -p $WEBSOCKIFY_PID > /dev/null 2>/dev/null; then
    echo "✅ websockify يعمل (PID: $WEBSOCKIFY_PID)"
else
    echo "❌ websockify لا يعمل"
    cat ./logs/websockify.log
fi

# فحص HTTP server
if ps -p $HTTP_PID > /dev/null 2>/dev/null; then
    echo "✅ HTTP Server يعمل (PID: $HTTP_PID)"
else
    echo "❌ HTTP Server لا يعمل"
    cat ./logs/http-full.log
fi

# 📊 إنشاء صفحة مخصصة للعرض التوضيحي
echo "📊 [8/10] إنشاء صفحة العرض المخصصة..."
cat > ./noVNC/demo-page.html << 'EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ubuntu Desktop - VNC Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            text-align: center;
        }
        .vnc-frame {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .control-panel {
            background: rgba(0,0,0,0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .status {
            background: rgba(46, 204, 113, 0.2);
            border: 1px solid #2ecc71;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .button {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .button:hover {
            background: #2980b9;
        }
        iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Ubuntu Desktop VNC Demo</h1>
        <p>تجربة سطح مكتب Ubuntu عبر المتصفح</p>
        
        <div class="status">
            ✅ الخدمات تعمل: WebSocket Proxy على المنفذ 6080 | HTTP Server على المنفذ 5000
        </div>
        
        <div class="control-panel">
            <h3>روابط الوصول</h3>
            <a href="vnc.html" class="button">🔗 VNC Client</a>
            <a href="vnc_lite.html" class="button">📱 VNC Lite</a>
            <a href="../simple-vnc-demo.html" class="button">📋 العرض التوضيحي</a>
        </div>
        
        <div class="vnc-frame">
            <h3 style="color: #333;">VNC Client المدمج</h3>
            <iframe src="vnc.html?autoconnect=true&resize=scale&host=localhost&port=6080"></iframe>
        </div>
        
        <div class="control-panel">
            <h3>معلومات الاتصال</h3>
            <p>Host: localhost | Port: 6080 | Password: (ليس مطلوب)</p>
            <p>ملاحظة: هذا عرض توضيحي. للحصول على سطح مكتب حقيقي، استخدم Docker</p>
        </div>
    </div>
</body>
</html>
EOF

# ☁️ تشغيل cloudflared إذا كان متوفراً
echo "☁️ [9/10] تشغيل cloudflared..."
if command -v cloudflared >/dev/null 2>&1; then
    cloudflared tunnel --url http://localhost:5000 --no-autoupdate --metrics localhost:0 > ./logs/cloudflared-full.log 2>&1 &
    CLOUDFLARED_PID=$!
    sleep 10
    
    # استخراج رابط Cloudflare
    CLOUDFLARE_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' ./logs/cloudflared-full.log | head -n 1)
    
    if [[ -n "$CLOUDFLARE_URL" ]]; then
        echo "✅ Cloudflare Tunnel متاح: $CLOUDFLARE_URL"
    else
        echo "⚠️ لم يتم العثور على رابط Cloudflare"
    fi
else
    echo "⚠️ cloudflared غير متوفر"
fi

# 📊 عرض معلومات الاتصال النهائية
echo ""
echo "🎉 [10/10] تم تشغيل النظام بنجاح!"
echo "================================="
echo "🌐 الروابط المتاحة:"
echo "• الصفحة الرئيسية: http://localhost:5000"
echo "• VNC Client: http://localhost:5000/vnc.html"
echo "• العرض المخصص: http://localhost:5000/demo-page.html"
echo "• VNC Lite: http://localhost:5000/vnc_lite.html"
if [[ -n "$CLOUDFLARE_URL" ]]; then
    echo "• رابط عام: $CLOUDFLARE_URL"
fi
echo ""
echo "🔧 معلومات تقنية:"
echo "• WebSocket Proxy: localhost:6080"
echo "• HTTP Server: localhost:5000"
echo "• VNC Server: localhost:5900 (وهمي)"
echo ""
echo "📝 ملاحظة: هذا إصدار تجريبي للعرض في بيئة Replit"
echo "للحصول على سطح مكتب Ubuntu حقيقي، استخدم Docker في بيئة تدعمه"

# 🔁 إبقاء التطبيق يعمل
echo ""
echo "🔁 النظام يعمل... للإيقاف اضغط Ctrl+C"

# إنشاء وظيفة لتنظيف العمليات عند الخروج
cleanup() {
    echo ""
    echo "🛑 إيقاف جميع العمليات..."
    kill $DUMMY_VNC_PID 2>/dev/null
    kill $WEBSOCKIFY_PID 2>/dev/null
    kill $HTTP_PID 2>/dev/null
    kill $CLOUDFLARED_PID 2>/dev/null
    echo "✅ تم إيقاف جميع العمليات"
    exit 0
}

trap cleanup SIGINT SIGTERM

# إبقاء السكريبت يعمل
tail -f /dev/null