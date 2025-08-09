"""
Security utilities for VNC Desktop project
أدوات الأمان لمشروع سطح مكتب VNC
"""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import request, session, abort
from functools import wraps
from app import db
from models import ConnectionLog
import logging
import os

class SecurityManager:
    """مدير الأمان للتطبيق"""
    
    def __init__(self):
        self.failed_attempts = {}  # تتبع محاولات الفشل
        self.max_attempts = 5      # الحد الأقصى للمحاولات
        self.lockout_duration = 300  # مدة الحظر بالثواني (5 دقائق)
        
    def is_ip_blocked(self, ip_address):
        """فحص ما إذا كان IP محظوراً"""
        if ip_address in self.failed_attempts:
            attempts_data = self.failed_attempts[ip_address]
            if attempts_data['count'] >= self.max_attempts:
                # فحص انتهاء فترة الحظر
                if datetime.now() < attempts_data['blocked_until']:
                    return True
                else:
                    # إنتهت فترة الحظر، إعادة تعيين
                    del self.failed_attempts[ip_address]
        return False
    
    def record_failed_attempt(self, ip_address):
        """تسجيل محاولة فاشلة"""
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = {'count': 0, 'blocked_until': None}
        
        self.failed_attempts[ip_address]['count'] += 1
        
        if self.failed_attempts[ip_address]['count'] >= self.max_attempts:
            self.failed_attempts[ip_address]['blocked_until'] = datetime.now() + timedelta(seconds=self.lockout_duration)
            logging.warning(f"IP {ip_address} has been blocked due to too many failed attempts")
    
    def reset_failed_attempts(self, ip_address):
        """إعادة تعيين المحاولات الفاشلة عند نجاح العملية"""
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]

# إنشاء مثيل عام من مدير الأمان
security_manager = SecurityManager()

def validate_vnc_password(password):
    """التحقق من صحة كلمة مرور VNC"""
    if not password:
        return False, "كلمة المرور مطلوبة"
    
    if len(password) < 6:
        return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    
    if len(password) > 8:
        return False, "كلمة المرور يجب ألا تزيد عن 8 أحرف (قيود VNC)"
    
    # فقط أحرف وأرقام
    if not re.match("^[a-zA-Z0-9]+$", password):
        return False, "كلمة المرور يجب أن تحتوي على أحرف وأرقام فقط"
    
    return True, "كلمة المرور صالحة"

def validate_screen_resolution(resolution):
    """التحقق من صحة دقة الشاشة"""
    if not resolution:
        return False, "دقة الشاشة مطلوبة"
    
    # تنسيق مثل 1024x768
    pattern = re.match(r"^(\d{3,4})x(\d{3,4})$", resolution)
    if not pattern:
        return False, "تنسيق دقة الشاشة غير صحيح (مثال: 1024x768)"
    
    width, height = int(pattern.group(1)), int(pattern.group(2))
    
    if width < 640 or height < 480:
        return False, "دقة الشاشة صغيرة جداً (الحد الأدنى 640x480)"
    
    if width > 1920 or height > 1080:
        return False, "دقة الشاشة كبيرة جداً (الحد الأقصى 1920x1080)"
    
    return True, "دقة الشاشة صالحة"

def sanitize_input(text):
    """تنظيف النص المدخل من المستخدم"""
    if not text:
        return ""
    
    # إزالة الأحرف الخطيرة
    dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def generate_session_token():
    """توليد رمز جلسة آمن"""
    return secrets.token_urlsafe(32)

def hash_password(password):
    """تشفير كلمة المرور"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, hashed_password):
    """التحقق من كلمة المرور"""
    try:
        salt, stored_hash = hashed_password.split(':')
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return stored_hash == password_hash.hex()
    except:
        return False

def rate_limit_decorator(max_requests=10, window_minutes=1):
    """محدد معدل الطلبات"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # فحص الحظر
            if security_manager.is_ip_blocked(client_ip):
                abort(429, description="تم تجاوز الحد المسموح من الطلبات")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type, description, ip_address=None, success=True):
    """تسجيل أحداث الأمان"""
    try:
        if not ip_address:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        log_entry = ConnectionLog()
        log_entry.action = f"security_{event_type}"
        log_entry.success = success
        log_entry.message = description
        log_entry.client_ip = ip_address
        db.session.add(log_entry)
        db.session.commit()
        
        if not success:
            security_manager.record_failed_attempt(ip_address)
        else:
            security_manager.reset_failed_attempts(ip_address)
            
    except Exception as e:
        logging.error(f"Failed to log security event: {e}")

def check_session_security():
    """فحص أمان الجلسة"""
    if 'session_token' not in session:
        session['session_token'] = generate_session_token()
    
    # فحص انتهاء صلاحية الجلسة
    if 'session_start' not in session:
        session['session_start'] = datetime.now().isoformat()
    
    session_start = datetime.fromisoformat(session['session_start'])
    if datetime.now() - session_start > timedelta(hours=24):
        session.clear()
        return False
    
    return True

def validate_replit_environment():
    """التحقق من بيئة Replit"""
    required_vars = ['REPL_ID', 'REPL_OWNER', 'REPLIT_DB_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.warning(f"Missing Replit environment variables: {missing_vars}")
        return False
    
    return True

class SecurityHeaders:
    """إضافة headers الأمان"""
    
    @staticmethod
    def add_security_headers(response):
        """إضافة headers الأمان للاستجابة"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        return response

# تطبيق headers الأمان على جميع الاستجابات
def init_security(app):
    """تهيئة الأمان للتطبيق"""
    
    @app.after_request
    def after_request(response):
        return SecurityHeaders.add_security_headers(response)
    
    @app.before_request
    def before_request():
        # فحص الجلسة
        if not check_session_security():
            session.clear()
        
        # تسجيل كل طلب
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if request.endpoint and not request.endpoint.startswith('static'):
            log_security_event('request', f"Access to {request.endpoint}", client_ip)