"""
VNC Desktop System - Entry Point
نقطة دخول نظام VNC Desktop في بيئة Replit
"""

import os
import sys
import logging
import threading
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Flask app
from app import app

def start_vnc_services():
    """تشغيل خدمات VNC في خيط منفصل"""
    try:
        from vnc_native import VNCManager
        
        vnc = VNCManager()
        logger.info("🚀 بدء تشغيل خدمات VNC...")
        
        if vnc.start_all():
            logger.info("✅ تم تشغيل VNC بنجاح على المنفذ 5901")
            
            # مراقبة الخدمات
            while True:
                time.sleep(30)
                status = vnc.get_status()
                if not status["x11vnc_running"]:
                    logger.warning("⚠️ إعادة تشغيل VNC Server...")
                    vnc.start_x11vnc()
        else:
            logger.error("❌ فشل في تشغيل VNC")
            
    except Exception as e:
        logger.error(f"خطأ في خدمات VNC: {e}")

# تشغيل خدمات VNC في الخلفية
vnc_thread = threading.Thread(target=start_vnc_services, daemon=True)
vnc_thread.start()

# Export Flask app for gunicorn
if __name__ == "__main__":
    # هذا الجزء لن يعمل مع gunicorn، ولكنه مفيد للاختبار المحلي
    app.run(host="0.0.0.0", port=5000, debug=True)