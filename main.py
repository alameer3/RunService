"""
نظام VNC Desktop المتطور
تطبيق Flask متكامل لإدارة بيئة VNC Desktop
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vnc_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# إعداد المسارات والمجلدات
BASE_DIR = Path(__file__).parent.absolute()
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
LOGS_DIR = BASE_DIR / "logs"

# إنشاء المجلدات المطلوبة
for directory in [TEMPLATES_DIR, STATIC_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# تهيئة Flask
from flask_app import create_app

app = create_app()

if __name__ == "__main__":
    logger.info("🚀 بدء تشغيل نظام VNC Desktop المتطور")
    
    # فحص متطلبات النظام
    from system_check import verify_system_requirements
    if not verify_system_requirements():
        logger.error("❌ متطلبات النظام غير مكتملة")
        sys.exit(1)
    
    # بدء الخدمات الأساسية
    from services_manager import start_background_services
    start_background_services()
    
    # تشغيل التطبيق
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True
    )