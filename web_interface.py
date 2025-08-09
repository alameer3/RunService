#!/usr/bin/env python3
"""
VNC Web Interface Server
خادم واجهة ويب لـ VNC باستخدام noVNC
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from flask import Flask, render_template_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# قالب HTML بسيط لـ noVNC
NOVNC_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VNC Desktop - سطح المكتب</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #000;
            font-family: Arial, sans-serif;
            direction: rtl;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: center;
        }
        .vnc-container {
            width: 100%;
            height: calc(100vh - 60px);
            background: #34495e;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .status-message {
            color: white;
            text-align: center;
            padding: 20px;
            background: rgba(52, 73, 94, 0.8);
            border-radius: 10px;
            margin: 20px;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥️ VNC Desktop - سطح المكتب البعيد</h1>
        <p>الحالة: {{ status }}</p>
    </div>
    <div class="vnc-container">
        {% if vnc_ready %}
            <iframe src="/vnc.html?host=localhost&port=6080&autoconnect=true&resize=scale"></iframe>
        {% else %}
            <div class="status-message">
                <h2>⚠️ خدمة VNC غير متاحة</h2>
                <p>يتم تحضير سطح المكتب، يرجى الانتظار...</p>
                <p>إذا استمر الانتظار، تحقق من تشغيل خدمة VNC Server</p>
            </div>
        {% endif %}
    </div>
    
    <script>
        // تحديث الصفحة كل 10 ثوان إذا لم تكن الخدمة جاهزة
        {% if not vnc_ready %}
        setTimeout(function() {
            location.reload();
        }, 10000);
        {% endif %}
    </script>
</body>
</html>
"""

class NoVNCServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.vnc_port = 5901
        self.novnc_port = 6080
        self.http_port = 8080
        
        # مسارات noVNC
        self.novnc_path = Path("/tmp/noVNC")
        self.websockify_pid = None
        
        self.setup_routes()
    
    def setup_routes(self):
        """إعداد مسارات Flask"""
        
        @self.app.route('/')
        def index():
            """الصفحة الرئيسية"""
            vnc_ready = self.is_vnc_ready()
            status = "متصل ✅" if vnc_ready else "غير متصل ❌"
            
            return render_template_string(
                NOVNC_TEMPLATE,
                vnc_ready=vnc_ready,
                status=status
            )
        
        @self.app.route('/status')
        def status():
            """API لحالة الاتصال"""
            return {
                "vnc_ready": self.is_vnc_ready(),
                "vnc_port": self.vnc_port,
                "novnc_port": self.novnc_port
            }
    
    def download_novnc(self):
        """تحميل noVNC إذا لم يكن موجوداً"""
        try:
            if not self.novnc_path.exists():
                logger.info("📥 تحميل noVNC...")
                
                subprocess.run([
                    "git", "clone", "--branch", "v1.2.0",
                    "https://github.com/novnc/noVNC.git",
                    str(self.novnc_path)
                ], check=True)
                
                # تحميل websockify
                websockify_path = self.novnc_path / "utils" / "websockify"
                subprocess.run([
                    "git", "clone",
                    "https://github.com/novnc/websockify",
                    str(websockify_path)
                ], check=True)
                
                logger.info("✅ تم تحميل noVNC")
                return True
            else:
                logger.info("✅ noVNC موجود مسبقاً")
                return True
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل noVNC: {e}")
            return False
    
    def start_websockify(self):
        """تشغيل websockify"""
        try:
            websockify_script = self.novnc_path / "utils" / "websockify" / "run"
            
            if not websockify_script.exists():
                logger.error("❌ websockify غير موجود")
                return False
            
            # تشغيل websockify
            cmd = [
                "python3", str(websockify_script),
                "--web", str(self.novnc_path),
                str(self.novnc_port),
                f"localhost:{self.vnc_port}"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.websockify_pid = process.pid
            time.sleep(3)
            
            # تحقق من تشغيل websockify
            if self.is_port_open(self.novnc_port):
                logger.info(f"✅ تم تشغيل websockify على المنفذ {self.novnc_port}")
                return True
            else:
                logger.error("❌ فشل في تشغيل websockify")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل websockify: {e}")
            return False
    
    def is_vnc_ready(self):
        """التحقق من جاهزية VNC"""
        return (
            self.is_port_open(self.vnc_port) and
            self.is_port_open(self.novnc_port)
        )
    
    def is_port_open(self, port):
        """التحقق من أن المنفذ مفتوح"""
        try:
            result = subprocess.run(
                ["netcat", "-z", "localhost", str(port)],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False
    
    def start_services(self):
        """تشغيل جميع الخدمات المطلوبة"""
        logger.info("🚀 بدء تشغيل خدمات noVNC...")
        
        # تحميل noVNC
        if not self.download_novnc():
            return False
        
        # تشغيل websockify
        if not self.start_websockify():
            return False
        
        logger.info("✅ تم تشغيل خدمات noVNC بنجاح")
        return True
    
    def run(self):
        """تشغيل الخادم"""
        if self.start_services():
            logger.info(f"🌐 تشغيل خادم الويب على المنفذ {self.http_port}")
            self.app.run(
                host="0.0.0.0",
                port=self.http_port,
                debug=False
            )
        else:
            logger.error("❌ فشل في تشغيل الخدمات")
            sys.exit(1)

def main():
    """البرنامج الرئيسي"""
    server = NoVNCServer()
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
    except Exception as e:
        logger.error(f"خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()