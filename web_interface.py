#!/usr/bin/env python3
"""
واجهة ويب لخادم VNC Desktop
توفر صفحة ويب بسيطة لعرض معلومات الاتصال وإدارة الخادم
"""

import os
import subprocess
import socket
from flask import Flask, render_template_string, jsonify, request
import threading
import time

app = Flask(__name__)

# قالب HTML للصفحة الرئيسية
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خادم VNC Desktop</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .status-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 5px solid #28a745;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        
        .status-running {
            background-color: #28a745;
            animation: pulse 2s infinite;
        }
        
        .status-stopped {
            background-color: #dc3545;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .info-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        
        .info-item h3 {
            color: #495057;
            margin-bottom: 10px;
            font-size: 1em;
        }
        
        .info-item p {
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
        }
        
        .connection-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 25px;
        }
        
        .connection-section h2 {
            margin-bottom: 20px;
            text-align: center;
        }
        
        .connection-steps {
            list-style: none;
            counter-reset: step-counter;
        }
        
        .connection-steps li {
            counter-increment: step-counter;
            margin-bottom: 15px;
            padding-right: 30px;
            position: relative;
        }
        
        .connection-steps li::before {
            content: counter(step-counter);
            position: absolute;
            right: 0;
            top: 0;
            background: rgba(255,255,255,0.2);
            color: white;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-top: 25px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-warning {
            background: #ffc107;
            color: #212529;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .vnc-clients {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin-top: 25px;
        }
        
        .vnc-clients h3 {
            margin-bottom: 15px;
            color: #495057;
        }
        
        .client-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .client-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s;
        }
        
        .client-item:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ خادم VNC Desktop</h1>
            <p>سطح مكتب عن بُعد مع متصفح ويب</p>
        </div>
        
        <div class="content">
            <div class="status-card">
                <h2>
                    حالة الخادم
                    <span class="status-indicator {{ 'status-running' if server_status else 'status-stopped' }}"></span>
                </h2>
                <p>{{ 'الخادم يعمل بشكل طبيعي' if server_status else 'الخادم متوقف' }}</p>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <h3>عنوان الخادم</h3>
                    <p>localhost</p>
                </div>
                <div class="info-item">
                    <h3>المنفذ</h3>
                    <p>{{ vnc_port }}</p>
                </div>
                <div class="info-item">
                    <h3>كلمة المرور</h3>
                    <p>{{ vnc_password }}</p>
                </div>
                <div class="info-item">
                    <h3>دقة الشاشة</h3>
                    <p>{{ screen_resolution }}</p>
                </div>
            </div>
            
            <div class="connection-section">
                <h2>📋 خطوات الاتصال</h2>
                <ol class="connection-steps">
                    <li>قم بتنزيل وتثبيت برنامج VNC Viewer</li>
                    <li>افتح البرنامج وأدخل العنوان: <strong>localhost:{{ vnc_port }}</strong></li>
                    <li>عند المطالبة، أدخل كلمة المرور: <strong>{{ vnc_password }}</strong></li>
                    <li>اضغط Connect للاتصال بسطح المكتب</li>
                </ol>
            </div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="refreshStatus()">🔄 تحديث الحالة</button>
                <button class="btn btn-primary" onclick="restartServer()">🚀 إعادة التشغيل</button>
                <button class="btn btn-warning" onclick="showLogs()">📋 عرض السجلات</button>
                <a href="/download" class="btn btn-primary">📥 تحميل العميل</a>
            </div>
            
            <div class="vnc-clients">
                <h3>🔧 برامج VNC الموصى بها</h3>
                <div class="client-list">
                    <div class="client-item">
                        <h4>VNC Viewer</h4>
                        <p>الأفضل للاستخدام العام</p>
                    </div>
                    <div class="client-item">
                        <h4>TigerVNC</h4>
                        <p>سريع ومستقر</p>
                    </div>
                    <div class="client-item">
                        <h4>TightVNC</h4>
                        <p>خفيف ومضغوط</p>
                    </div>
                    <div class="client-item">
                        <h4>Remmina (Linux)</h4>
                        <p>مدمج مع Linux</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2025 خادم VNC Desktop - مُحسن للسيرفرات الخفيفة</p>
        </div>
    </div>
    
    <script>
        function refreshStatus() {
            window.location.reload();
        }
        
        function restartServer() {
            if (confirm('هل تريد إعادة تشغيل خادم VNC؟')) {
                fetch('/restart', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(refreshStatus, 3000);
                });
            }
        }
        
        function showLogs() {
            fetch('/logs')
            .then(response => response.text())
            .then(data => {
                const logWindow = window.open('', '_blank', 'width=800,height=600');
                logWindow.document.write('<html><head><title>سجلات الخادم</title></head><body>');
                logWindow.document.write('<h2>سجلات خادم VNC</h2>');
                logWindow.document.write('<pre style="background:#f8f9fa;padding:15px;border-radius:5px;font-family:monospace;">' + data + '</pre>');
                logWindow.document.write('</body></html>');
            });
        }
        
        // تحديث تلقائي كل 30 ثانية
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
"""

class VNCWebInterface:
    def __init__(self, vnc_port=5901, web_port=5000):
        self.vnc_port = vnc_port
        self.web_port = web_port
        self.vnc_password = "vnc123456"
        self.screen_resolution = "1024x768"
    
    def check_vnc_status(self):
        """فحص حالة خادم VNC"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', self.vnc_port))
                return result == 0
        except:
            return False
    
    def get_vnc_processes(self):
        """الحصول على عمليات VNC النشطة"""
        try:
            result = subprocess.run(['pgrep', '-f', 'x11vnc'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except:
            return 0
    
    def restart_vnc_server(self):
        """إعادة تشغيل خادم VNC"""
        try:
            # إيقاف العمليات الحالية
            subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
            subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
            
            time.sleep(2)
            
            # بدء الخادم من جديد (يفترض وجود main.py)
            subprocess.Popen(['python3', 'main.py'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
            print(f"خطأ في إعادة التشغيل: {e}")
            return False

# إنشاء مثيل الواجهة
vnc_interface = VNCWebInterface()

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    server_status = vnc_interface.check_vnc_status()
    
    return render_template_string(HTML_TEMPLATE, 
                                server_status=server_status,
                                vnc_port=vnc_interface.vnc_port,
                                vnc_password=vnc_interface.vnc_password,
                                screen_resolution=vnc_interface.screen_resolution)

@app.route('/api/status')
def api_status():
    """API للحصول على حالة الخادم"""
    return jsonify({
        'server_running': vnc_interface.check_vnc_status(),
        'vnc_processes': vnc_interface.get_vnc_processes(),
        'vnc_port': vnc_interface.vnc_port,
        'vnc_password': vnc_interface.vnc_password,
        'screen_resolution': vnc_interface.screen_resolution
    })

@app.route('/restart', methods=['POST'])
def restart_server():
    """إعادة تشغيل خادم VNC"""
    success = vnc_interface.restart_vnc_server()
    return jsonify({
        'success': success,
        'message': 'تم إعادة تشغيل الخادم بنجاح' if success else 'فشل في إعادة تشغيل الخادم'
    })

@app.route('/logs')
def show_logs():
    """عرض سجلات النظام"""
    try:
        # محاولة قراءة سجلات مختلفة
        logs = []
        
        # سجلات VNC
        try:
            result = subprocess.run(['pgrep', '-f', 'x11vnc'], capture_output=True, text=True)
            if result.stdout.strip():
                logs.append("=== عمليات VNC النشطة ===")
                logs.append(result.stdout)
        except:
            pass
        
        # سجلات Xvfb
        try:
            result = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True, text=True)
            if result.stdout.strip():
                logs.append("\n=== عمليات Xvfb النشطة ===")
                logs.append(result.stdout)
        except:
            pass
        
        # معلومات الشبكة
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            vnc_lines = [line for line in result.stdout.split('\n') if ':590' in line]
            if vnc_lines:
                logs.append("\n=== منافذ VNC النشطة ===")
                logs.extend(vnc_lines)
        except:
            pass
        
        if not logs:
            logs.append("لا توجد سجلات متاحة")
        
        return '\n'.join(logs)
        
    except Exception as e:
        return f"خطأ في قراءة السجلات: {e}"

@app.route('/download')
def download_page():
    """صفحة تنزيل عملاء VNC"""
    download_links = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تنزيل عملاء VNC</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #333; text-align: center; }
            .client { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .client h3 { margin: 0 0 10px 0; color: #007bff; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>تنزيل عملاء VNC</h1>
            
            <div class="client">
                <h3>VNC Viewer (موصى به)</h3>
                <p>العميل الأكثر شعبية واستقراراً</p>
                <p><a href="https://www.realvnc.com/download/viewer/" target="_blank">تنزيل VNC Viewer</a></p>
            </div>
            
            <div class="client">
                <h3>TigerVNC</h3>
                <p>عميل مفتوح المصدر وسريع</p>
                <p><a href="https://github.com/TigerVNC/tigervnc/releases" target="_blank">تنزيل TigerVNC</a></p>
            </div>
            
            <div class="client">
                <h3>TightVNC</h3>
                <p>عميل خفيف ومضغوط</p>
                <p><a href="https://www.tightvnc.com/download.php" target="_blank">تنزيل TightVNC</a></p>
            </div>
            
            <div class="client">
                <h3>UltraVNC (Windows فقط)</h3>
                <p>عميل متقدم لنظام Windows</p>
                <p><a href="https://www.uvnc.com/downloads/ultravnc.html" target="_blank">تنزيل UltraVNC</a></p>
            </div>
            
            <br>
            <p style="text-align: center;">
                <a href="/">&larr; العودة للصفحة الرئيسية</a>
            </p>
        </div>
    </body>
    </html>
    """
    return download_links

def run_web_interface(host='0.0.0.0', port=5000):
    """تشغيل واجهة الويب"""
    print(f"🌐 بدء تشغيل واجهة الويب على http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_web_interface()