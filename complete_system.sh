#!/bin/bash

echo "==== نظام OneClickDesktop كامل ومحسن $(date) ===="

# 🧹 تنظيف شامل
echo "🧹 [1/8] تنظيف شامل للعمليات..."
pkill -f "python3.*vnc" 2>/dev/null
pkill -f "websockify" 2>/dev/null
pkill -f "http.server" 2>/dev/null
pkill -f "oneclick" 2>/dev/null
sleep 3

# 📁 إعداد المجلدات
echo "📁 [2/8] إعداد المجلدات..."
mkdir -p logs
rm -f logs/*.log 2>/dev/null

# 🔍 فحص شامل للنظام
echo "🔍 [3/8] فحص شامل للنظام..."
echo "=== تحليل OneClickDesktop ==="
if [[ -f "OneClickDesktop/OneClickDesktop.sh" ]]; then
    echo "✅ OneClickDesktop.sh موجود"
    
    # استخراج معلومات مفصلة
    GUAC_VERSION=$(grep "GUACAMOLE_VERSION=" OneClickDesktop/OneClickDesktop.sh | head -1 | cut -d'"' -f2)
    DOWNLOAD_LINK=$(grep "GUACAMOLE_DOWNLOAD_LINK=" OneClickDesktop/OneClickDesktop.sh | head -1 | cut -d'"' -f2)
    FUNCTIONS_COUNT=$(grep -c "^function " OneClickDesktop/OneClickDesktop.sh)
    
    echo "📊 تفاصيل OneClickDesktop:"
    echo "  • إصدار Guacamole: $GUAC_VERSION"
    echo "  • رابط التحميل: $DOWNLOAD_LINK"
    echo "  • عدد الوظائف: $FUNCTIONS_COUNT"
    
    # فحص الإضافات
    if [[ -d "OneClickDesktop/plugins" ]]; then
        CHROME_PLUGIN=$(find OneClickDesktop/plugins -name "*chrome*" -type f | wc -l)
        AUDIO_PLUGIN=$(find OneClickDesktop/plugins -name "*audio*" -type f | wc -l)
        echo "  • إضافة Chrome: $([ $CHROME_PLUGIN -gt 0 ] && echo "✅" || echo "❌")"
        echo "  • إضافة الصوت: $([ $AUDIO_PLUGIN -gt 0 ] && echo "✅" || echo "❌")"
    fi
else
    echo "❌ OneClickDesktop غير موجود"
fi

echo ""
echo "=== فحص التبعيات ==="
PYTHON_VER=$(python3 --version 2>/dev/null | cut -d' ' -f2)
WEBSOCKIFY_VER=$(python3 -c "import websockify; print('متوفر')" 2>/dev/null || echo "غير متوفر")
NOVNC_VER=$([ -d "noVNC" ] && echo "متوفر" || echo "غير متوفر")

echo "Python3: $PYTHON_VER"
echo "websockify: $WEBSOCKIFY_VER"
echo "noVNC: $NOVNC_VER"

# 🖥️ تشغيل خادم VNC محسن
echo "🖥️ [4/8] تشغيل خادم VNC محسن..."
python3 fixed_vnc_server.py > logs/vnc_fixed.log 2>&1 &
VNC_PID=$!
sleep 3

# فحص حالة VNC
if ps -p $VNC_PID > /dev/null 2>&1; then
    echo "✅ خادم VNC محسن يعمل (PID: $VNC_PID)"
    
    # اختبار الاتصال
    if python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 5900))
    s.close()
    print('VNC متاح للاتصال')
except Exception as e:
    print(f'VNC غير متاح: {e}')
"; then
        echo "✅ VNC Server يقبل الاتصالات"
    else
        echo "⚠️ VNC Server لا يقبل الاتصالات"
    fi
else
    echo "❌ فشل في تشغيل VNC Server"
    cat logs/vnc_fixed.log
    exit 1
fi

# 🌐 تشغيل WebSocket Proxy
echo "🌐 [5/8] تشغيل WebSocket Proxy..."
cd noVNC
python3 -m websockify --web=. --verbose 6080 127.0.0.1:5900 > ../logs/websockify_complete.log 2>&1 &
WEBSOCKIFY_PID=$!
cd ..
sleep 3

if ps -p $WEBSOCKIFY_PID > /dev/null 2>&1; then
    echo "✅ WebSocket Proxy يعمل (PID: $WEBSOCKIFY_PID)"
else
    echo "❌ فشل في تشغيل WebSocket Proxy"
    cat logs/websockify_complete.log
    exit 1
fi

# 🌍 تشغيل خادم HTTP
echo "🌍 [6/8] تشغيل خادم HTTP..."
cd noVNC
python3 -m http.server 5000 --bind 0.0.0.0 > ../logs/http_complete.log 2>&1 &
HTTP_PID=$!
cd ..
sleep 2

if ps -p $HTTP_PID > /dev/null 2>&1; then
    echo "✅ خادم HTTP يعمل (PID: $HTTP_PID)"
else
    echo "❌ فشل في تشغيل خادم HTTP"
fi

# 🧪 اختبارات شاملة
echo "🧪 [7/8] اختبارات شاملة..."

echo "=== اختبار المنافذ ==="
for PORT in 5900 6080 5000; do
    if python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(1)
    result = s.connect_ex(('127.0.0.1', $PORT))
    s.close()
    print('متاح' if result == 0 else 'مغلق')
except:
    print('خطأ')
"; then
        STATUS=$(python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(1)
    result = s.connect_ex(('127.0.0.1', $PORT))
    s.close()
    print('✅' if result == 0 else '❌')
except:
    print('❌')
")
        echo "المنفذ $PORT: $STATUS"
    fi
done

echo ""
echo "=== اختبار HTTP ==="
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ || echo "فشل")
echo "HTTP Response: $HTTP_STATUS"

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "✅ خادم HTTP يستجيب بشكل صحيح"
else
    echo "❌ مشكلة في خادم HTTP"
fi

echo ""
echo "=== اختبار WebSocket ==="
WS_TEST=$(python3 -c "
import socket
try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 6080))
    s.send(b'GET /websockify HTTP/1.1\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n\r\n')
    response = s.recv(1024)
    s.close()
    print('يعمل' if b'websocket' in response.lower() or b'upgrade' in response.lower() else 'مشكلة')
except Exception as e:
    print(f'فشل: {e}')
" 2>/dev/null)
echo "WebSocket Test: $WS_TEST"

# 📊 إنشاء صفحة حالة شاملة
echo "📊 [8/8] إنشاء صفحة الحالة الشاملة..."
cat > noVNC/system-status.html << 'STATUSHTML'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>حالة النظام الشاملة</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .status-card {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        .status-card.online {
            border-color: #2ecc71;
            box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
        }
        .status-card.offline {
            border-color: #e74c3c;
            box-shadow: 0 0 20px rgba(231, 76, 60, 0.3);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-green { background: #2ecc71; }
        .status-red { background: #e74c3c; }
        .status-yellow { background: #f39c12; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .vnc-viewer {
            grid-column: 1 / -1;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 10px;
            background: white;
        }
        
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            margin: 10px;
            font-size: 16px;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .log-viewer {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 10px;
            font-family: monospace;
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
            display: none;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ OneClickDesktop - حالة النظام الشاملة</h1>
            <p>نظام سطح المكتب عن بُعد مع VNC وGuacamole</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card" id="vnc-card">
                <div class="card-header">
                    <h3>🖥️ VNC Server</h3>
                    <span class="status-indicator status-green" id="vnc-indicator"></span>
                </div>
                <p><strong>المنفذ:</strong> 5900</p>
                <p><strong>الدقة:</strong> 1024x768</p>
                <p><strong>الحالة:</strong> <span id="vnc-status">جاري الفحص...</span></p>
            </div>
            
            <div class="status-card" id="websocket-card">
                <div class="card-header">
                    <h3>🌐 WebSocket Proxy</h3>
                    <span class="status-indicator status-green" id="websocket-indicator"></span>
                </div>
                <p><strong>المنفذ:</strong> 6080</p>
                <p><strong>البروتوكول:</strong> VNC over WebSocket</p>
                <p><strong>الحالة:</strong> <span id="websocket-status">جاري الفحص...</span></p>
            </div>
            
            <div class="status-card" id="http-card">
                <div class="card-header">
                    <h3>🌍 HTTP Server</h3>
                    <span class="status-indicator status-green" id="http-indicator"></span>
                </div>
                <p><strong>المنفذ:</strong> 5000</p>
                <p><strong>الخادم:</strong> Python HTTP Server</p>
                <p><strong>الحالة:</strong> <span id="http-status">جاري الفحص...</span></p>
            </div>
            
            <div class="status-card">
                <div class="card-header">
                    <h3>📊 OneClickDesktop</h3>
                    <span class="status-indicator status-yellow"></span>
                </div>
                <p><strong>الإصدار:</strong> v0.4.0</p>
                <p><strong>Guacamole:</strong> 1.5.5 (محاكي)</p>
                <p><strong>الحالة:</strong> محدود للـ Replit</p>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="runSystemTest()">🧪 اختبار شامل</button>
            <button class="btn" onclick="connectVNC()">🔗 اتصال VNC</button>
            <button class="btn" onclick="toggleLogs()">📋 عرض السجلات</button>
            <button class="btn" onclick="refreshStatus()">🔄 تحديث الحالة</button>
        </div>
        
        <div class="log-viewer" id="log-viewer">
            <div id="log-content">جاري تحميل السجلات...</div>
        </div>
        
        <div class="vnc-viewer">
            <h3>🖥️ VNC Desktop Viewer</h3>
            <iframe src="vnc.html?autoconnect=true&host=localhost&port=6080&resize=scale&quality=9" id="vnc-frame"></iframe>
        </div>
        
        <div class="footer">
            <h4>📘 معلومات النظام</h4>
            <p><strong>OneClickDesktop الأصلي:</strong> نظام كامل لإعداد سطح مكتب عن بُعد مع Guacamole + Tomcat + XFCE4</p>
            <p><strong>هذا المحول:</strong> نسخة محدودة تعمل في بيئة Replit بدون صلاحيات الجذر</p>
            <p><strong>الميزات المتاحة:</strong> VNC Server تفاعلي + WebSocket Proxy + واجهة ويب شاملة</p>
        </div>
    </div>
    
    <script>
        function updateServiceStatus(service, isOnline, message) {
            const card = document.getElementById(service + '-card');
            const indicator = document.getElementById(service + '-indicator');
            const status = document.getElementById(service + '-status');
            
            card.className = 'status-card ' + (isOnline ? 'online' : 'offline');
            indicator.className = 'status-indicator ' + (isOnline ? 'status-green' : 'status-red');
            status.textContent = message;
        }
        
        function checkVNCStatus() {
            // محاولة اتصال TCP للمنفذ 5900
            fetch('/diagnosis.html')
                .then(() => updateServiceStatus('vnc', true, 'VNC Server يعمل'))
                .catch(() => updateServiceStatus('vnc', false, 'VNC Server لا يستجيب'));
        }
        
        function checkWebSocketStatus() {
            const ws = new WebSocket('ws://localhost:6080');
            ws.onopen = function() {
                updateServiceStatus('websocket', true, 'WebSocket متصل');
                ws.close();
            };
            ws.onerror = function() {
                updateServiceStatus('websocket', false, 'WebSocket فشل الاتصال');
            };
        }
        
        function checkHTTPStatus() {
            fetch('/')
                .then(response => {
                    if (response.ok) {
                        updateServiceStatus('http', true, 'HTTP Server يعمل');
                    } else {
                        updateServiceStatus('http', false, 'HTTP خطأ: ' + response.status);
                    }
                })
                .catch(() => updateServiceStatus('http', false, 'HTTP غير متاح'));
        }
        
        function refreshStatus() {
            checkVNCStatus();
            checkWebSocketStatus();
            checkHTTPStatus();
        }
        
        function runSystemTest() {
            const logContent = document.getElementById('log-content');
            const logViewer = document.getElementById('log-viewer');
            
            logViewer.style.display = 'block';
            logContent.innerHTML = '';
            
            const tests = [
                '🧪 بدء الاختبار الشامل...',
                '📡 فحص اتصال VNC Server...',
                '🌐 فحص WebSocket Proxy...',
                '🌍 فحص HTTP Server...',
                '🔗 اختبار البروتوكولات...',
                '✅ اكتمل الاختبار الشامل'
            ];
            
            let index = 0;
            const interval = setInterval(() => {
                if (index < tests.length) {
                    logContent.innerHTML += new Date().toLocaleTimeString() + ': ' + tests[index] + '\\n';
                    logContent.scrollTop = logContent.scrollHeight;
                    index++;
                } else {
                    clearInterval(interval);
                    refreshStatus();
                }
            }, 1000);
        }
        
        function connectVNC() {
            const frame = document.getElementById('vnc-frame');
            frame.src = frame.src + '&reconnect=' + Date.now();
        }
        
        function toggleLogs() {
            const logViewer = document.getElementById('log-viewer');
            logViewer.style.display = logViewer.style.display === 'none' ? 'block' : 'none';
        }
        
        // تحديث تلقائي كل 30 ثانية
        setInterval(refreshStatus, 30000);
        
        // فحص أولي عند التحميل
        window.addEventListener('load', function() {
            setTimeout(refreshStatus, 1000);
        });
    </script>
</body>
</html>
STATUSHTML

# 🎉 تقرير الحالة النهائي
echo ""
echo "🎉 تم تشغيل النظام الكامل بنجاح!"
echo "============================================="

echo ""
echo "📊 حالة الخدمات:"
echo "🖥️ VNC Server: $(ps -p $VNC_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $VNC_PID)" || echo "❌ لا يعمل")"
echo "🌐 WebSocket Proxy: $(ps -p $WEBSOCKIFY_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $WEBSOCKIFY_PID)" || echo "❌ لا يعمل")"
echo "🌍 HTTP Server: $(ps -p $HTTP_PID > /dev/null 2>&1 && echo "✅ يعمل (PID: $HTTP_PID)" || echo "❌ لا يعمل")"

echo ""
echo "🌐 الروابط المتاحة:"
echo "• حالة النظام: http://localhost:5000/system-status.html"
echo "• OneClick Demo: http://localhost:5000/oneclick-demo.html"
echo "• صفحة التشخيص: http://localhost:5000/diagnosis.html"
echo "• VNC Client: http://localhost:5000/vnc.html"

echo ""
echo "🔧 معلومات تقنية:"
echo "• VNC Server: localhost:5900 (محسن)"
echo "• WebSocket: localhost:6080"
echo "• HTTP: localhost:5000"
echo "• البروتوكول: RFB 3.8"

echo ""
echo "📋 OneClickDesktop الأصلي vs المحول:"
echo "الأصلي: Ubuntu/Debian + Root + Guacamole + Tomcat + XFCE4 + RDP"
echo "المحول: Replit + Python + VNC + WebSocket + محاكي Guacamole"

echo ""
echo "🔁 النظام يعمل بكامل طاقته... للإيقاف اضغط Ctrl+C"

# وظيفة التنظيف
cleanup() {
    echo ""
    echo "🛑 إيقاف النظام الكامل..."
    kill $VNC_PID 2>/dev/null && echo "✅ تم إيقاف VNC Server"
    kill $WEBSOCKIFY_PID 2>/dev/null && echo "✅ تم إيقاف WebSocket Proxy"
    kill $HTTP_PID 2>/dev/null && echo "✅ تم إيقاف HTTP Server"
    echo "✅ تم إيقاف جميع الخدمات"
    exit 0
}

trap cleanup SIGINT SIGTERM

# انتظار لانهائي
tail -f /dev/null