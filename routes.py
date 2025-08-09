"""
Routes for the VNC Desktop web interface
"""
import os
import subprocess
import socket
import time
import threading
from flask import render_template_string, jsonify, request, redirect, url_for
from app import app

# VNC server configuration
VNC_PORT = 5901
VNC_PASSWORD = "vnc123456" 
SCREEN_RESOLUTION = "1024x768"

# HTML Template for the main page
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
                <button class="btn btn-primary" onclick="startVncServer()">🚀 بدء الخادم</button>
                <button class="btn btn-warning" onclick="stopVncServer()">⏹️ إيقاف الخادم</button>
                <button class="btn btn-warning" onclick="showLogs()">📋 عرض السجلات</button>
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
        
        function startVncServer() {
            if (confirm('هل تريد بدء تشغيل خادم VNC؟')) {
                fetch('/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(refreshStatus, 3000);
                });
            }
        }
        
        function stopVncServer() {
            if (confirm('هل تريد إيقاف خادم VNC؟')) {
                fetch('/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(refreshStatus, 2000);
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

def check_vnc_status():
    """Check VNC server status"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', VNC_PORT))
            return result == 0
    except:
        return False

def start_vnc_server():
    """Start VNC server using the VNC Desktop Server workflow"""
    try:
        # Kill any existing VNC processes first
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        time.sleep(2)
        
        # Start VNC server in background
        subprocess.Popen(['python3', 'vnc_server.py'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        app.logger.error(f"Error starting VNC server: {e}")
        return False

def stop_vnc_server():
    """Stop VNC server"""
    try:
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        return True
    except Exception as e:
        app.logger.error(f"Error stopping VNC server: {e}")
        return False

@app.route('/')
def home():
    """Main page"""
    server_status = check_vnc_status()
    
    return render_template_string(HTML_TEMPLATE, 
                                server_status=server_status,
                                vnc_port=VNC_PORT,
                                vnc_password=VNC_PASSWORD,
                                screen_resolution=SCREEN_RESOLUTION)

@app.route('/api/status')
def api_status():
    """API endpoint for server status"""
    return jsonify({
        'status': check_vnc_status(),
        'port': VNC_PORT,
        'password': VNC_PASSWORD,
        'resolution': SCREEN_RESOLUTION
    })

@app.route('/start', methods=['POST'])
def start_server():
    """Start VNC server"""
    if start_vnc_server():
        return jsonify({'success': True, 'message': 'تم بدء تشغيل خادم VNC بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في بدء تشغيل خادم VNC'}), 500

@app.route('/stop', methods=['POST'])
def stop_server():
    """Stop VNC server"""
    if stop_vnc_server():
        return jsonify({'success': True, 'message': 'تم إيقاف خادم VNC بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في إيقاف خادم VNC'}), 500

@app.route('/logs')
def show_logs():
    """Show server logs"""
    try:
        # Get recent system logs related to VNC
        result = subprocess.run(['journalctl', '--no-pager', '-n', '50', '--grep=vnc'],
                              capture_output=True, text=True)
        logs = result.stdout or "لا توجد سجلات متاحة"
    except:
        logs = "لا يمكن الوصول إلى السجلات"
    
    return logs, 200, {'Content-Type': 'text/plain; charset=utf-8'}