"""
نماذج قاعدة البيانات لنظام VNC
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class VNCSession(db.Model):
    """جلسات VNC"""
    __tablename__ = 'vnc_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100), nullable=False, default='جلسة افتراضية')
    display_number = db.Column(db.Integer, default=1)
    port = db.Column(db.Integer, default=5900)
    screen_resolution = db.Column(db.String(20), default='1024x768')
    color_depth = db.Column(db.Integer, default=24)
    
    # معلومات الجلسة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    
    # إعدادات الأمان
    password_hash = db.Column(db.String(255))
    access_count = db.Column(db.Integer, default=0)
    
    # معلومات إضافية
    desktop_environment = db.Column(db.String(50), default='LXDE')
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<VNCSession {self.session_name}:{self.port}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_name': self.session_name,
            'display_number': self.display_number,
            'port': self.port,
            'screen_resolution': self.screen_resolution,
            'color_depth': self.color_depth,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'is_active': self.is_active,
            'access_count': self.access_count,
            'desktop_environment': self.desktop_environment,
            'notes': self.notes
        }

class ConnectionLog(db.Model):
    """سجل الاتصالات"""
    __tablename__ = 'connection_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50), nullable=False)  # connect, disconnect, start, stop
    session_id = db.Column(db.Integer, db.ForeignKey('vnc_sessions.id'))
    
    # معلومات العميل
    client_ip = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.String(255))
    
    # تفاصيل العملية
    success = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text)
    duration = db.Column(db.Integer)  # seconds
    
    # علاقات
    session = db.relationship('VNCSession', backref='connections')
    
    def __repr__(self):
        return f'<ConnectionLog {self.action} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'session_id': self.session_id,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent,
            'success': self.success,
            'message': self.message,
            'duration': self.duration
        }

class SystemLog(db.Model):
    """سجل النظام"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    category = db.Column(db.String(50), nullable=False)  # VNC, SYSTEM, APP, SECURITY
    message = db.Column(db.Text, nullable=False)
    
    # معلومات إضافية
    component = db.Column(db.String(100))  # اسم المكون المتأثر
    details = db.Column(db.Text)  # JSON أو تفاصيل إضافية
    
    def __repr__(self):
        return f'<SystemLog {self.level}:{self.category} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'category': self.category,
            'message': self.message,
            'component': self.component,
            'details': self.details
        }
    
    @classmethod
    def log(cls, level, category, message, component=None, details=None):
        """إضافة سجل جديد"""
        log_entry = cls(
            level=level,
            category=category,
            message=message,
            component=component,
            details=details
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في حفظ السجل: {e}")

class ApplicationInfo(db.Model):
    """معلومات التطبيقات المثبتة"""
    __tablename__ = 'application_info'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # browser, editor, multimedia, etc.
    description = db.Column(db.Text)
    version = db.Column(db.String(50))
    
    # معلومات التثبيت
    installed_at = db.Column(db.DateTime, default=datetime.utcnow)
    install_command = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    # معلومات الاستخدام
    launch_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # تصنيف وترتيب
    priority = db.Column(db.Integer, default=0)  # للترتيب في الواجهة
    icon = db.Column(db.String(255))  # مسار أو اسم الأيقونة
    
    def __repr__(self):
        return f'<ApplicationInfo {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'category': self.category,
            'description': self.description,
            'version': self.version,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'is_active': self.is_active,
            'launch_count': self.launch_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'priority': self.priority,
            'icon': self.icon
        }

class SystemConfig(db.Model):
    """إعدادات النظام"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, int, bool, json
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.Text)
    
    # معلومات التحديث
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'
    
    def get_value(self):
        """إرجاع القيمة بالنوع الصحيح"""
        if self.data_type == 'int':
            return int(self.value) if self.value else 0
        elif self.data_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes') if self.value else False
        elif self.data_type == 'json':
            try:
                return json.loads(self.value) if self.value else {}
            except:
                return {}
        else:
            return self.value or ''
    
    def set_value(self, value):
        """تعيين القيمة مع التحويل المناسب"""
        if self.data_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_config(cls, key, default_value=None):
        """الحصول على إعداد"""
        config = cls.query.filter_by(key=key).first()
        return config.get_value() if config else default_value
    
    @classmethod
    def set_config(cls, key, value, data_type='string', category='general', description=''):
        """تعيين إعداد"""
        config = cls.query.filter_by(key=key).first()
        if not config:
            config = cls(key=key, data_type=data_type, category=category, description=description)
            db.session.add(config)
        
        config.set_value(value)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e