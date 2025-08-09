"""
Database models for VNC Desktop project
"""
from app import db
from datetime import datetime

class VNCSession(db.Model):
    """Model to track VNC sessions"""
    __tablename__ = 'vnc_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100), nullable=False, default='Desktop Session')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    vnc_port = db.Column(db.Integer, default=5901)
    screen_resolution = db.Column(db.String(20), default='1024x768')
    
    def __repr__(self):
        return f'<VNCSession {self.session_name}>'

class ConnectionLog(db.Model):
    """Model to track connection attempts"""
    __tablename__ = 'connection_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50), nullable=False)  # start, stop, connect
    success = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text)
    client_ip = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<ConnectionLog {self.action} at {self.timestamp}>'