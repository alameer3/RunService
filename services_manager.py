"""
مدير الخدمات الخلفية
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

def start_background_services():
    """بدء الخدمات الخلفية"""
    try:
        logger.info("🔧 بدء الخدمات الخلفية...")
        
        # بدء مراقب النظام
        monitor_thread = threading.Thread(target=system_monitor_worker, daemon=True)
        monitor_thread.start()
        
        # بدء خادم VNC للاتصال الخارجي
        vnc_thread = threading.Thread(target=start_vnc_server, daemon=True)
        vnc_thread.start()
        
        logger.info("✅ تم بدء جميع الخدمات الخلفية")
        
    except Exception as e:
        logger.error(f"خطأ في بدء الخدمات: {e}")

def system_monitor_worker():
    """عامل مراقبة النظام"""
    while True:
        try:
            # مراقبة بسيطة - يمكن تطويرها لاحقاً
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"خطأ في مراقب النظام: {e}")
            time.sleep(10)

def start_vnc_server():
    """بدء خادم VNC في الخلفية"""
    try:
        from simple_vnc_server import SimpleVNCServer
        
        logger.info("🚀 بدء خادم VNC على المنفذ 8000...")
        vnc_server = SimpleVNCServer()
        
        if vnc_server.start():
            logger.info("✅ خادم VNC يعمل بنجاح على المنفذ 8000")
            
            # الحفاظ على الخادم يعمل
            while vnc_server.is_running:
                time.sleep(10)
        else:
            logger.error("❌ فشل في بدء خادم VNC")
            
    except Exception as e:
        logger.error(f"خطأ في خادم VNC: {e}")