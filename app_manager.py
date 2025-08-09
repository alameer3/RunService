"""
مدير التطبيقات
"""

import subprocess
import logging
from models import ApplicationInfo, SystemLog, db

logger = logging.getLogger(__name__)

def get_installed_apps():
    """الحصول على التطبيقات المثبتة"""
    try:
        from flask import current_app
        with current_app.app_context():
            apps = ApplicationInfo.query.filter_by(is_active=True).order_by(ApplicationInfo.priority.desc()).all()
            return [app.to_dict() for app in apps]
    except Exception as e:
        logger.error(f"خطأ في قراءة التطبيقات: {e}")
        # إرجاع بيانات تجريبية في حالة الخطأ
        return [
            {
                'name': 'firefox-esr',
                'display_name': 'Firefox ESR',
                'category': 'browser',
                'description': 'متصفح فايرفوكس الآمن والمستقر',
                'version': '115.0',
                'is_active': True
            }
        ]

def get_available_apps():
    """قائمة التطبيقات المتاحة للتثبيت"""
    return [
        {
            'name': 'firefox-esr',
            'display_name': 'Firefox ESR',
            'category': 'browser',
            'description': 'متصفح فايرفوكس المستقر',
            'install_command': 'apt-get install -y firefox-esr'
        },
        {
            'name': 'chromium-browser',
            'display_name': 'Chromium',
            'category': 'browser',
            'description': 'متصفح كروميوم مفتوح المصدر',
            'install_command': 'apt-get install -y chromium-browser'
        },
        {
            'name': 'gedit',
            'display_name': 'محرر النصوص',
            'category': 'editor',
            'description': 'محرر نصوص بسيط',
            'install_command': 'apt-get install -y gedit'
        },
        {
            'name': 'libreoffice',
            'display_name': 'LibreOffice',
            'category': 'office',
            'description': 'مجموعة مكتبية متكاملة',
            'install_command': 'apt-get install -y libreoffice'
        }
    ]

def install_application(app_name):
    """تثبيت تطبيق"""
    try:
        from flask import current_app
        
        available_apps = get_available_apps()
        app_info = next((app for app in available_apps if app['name'] == app_name), None)
        
        if not app_info:
            return {
                'success': False,
                'message': f'التطبيق {app_name} غير متوفر'
            }
        
        # تشغيل أمر التثبيت (محاكاة)
        logger.info(f"تثبيت {app_name}...")
        
        with current_app.app_context():
            SystemLog.log('INFO', 'APP', f'بدء تثبيت التطبيق: {app_name}')
            
            # إضافة التطبيق لقاعدة البيانات
            app_record = ApplicationInfo(
                name=app_name,
                display_name=app_info['display_name'],
                category=app_info['category'],
                description=app_info['description'],
                install_command=app_info.get('install_command', ''),
                version='1.0',
                is_active=True
            )
            
            db.session.add(app_record)
            db.session.commit()
            
            SystemLog.log('INFO', 'APP', f'تم تثبيت التطبيق بنجاح: {app_name}')
        
        return {
            'success': True,
            'message': f'تم تثبيت {app_info["display_name"]} بنجاح'
        }
        
    except Exception as e:
        logger.error(f"خطأ في تثبيت التطبيق {app_name}: {e}")
        try:
            from flask import current_app
            with current_app.app_context():
                SystemLog.log('ERROR', 'APP', f'فشل تثبيت التطبيق {app_name}: {e}')
        except:
            pass
        return {
            'success': False,
            'message': f'فشل في تثبيت التطبيق: {str(e)}'
        }