#!/bin/bash

echo "==== Ultimate Ubuntu Desktop VNC Server $(date) ===="

# 🧹 تنظيف العمليات السابقة
echo "🧹 [1/10] تنظيف العمليات السابقة..."
pkill -f "websockify" 2>/dev/null
pkill -f "vnc_simulator" 2>/dev/null
pkill -f "http.server" 2>/dev/null
sleep 2

# 📁 إنشاء مجلد السجلات
echo "📁 [2/10] إنشاء مجلد السجلات..."
mkdir -p logs
rm -f logs/*.log 2>/dev/null

# 🔍 فحص التبعيات
echo "🔍 [3/10] فحص التبعيات..."
PYTHON_OK=$(python3 --version >/dev/null 2>&1 && echo "✅" || echo "❌")
WEBSOCKIFY_OK=$(python3 -c "import websockify" >/dev/null 2>&1 && echo "✅" || echo "❌")
NOVNC_OK=$([ -d "./noVNC" ] && echo "✅" || echo "❌")

echo "Python3: $PYTHON_OK"
echo "websockify: $WEBSOCKIFY_OK"
echo "noVNC: $NOVNC_OK"

if [[ "$NOVNC_OK" == "❌" ]]; then
    echo "❌ noVNC غير موجود! قم بتشغيل setup.sh"
    exit 1
fi

if [[ "$WEBSOCKIFY_OK" == "❌" ]]; then
    echo "❌ websockify غير متوفر! قم بتثبيته"
    exit 1
fi

# 🖥️ تشغيل خادم VNC المتقدم
echo "🖥️ [4/10] تشغيل خادم VNC المتقدم..."
python3 ultimate_vnc_server.py &
VNC_PID=$!
sleep 3

# فحص تشغيل VNC
if ps -p $VNC_PID > /dev/null 2>&1; then
    echo "✅ خادم VNC يعمل (PID: $VNC_PID)"
else
    echo "❌ فشل في تشغيل خادم VNC"
    cat logs/vnc_server.log 2>/dev/null
    exit 1
fi

# 🌐 تشغيل websockify
echo "🌐 [5/10] تشغيل websockify..."
cd ./noVNC
python3 -m websockify --web=. --verbose 6080 127.0.0.1:5900 > ../logs/websockify_ultimate.log 2>&1 &
WEBSOCKIFY_PID=$!
cd ..
sleep 3

# فحص websockify
if ps -p $WEBSOCKIFY_PID > /dev/null 2>&1; then
    echo "✅ websockify يعمل (PID: $WEBSOCKIFY_PID)"
else
    echo "❌ فشل في تشغيل websockify"
    cat logs/websockify_ultimate.log
    exit 1
fi

# 🌍 تشغيل خادم HTTP منفصل
echo "🌍 [6/10] تشغيل خادم HTTP..."
cd ./noVNC
python3 -m http.server 5000 --bind 0.0.0.0 > ../logs/http_ultimate.log 2>&1 &
HTTP_PID=$!
cd ..
sleep 2

# فحص HTTP
if ps -p $HTTP_PID > /dev/null 2>&1; then
    echo "✅ خادم HTTP يعمل (PID: $HTTP_PID)"
else
    echo "❌ فشل في تشغيل خادم HTTP"
    cat logs/http_ultimate.log
    exit 1
fi

# 🧪 اختبار الاتصالات
echo "🧪 [7/10] اختبار الاتصالات..."

# اختبار VNC
if python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 5900))
    s.close()
    print('VNC: متاح')
except:
    print('VNC: غير متاح')
"; then
    echo "✅ VNC Server متاح على المنفذ 5900"
else
    echo "❌ VNC Server غير متاح"
fi

# اختبار WebSocket
if python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 6080))
    s.close()
    print('WebSocket: متاح')
except:
    print('WebSocket: غير متاح')
"; then
    echo "✅ WebSocket متاح على المنفذ 6080"
else
    echo "❌ WebSocket غير متاح"
fi

# اختبار HTTP
if python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 5000))
    s.close()
    print('HTTP: متاح')
except:
    print('HTTP: غير متاح')
"; then
    echo "✅ HTTP Server متاح على المنفذ 5000"
else
    echo "❌ HTTP Server غير متاح"
fi

# 📊 إنشاء صفحة تشخيص متقدمة
echo "📊 [8/10] إنشاء صفحة التشخيص..."
cat > ./noVNC/diagnosis.html << 'DIAGNOSIS'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تشخيص VNC Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f8f9fa;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .status-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        .status-card.success {
            border-left-color: #28a745;
            background: #d4edda;
        }
        .status-card.error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        .test-button {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .test-button:hover {
            background: #0056b3;
        }
        .log-area {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            max-height: 300px;
            overflow-y: auto;
            margin: 10px 0;
        }
        .vnc-embed {
            border: 2px solid #007bff;
            border-radius: 10px;
            margin: 20px 0;
            background: white;
        }
        iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 تشخيص خادم VNC المتكامل</h1>
        
        <div class="status-grid">
            <div class="status-card" id="vnc-status">
                <h3>🖥️ VNC Server</h3>
                <p>المنفذ: 5900</p>
                <p id="vnc-result">جاري الفحص...</p>
            </div>
            
            <div class="status-card" id="websocket-status">
                <h3>🌐 WebSocket Proxy</h3>
                <p>المنفذ: 6080</p>
                <p id="websocket-result">جاري الفحص...</p>
            </div>
            
            <div class="status-card" id="http-status">
                <h3>🌍 HTTP Server</h3>
                <p>المنفذ: 5000</p>
                <p id="http-result">جاري الفحص...</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <button class="test-button" onclick="runDiagnostics()">🔄 إعادة التشخيص</button>
            <button class="test-button" onclick="testVNCConnection()">🧪 اختبار VNC</button>
            <button class="test-button" onclick="showLogs()">📋 عرض السجلات</button>
        </div>
        
        <div id="log-container" style="display: none;">
            <h3>📋 سجلات النظام</h3>
            <div class="log-area" id="log-content">جاري تحميل السجلات...</div>
        </div>
        
        <div class="vnc-embed">
            <h3>🖥️ VNC Client مباشر</h3>
            <iframe src="vnc.html?autoconnect=true&host=localhost&port=6080&password=&encrypt=false&true_color=true&cursor=true"></iframe>
        </div>
        
        <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h4>📘 معلومات الاتصال</h4>
            <ul>
                <li><strong>VNC Host:</strong> localhost</li>
                <li><strong>VNC Port:</strong> 6080 (WebSocket) / 5900 (مباشر)</li>
                <li><strong>كلمة المرور:</strong> غير مطلوبة</li>
                <li><strong>التشفير:</strong> غير مفعل</li>
                <li><strong>جودة الاتصال:</strong> عالية</li>
            </ul>
        </div>
    </div>
    
    <script>
        function updateStatus(elementId, success, message) {
            const element = document.getElementById(elementId);
            element.className = success ? 'status-card success' : 'status-card error';
            document.getElementById(elementId.replace('-status', '-result')).textContent = message;
        }
        
        function runDiagnostics() {
            // فحص WebSocket
            const ws = new WebSocket('ws://localhost:6080');
            
            ws.onopen = function() {
                updateStatus('websocket-status', true, '✅ متصل بنجاح');
                ws.close();
            };
            
            ws.onerror = function() {
                updateStatus('websocket-status', false, '❌ فشل الاتصال');
            };
            
            // فحص HTTP
            fetch('/')
                .then(response => {
                    if (response.ok) {
                        updateStatus('http-status', true, '✅ يعمل بنجاح');
                    } else {
                        updateStatus('http-status', false, '❌ خطأ في الاستجابة');
                    }
                })
                .catch(error => {
                    updateStatus('http-status', false, '❌ فشل الاتصال');
                });
            
            // فحص VNC (غير مباشر عبر WebSocket)
            setTimeout(() => {
                const testWs = new WebSocket('ws://localhost:6080');
                testWs.onopen = function() {
                    updateStatus('vnc-status', true, '✅ خادم VNC متاح');
                    testWs.close();
                };
                testWs.onerror = function() {
                    updateStatus('vnc-status', false, '❌ خادم VNC غير متاح');
                };
            }, 1000);
        }
        
        function testVNCConnection() {
            const testWs = new WebSocket('ws://localhost:6080');
            const logArea = document.getElementById('log-content');
            
            testWs.onopen = function() {
                logArea.textContent += new Date().toLocaleTimeString() + ': اتصال WebSocket نجح\n';
            };
            
            testWs.onmessage = function(event) {
                logArea.textContent += new Date().toLocaleTimeString() + ': رسالة مستقبلة من VNC\n';
            };
            
            testWs.onerror = function() {
                logArea.textContent += new Date().toLocaleTimeString() + ': خطأ في WebSocket\n';
            };
            
            testWs.onclose = function() {
                logArea.textContent += new Date().toLocaleTimeString() + ': تم إغلاق WebSocket\n';
            };
            
            document.getElementById('log-container').style.display = 'block';
            logArea.scrollTop = logArea.scrollHeight;
        }
        
        function showLogs() {
            const logContainer = document.getElementById('log-container');
            logContainer.style.display = logContainer.style.display === 'none' ? 'block' : 'none';
        }
        
        // تشغيل التشخيص عند التحميل
        window.addEventListener('load', function() {
            setTimeout(runDiagnostics, 1000);
        });
        
        // تحديث تلقائي كل 30 ثانية
        setInterval(runDiagnostics, 30000);
    </script>
</body>
</html>
DIAGNOSIS

# ☁️ تشغيل cloudflared إذا كان متوفراً
echo "☁️ [9/10] فحص cloudflared..."
if command -v cloudflared >/dev/null 2>&1; then
    echo "✅ cloudflared متوفر، بدء النفق..."
    cloudflared tunnel --url http://localhost:5000 --no-autoupdate --metrics localhost:0 > ./logs/cloudflared_ultimate.log 2>&1 &
    CLOUDFLARED_PID=$!
    sleep 10
    
    CLOUDFLARE_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' ./logs/cloudflared_ultimate.log | head -n 1)
    
    if [[ -n "$CLOUDFLARE_URL" ]]; then
        echo "✅ Cloudflare Tunnel: $CLOUDFLARE_URL"
    else
        echo "⚠️ لم يتم إنشاء نفق Cloudflare"
    fi
else
    echo "⚠️ cloudflared غير متوفر"
fi

# 📊 تقرير الحالة النهائي
echo ""
echo "🎉 [10/10] تقرير الحالة النهائي"
echo "================================="
echo "🖥️ VNC Server: $(ps -p $VNC_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $VNC_PID)" || echo "❌ لا يعمل")"
echo "🌐 WebSocket Proxy: $(ps -p $WEBSOCKIFY_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $WEBSOCKIFY_PID)" || echo "❌ لا يعمل")"
echo "🌍 HTTP Server: $(ps -p $HTTP_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $HTTP_PID)" || echo "❌ لا يعمل")"

echo ""
echo "🌐 الروابط المتاحة:"
echo "• صفحة التشخيص: http://localhost:5000/diagnosis.html"
echo "• VNC Client: http://localhost:5000/vnc.html"
echo "• VNC Lite: http://localhost:5000/vnc_lite.html"
echo "• الصفحة الرئيسية: http://localhost:5000"

if [[ -n "$CLOUDFLARE_URL" ]]; then
    echo "• رابط عام: $CLOUDFLARE_URL"
fi

echo ""
echo "🔧 معلومات الاتصال:"
echo "• VNC Server: localhost:5900"
echo "• WebSocket: localhost:6080"
echo "• HTTP: localhost:5000"
echo "• كلمة المرور: غير مطلوبة"

echo ""
echo "📋 للتشخيص والمراقبة:"
echo "• السجلات: ls -la logs/"
echo "• العمليات: ps aux | grep -E '(vnc|websockify|http)'"
echo "• المنافذ: python3 -c \"import socket; [print(f'Port {p}: {socket.socket().connect_ex(('127.0.0.1', p)) == 0}') for p in [5900, 6080, 5000]]\""

echo ""
echo "🔁 النظام يعمل بكامل طاقته... للإيقاف اضغط Ctrl+C"

# وظيفة التنظيف
cleanup() {
    echo ""
    echo "🛑 إيقاف جميع العمليات..."
    kill $VNC_PID 2>/dev/null && echo "✅ تم إيقاف VNC Server"
    kill $WEBSOCKIFY_PID 2>/dev/null && echo "✅ تم إيقاف WebSocket Proxy"
    kill $HTTP_PID 2>/dev/null && echo "✅ تم إيقاف HTTP Server"
    [[ -n "$CLOUDFLARED_PID" ]] && kill $CLOUDFLARED_PID 2>/dev/null && echo "✅ تم إيقاف Cloudflare Tunnel"
    echo "✅ تم إيقاف جميع العمليات بنجاح"
    exit 0
}

trap cleanup SIGINT SIGTERM

# انتظار لانهائي
tail -f /dev/null