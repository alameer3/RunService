"""
واجهة VNC عبر الويب
"""

import logging
import time
import subprocess
from flask import Blueprint, render_template, jsonify, request

logger = logging.getLogger(__name__)

vnc_web = Blueprint('vnc_web', __name__)

@vnc_web.route('/vnc')
def vnc_viewer():
    """واجهة عارض VNC عبر الويب"""
    return render_template('vnc_viewer.html')

@vnc_web.route('/vnc/status')
def vnc_status():
    """حالة خادم VNC"""
    try:
        # التحقق من تشغيل VNC
        vnc_check = subprocess.run(["pgrep", "-f", "x11vnc"], capture_output=True)
        xvfb_check = subprocess.run(["pgrep", "-f", "Xvfb"], capture_output=True)
        
        vnc_running = vnc_check.returncode == 0
        xvfb_running = xvfb_check.returncode == 0
        
        status = {
            'vnc_running': vnc_running,
            'xvfb_running': xvfb_running,
            'port': 5900,
            'display': ':1',
            'status': 'متصل' if vnc_running else 'غير متصل'
        }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"خطأ في فحص حالة VNC: {e}")
        return jsonify({'error': str(e)}), 500

@vnc_web.route('/api/vnc/screenshot')
def vnc_screenshot():
    """لقطة شاشة من VNC"""
    try:
        # محاكاة لقطة شاشة
        import base64
        from io import BytesIO
        from PIL import Image, ImageDraw
        
        # إنشاء صورة تجريبية
        img = Image.new('RGB', (1024, 768), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # رسم سطح مكتب بسيط
        draw.rectangle((10, 10, 1014, 50), fill='darkblue')
        draw.text((20, 25), "VNC Desktop - نظام سطح المكتب الافتراضي", fill='white')
        
        # رسم نافذة
        draw.rectangle((100, 100, 600, 400), outline='gray', width=2)
        draw.rectangle((100, 100, 600, 130), fill='lightgray')
        draw.text((110, 110), "Terminal - المحطة الطرفية", fill='black')
        
        # رسم محتوى النافذة
        draw.rectangle((110, 140, 590, 390), fill='black')
        terminal_text = [
            "user@vnc-desktop:~$ ls -la",
            "total 12",
            "drwxr-xr-x 1 user user  4096 Jan 1 12:00 .",
            "drwxr-xr-x 1 root root  4096 Jan 1 12:00 ..",
            "-rw-r--r-- 1 user user   220 Jan 1 12:00 .bash_logout",
            "-rw-r--r-- 1 user user  3771 Jan 1 12:00 .bashrc",
            "-rw-r--r-- 1 user user   807 Jan 1 12:00 .profile",
            "user@vnc-desktop:~$ _"
        ]
        
        for i, line in enumerate(terminal_text):
            draw.text((120, 150 + i * 15), line, fill='lime')
        
        # تحويل إلى base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'screenshot': f'data:image/png;base64,{img_str}',
            'timestamp': int(time.time())
        })
        
    except Exception as e:
        logger.error(f"خطأ في لقطة الشاشة: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vnc_web.route('/api/vnc/input', methods=['POST'])
def vnc_input():
    """إدخال لوحة المفاتيح والماوس"""
    try:
        data = request.get_json()
        input_type = data.get('type')  # keyboard, mouse
        
        if input_type == 'keyboard':
            key = data.get('key')
            logger.info(f"إدخال لوحة مفاتيح: {key}")
            
        elif input_type == 'mouse':
            x = data.get('x', 0)
            y = data.get('y', 0)
            button = data.get('button', 'left')
            action = data.get('action', 'click')  # click, move, drag
            logger.info(f"إدخال ماوس: {action} في ({x}, {y}) بالزر {button}")
        
        return jsonify({
            'success': True,
            'message': 'تم معالجة الإدخال'
        })
        
    except Exception as e:
        logger.error(f"خطأ في معالجة الإدخال: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# تسجيل Blueprint
def register_vnc_web(app):
    """تسجيل blueprint VNC Web"""
    app.register_blueprint(vnc_web)