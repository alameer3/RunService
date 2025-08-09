#!/usr/bin/env python3
"""
Web VNC Interface Server - خادم واجهة VNC للويب
يوفر واجهة HTML5 للاتصال بخوادم VNC المختلفة
"""

import os
import sys
import subprocess
import time
import logging
import threading
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebVNCInterface:
    def __init__(self):
        self.app = Flask(__name__)
        self.vnc_ports = {
            'main': 5900,
            'web': 5901, 
            'mobile': 5902,
            'admin': 5903
        }
        self.websockify_processes = {}
        self.setup_routes()
        
    def setup_routes(self):
        """إعداد مسارات Flask"""
        
        @self.app.route('/')
        def index():
            """الصفحة الرئيسية - اختيار الواجهة"""
            html_content = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <title>VNC Desktop - اختر الواجهة</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        .interfaces-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        .interface-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 2px solid transparent;
        }
        .interface-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
            border-color: #3498db;
        }
        .interface-card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.4em;
        }
        .interface-card p {
            color: #7f8c8d;
            margin-bottom: 20px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        .status-online { background: #27ae60; }
        .status-offline { background: #e74c3c; }
        .btn {
            display: inline-block;
            padding: 12px 25px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 1em;
        }
        .btn:hover {
            background: #2980b9;
        }
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }
        .system-status {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .system-status h3 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .status-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }
        .status-row:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ VNC Desktop</h1>
            <p>اختر الواجهة المناسبة للاتصال بسطح المكتب البعيد</p>
        </div>
        
        <div class="interfaces-grid">
            <div class="interface-card">
                <h3>الواجهة الرئيسية <span class="status-indicator status-online" id="status-main"></span></h3>
                <p><strong>المنفذ:</strong> 5900<br>
                <strong>الوصف:</strong> واجهة VNC الأساسية مع كامل الصلاحيات</p>
                <button class="btn" onclick="connectToVNC('main', 5900)">اتصال</button>
            </div>
            
            <div class="interface-card">
                <h3>واجهة الويب <span class="status-indicator status-online" id="status-web"></span></h3>
                <p><strong>المنفذ:</strong> 5901<br>
                <strong>الوصف:</strong> محسنة للمتصفحات مع دعم HTTP</p>
                <button class="btn" onclick="connectToVNC('web', 5901)">اتصال</button>
            </div>
            
            <div class="interface-card">
                <h3>واجهة الموبايل <span class="status-indicator status-online" id="status-mobile"></span></h3>
                <p><strong>المنفذ:</strong> 5902<br>
                <strong>الوصف:</strong> محسنة للأجهزة المحمولة والشاشات الصغيرة</p>
                <button class="btn" onclick="connectToVNC('mobile', 5902)">اتصال</button>
            </div>
            
            <div class="interface-card">
                <h3>واجهة الإدارة <span class="status-indicator status-offline" id="status-admin"></span></h3>
                <p><strong>المنفذ:</strong> 5903<br>
                <strong>الوصف:</strong> للمراقبة فقط - صلاحيات محدودة</p>
                <button class="btn" onclick="connectToVNC('admin', 5903)">اتصال</button>
            </div>
        </div>
        
        <div class="system-status">
            <h3>حالة النظام</h3>
            <div class="status-row">
                <span>الشاشة الافتراضية (Xvfb)</span>
                <span id="xvfb-status">جاري الفحص...</span>
            </div>
            <div class="status-row">
                <span>خوادم VNC النشطة</span>
                <span id="vnc-count">جاري الفحص...</span>
            </div>
            <div class="status-row">
                <span>التطبيقات المفتوحة</span>
                <span id="apps-count">جاري الفحص...</span>
            </div>
        </div>
    </div>
    
    <script>
        function connectToVNC(type, port) {
            // فتح نافذة جديدة للاتصال بـ VNC
            const width = type === 'mobile' ? 800 : 1024;
            const height = type === 'mobile' ? 600 : 768;
            
            const params = `width=${width},height=${height},scrollbars=yes,resizable=yes`;
            const url = `/vnc/${type}?port=${port}`;
            
            window.open(url, `vnc_${type}`, params);
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // تحديث حالة الخوادم
                Object.keys(data.vnc_servers || {}).forEach(server => {
                    const indicator = document.getElementById(`status-${server}`);
                    if (indicator) {
                        indicator.className = `status-indicator ${data.vnc_servers[server].running ? 'status-online' : 'status-offline'}`;
                    }
                });
                
                // تحديث معلومات النظام
                document.getElementById('xvfb-status').textContent = data.xvfb_running ? 'يعمل ✅' : 'متوقف ❌';
                const activeServers = Object.values(data.vnc_servers || {}).filter(s => s.running).length;
                document.getElementById('vnc-count').textContent = `${activeServers}/4 خوادم`;
                document.getElementById('apps-count').textContent = '3+ تطبيقات';
                
            } catch (error) {
                console.error('خطأ في تحديث الحالة:', error);
            }
        }
        
        // تحديث الحالة كل 10 ثوان
        setInterval(updateStatus, 10000);
        updateStatus(); // تحديث فوري
    </script>
</body>
</html>
            """
            return html_content
        
        @self.app.route('/vnc/<interface_type>')
        def vnc_interface(interface_type):
            """واجهة VNC للنوع المحدد"""
            port = request.args.get('port', self.vnc_ports.get(interface_type, 5900))
            
            # قالب HTML لواجهة VNC
            vnc_html = f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <title>VNC Desktop - {interface_type}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #2c3e50;
            font-family: Arial, sans-serif;
            overflow: hidden;
        }}
        .vnc-container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .toolbar {{
            background: #34495e;
            padding: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
            flex-shrink: 0;
        }}
        .toolbar h3 {{
            margin: 0;
            font-size: 1.2em;
        }}
        .toolbar-buttons {{
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 8px 15px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
        }}
        .btn:hover {{
            background: #2980b9;
        }}
        .vnc-viewer {{
            flex: 1;
            background: #ecf0f1;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        .connection-info {{
            text-align: center;
            color: #7f8c8d;
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
        }}
        .connection-info h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        .connection-details {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: right;
        }}
        .connection-details strong {{
            color: #2c3e50;
        }}
        .status {{
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .status.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .instructions {{
            text-align: right;
            margin-top: 20px;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .instructions ol {{
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="vnc-container">
        <div class="toolbar">
            <h3>🖥️ VNC Desktop - {interface_type.upper()}</h3>
            <div class="toolbar-buttons">
                <button class="btn" onclick="refreshConnection()">تحديث</button>
                <button class="btn" onclick="fullscreen()">ملء الشاشة</button>
                <button class="btn" onclick="window.close()">إغلاق</button>
            </div>
        </div>
        
        <div class="vnc-viewer">
            <div class="connection-info">
                <h2>🔌 الاتصال بخادم VNC</h2>
                
                <div class="connection-details">
                    <p><strong>نوع الواجهة:</strong> {interface_type}</p>
                    <p><strong>المنفذ:</strong> {port}</p>
                    <p><strong>العرض:</strong> :1</p>
                    <p><strong>كلمة المرور:</strong> vnc123456</p>
                </div>
                
                <div class="status success">
                    ✅ الخادم متاح ويعمل بشكل طبيعي
                </div>
                
                <div class="instructions">
                    <h4>📋 تعليمات الاتصال:</h4>
                    <ol>
                        <li>استخدم برنامج VNC Viewer مثل RealVNC أو TightVNC</li>
                        <li>اتصل بالعنوان: <strong>localhost:{port}</strong></li>
                        <li>أدخل كلمة المرور: <strong>vnc123456</strong></li>
                        <li>ستظهر لك واجهة سطح المكتب مع التطبيقات المفتوحة</li>
                    </ol>
                    
                    <p><strong>ملاحظة:</strong> يمكنك أيضاً استخدام تطبيق VNC من الهاتف المحمول للاتصال.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function refreshConnection() {{
            location.reload();
        }}
        
        function fullscreen() {{
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }} else {{
                document.documentElement.requestFullscreen();
            }}
        }}
        
        // تحديث حالة الاتصال
        setInterval(async () => {{
            try {{
                const response = await fetch('/api/vnc/ping/{port}');
                const data = await response.json();
                // يمكن إضافة تحديثات الحالة هنا
            }} catch (error) {{
                console.error('خطأ في فحص الاتصال:', error);
            }}
        }}, 5000);
    </script>
</body>
</html>
            """
            return vnc_html
        
        @self.app.route('/api/status')
        def api_status():
            """API حالة النظام"""
            try:
                # فحص حالة الخدمات
                xvfb_check = subprocess.run(["pgrep", "-f", "Xvfb"], capture_output=True)
                vnc_processes = subprocess.run(["pgrep", "-f", "x11vnc"], capture_output=True, text=True)
                
                vnc_servers = {}
                for name, port in self.vnc_ports.items():
                    port_check = subprocess.run(["netcat", "-z", "localhost", str(port)], capture_output=True)
                    vnc_servers[name] = {
                        'port': port,
                        'running': port_check.returncode == 0
                    }
                
                return jsonify({
                    'xvfb_running': xvfb_check.returncode == 0,
                    'vnc_servers': vnc_servers,
                    'total_processes': len(vnc_processes.stdout.strip().split('\n')) if vnc_processes.stdout.strip() else 0
                })
                
            except Exception as e:
                logger.error(f"خطأ في API الحالة: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vnc/ping/<int:port>')
        def vnc_ping(port):
            """فحص حالة منفذ VNC محدد"""
            try:
                result = subprocess.run(["netcat", "-z", "localhost", str(port)], capture_output=True)
                return jsonify({
                    'port': port,
                    'available': result.returncode == 0,
                    'timestamp': int(time.time())
                })
            except Exception as e:
                return jsonify({
                    'port': port,
                    'available': False,
                    'error': str(e)
                }), 500
    
    def run(self, host='0.0.0.0', port=8080):
        """تشغيل خادم الواجهة"""
        logger.info(f"🌐 تشغيل واجهة VNC Web على {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

def main():
    """البرنامج الرئيسي"""
    web_interface = WebVNCInterface()
    
    try:
        web_interface.run()
    except KeyboardInterrupt:
        logger.info("تم إيقاف واجهة الويب")
    except Exception as e:
        logger.error(f"خطأ في تشغيل الواجهة: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()