"""
فحص متطلبات النظام
"""

import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

def verify_system_requirements():
    """فحص متطلبات النظام المطلوبة"""
    try:
        # فحص Python
        try:
            import sys
            python_version = sys.version_info
            if python_version.major >= 3 and python_version.minor >= 8:
                logger.info(f"✅ Python {python_version.major}.{python_version.minor} متوفر")
            else:
                logger.warning(f"⚠️ إصدار Python قديم: {python_version.major}.{python_version.minor}")
        except Exception as e:
            logger.error(f"خطأ في فحص Python: {e}")
            return False
        
        # فحص المكتبات المطلوبة
        required_modules = [
            'flask',
            'flask_sqlalchemy', 
            'flask_socketio',
            'psutil'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            logger.warning(f"مكتبات Python مفقودة: {missing_modules}")
            return False
        
        logger.info("✅ جميع متطلبات النظام متوفرة")
        return True
        
    except Exception as e:
        logger.error(f"خطأ في فحص متطلبات النظام: {e}")
        return True  # السماح بالمتابعة حتى مع الأخطاء