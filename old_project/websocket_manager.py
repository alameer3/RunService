"""
WebSocket Manager for Real-time Updates
مدير WebSocket للتحديثات الفورية
"""
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import json
import logging
from datetime import datetime
from typing import Dict, List
from redis_manager import redis_manager
import threading
import time

class WebSocketManager:
    """مدير WebSocket للتحديثات الفورية"""
    
    def __init__(self, app: Flask = None):
        self.socketio = None
        self.connected_clients = {}
        self.rooms = {}
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """تهيئة SocketIO مع Flask"""
        self.app = app
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=False
        )
        
        self._register_handlers()
        self._start_background_tasks()
        
        logging.info("WebSocket manager initialized")
    
    def _register_handlers(self):
        """تسجيل معالجات WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """عند اتصال عميل جديد"""
            client_id = str(id(auth)) if auth else 'anonymous'
            
            self.connected_clients[client_id] = {
                'connected_at': datetime.now(),
                'last_ping': datetime.now(),
                'subscriptions': set()
            }
            
            emit('connection_established', {
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'message': 'مرحباً! تم الاتصال بنجاح'
            })
            
            logging.info(f"Client {client_id} connected via WebSocket")
            
            # إرسال حالة النظام الحالية
            self._send_system_status(client_id)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """عند قطع الاتصال"""
            client_id = self._get_client_id()
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            
            logging.info(f"Client {client_id} disconnected")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """الاشتراك في تحديثات معينة"""
            client_id = self._get_client_id()
            subscription_type = data.get('type', 'general')
            
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscriptions'].add(subscription_type)
                join_room(subscription_type)
                
                emit('subscription_confirmed', {
                    'type': subscription_type,
                    'message': f'تم الاشتراك في {subscription_type}'
                })
                
                logging.info(f"Client {client_id} subscribed to {subscription_type}")
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """إلغاء الاشتراك"""
            client_id = self._get_client_id()
            subscription_type = data.get('type', 'general')
            
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscriptions'].discard(subscription_type)
                leave_room(subscription_type)
                
                emit('subscription_cancelled', {
                    'type': subscription_type,
                    'message': f'تم إلغاء الاشتراك في {subscription_type}'
                })
        
        @self.socketio.on('ping')
        def handle_ping():
            """Ping للحفاظ على الاتصال"""
            client_id = self._get_client_id()
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['last_ping'] = datetime.now()
            
            emit('pong', {'timestamp': datetime.now().isoformat()})
        
        @self.socketio.on('request_status')
        def handle_status_request(data):
            """طلب حالة محددة"""
            status_type = data.get('type', 'system')
            client_id = self._get_client_id()
            
            if status_type == 'system':
                self._send_system_status(client_id)
            elif status_type == 'vnc':
                self._send_vnc_status(client_id)
            elif status_type == 'performance':
                self._send_performance_status(client_id)
    
    def _get_client_id(self) -> str:
        """الحصول على معرف العميل"""
        from flask import request
        return request.sid
    
    def _send_system_status(self, client_id: str = None):
        """إرسال حالة النظام"""
        try:
            from performance import performance_monitor
            metrics = performance_monitor.get_current_metrics()
            
            status_data = {
                'type': 'system_status',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'cpu': metrics.get('cpu', {}),
                    'memory': metrics.get('memory', {}),
                    'disk': metrics.get('disk', {}),
                    'uptime': metrics.get('application', {}).get('uptime_seconds', 0)
                }
            }
            
            if client_id:
                self.socketio.emit('system_status', status_data, room=client_id)
            else:
                self.socketio.emit('system_status', status_data, room='system')
                
        except Exception as e:
            logging.error(f"Error sending system status: {e}")
    
    def _send_vnc_status(self, client_id: str = None):
        """إرسال حالة VNC"""
        try:
            import socket
            
            # فحص حالة VNC
            vnc_running = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    result = sock.connect_ex(('127.0.0.1', 5900))
                    vnc_running = result == 0
            except:
                pass
            
            status_data = {
                'type': 'vnc_status',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'running': vnc_running,
                    'port': 5900,
                    'url': f"vnc://localhost:5900"
                }
            }
            
            if client_id:
                self.socketio.emit('vnc_status', status_data, room=client_id)
            else:
                self.socketio.emit('vnc_status', status_data, room='vnc')
                
        except Exception as e:
            logging.error(f"Error sending VNC status: {e}")
    
    def _send_performance_status(self, client_id: str = None):
        """إرسال حالة الأداء"""
        try:
            from performance import performance_monitor
            metrics = performance_monitor.get_current_metrics()
            alerts = performance_monitor.get_performance_alerts()
            
            status_data = {
                'type': 'performance_status',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'metrics': metrics,
                    'alerts': alerts,
                    'redis_stats': redis_manager.get_stats() if redis_manager.is_connected() else {}
                }
            }
            
            if client_id:
                self.socketio.emit('performance_status', status_data, room=client_id)
            else:
                self.socketio.emit('performance_status', status_data, room='performance')
                
        except Exception as e:
            logging.error(f"Error sending performance status: {e}")
    
    def _start_background_tasks(self):
        """بدء المهام في الخلفية"""
        
        def periodic_updates():
            """تحديثات دورية"""
            while True:
                try:
                    # تحديث حالة النظام كل 5 ثواني
                    self._send_system_status()
                    
                    # تحديث حالة VNC كل 10 ثواني
                    if len(self.connected_clients) > 0:
                        self._send_vnc_status()
                    
                    time.sleep(5)
                    
                except Exception as e:
                    logging.error(f"Background task error: {e}")
                    time.sleep(10)
        
        def cleanup_disconnected_clients():
            """تنظيف العملاء المنقطعين"""
            while True:
                try:
                    current_time = datetime.now()
                    disconnected_clients = []
                    
                    for client_id, client_info in self.connected_clients.items():
                        last_ping = client_info.get('last_ping', client_info['connected_at'])
                        if (current_time - last_ping).total_seconds() > 60:  # 60 ثانية timeout
                            disconnected_clients.append(client_id)
                    
                    for client_id in disconnected_clients:
                        del self.connected_clients[client_id]
                        logging.info(f"Cleaned up disconnected client {client_id}")
                    
                    time.sleep(30)  # تنظيف كل 30 ثانية
                    
                except Exception as e:
                    logging.error(f"Cleanup task error: {e}")
                    time.sleep(60)
        
        # بدء المهام في threads منفصلة
        update_thread = threading.Thread(target=periodic_updates, daemon=True)
        cleanup_thread = threading.Thread(target=cleanup_disconnected_clients, daemon=True)
        
        update_thread.start()
        cleanup_thread.start()
        
        logging.info("Background tasks started")
    
    def broadcast_event(self, event_type: str, data: dict, room: str = None):
        """بث حدث لجميع العملاء أو غرفة محددة"""
        try:
            event_data = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            if room:
                self.socketio.emit('event', event_data, room=room)
            else:
                self.socketio.emit('event', event_data)
                
            logging.info(f"Broadcasted event {event_type} to {room or 'all clients'}")
            
        except Exception as e:
            logging.error(f"Broadcast error: {e}")
    
    def notify_vnc_change(self, action: str, success: bool, details: dict = None):
        """إشعار بتغيير في VNC"""
        self.broadcast_event('vnc_change', {
            'action': action,
            'success': success,
            'details': details or {},
            'message': f'VNC {action} {"نجح" if success else "فشل"}'
        }, room='vnc')
    
    def notify_system_alert(self, alert_type: str, message: str, severity: str = 'info'):
        """إشعار بتنبيه النظام"""
        self.broadcast_event('system_alert', {
            'alert_type': alert_type,
            'message': message,
            'severity': severity
        }, room='system')
    
    def get_connected_clients_count(self) -> int:
        """عدد العملاء المتصلين"""
        return len(self.connected_clients)
    
    def get_client_stats(self) -> dict:
        """إحصائيات العملاء"""
        return {
            'connected_count': len(self.connected_clients),
            'clients': {
                client_id: {
                    'connected_at': info['connected_at'].isoformat(),
                    'last_ping': info['last_ping'].isoformat(),
                    'subscriptions': list(info['subscriptions'])
                }
                for client_id, info in self.connected_clients.items()
            }
        }

# مثيل عام لـ WebSocket
websocket_manager = WebSocketManager()

def init_websocket(app: Flask):
    """تهيئة WebSocket مع Flask"""
    websocket_manager.init_app(app)
    return websocket_manager.socketio