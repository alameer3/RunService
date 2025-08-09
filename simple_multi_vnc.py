#!/usr/bin/env python3
"""
Simple Multi VNC - تشغيل واجهات VNC متعددة بسيط
"""

import os
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_vnc_on_port(port, description):
    """تشغيل VNC على منفذ محدد"""
    try:
        logger.info(f"🚀 تشغيل {description} على المنفذ {port}")
        
        # إيقاف أي خدمة على نفس المنفذ
        subprocess.run([
            "pkill", "-f", f"rfbport {port}"
        ], capture_output=True)
        
        time.sleep(1)
        
        # بناء أمر x11vnc
        cmd = [
            "x11vnc",
            "-display", ":1",
            "-rfbport", str(port), 
            "-passwd", "vnc123456",
            "-forever",
            "-shared",
            "-bg"
        ]
        
        # تشغيل الأمر
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} يعمل على المنفذ {port}")
            return True
        else:
            logger.error(f"❌ فشل في تشغيل {description}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل {description}: {e}")
        return False

def main():
    """تشغيل جميع الواجهات"""
    logger.info("🚀 تشغيل واجهات VNC متعددة...")
    
    # إعداد متغير البيئة
    os.environ["DISPLAY"] = ":1"
    
    # قائمة الواجهات
    interfaces = [
        (5900, "الواجهة الرئيسية"),
        (5901, "واجهة الويب"),
        (5902, "واجهة الموبايل"), 
        (5903, "واجهة المراقبة")
    ]
    
    # تشغيل كل واجهة
    success_count = 0
    for port, desc in interfaces:
        if start_vnc_on_port(port, desc):
            success_count += 1
        time.sleep(2)
    
    logger.info(f"✅ تم تشغيل {success_count}/{len(interfaces)} واجهات")
    
    # طباعة معلومات الاتصال
    logger.info("\n" + "="*50)
    logger.info("📡 معلومات الاتصال:")
    
    for port, desc in interfaces:
        # فحص حالة المنفذ
        check = subprocess.run([
            "pgrep", "-f", f"rfbport {port}"
        ], capture_output=True)
        
        status = "✅ يعمل" if check.returncode == 0 else "❌ متوقف"
        logger.info(f"  {desc}: localhost:{port} - {status}")
    
    logger.info("🔑 كلمة المرور: vnc123456")
    logger.info("="*50)

if __name__ == "__main__":
    main()