#!/usr/bin/env python3
"""
خادم VNC بسيط يعمل على منفذ 8000 المدعوم في Replit
"""

import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)

class SimpleVNCServer:
    """خادم VNC بسيط للاتصال الخارجي"""
    
    def __init__(self, host='0.0.0.0', port=8000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.connections = []
        
    def start(self):
        """بدء خادم VNC"""
        try:
            if self.is_running:
                logger.info("خادم VNC يعمل بالفعل")
                return True
                
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            
            logger.info(f"🚀 خادم VNC يعمل على {self.host}:{self.port}")
            
            # بدء thread للاستماع للاتصالات
            listen_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            listen_thread.start()
            
            # انتظار قصير للتأكد من بدء الخادم
            import time
            time.sleep(0.5)
            
            return True
        except Exception as e:
            logger.error(f"خطأ في بدء خادم VNC: {e}")
            self.is_running = False
            return False
    
    def _listen_for_connections(self):
        """الاستماع للاتصالات الواردة"""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"🔗 اتصال جديد من {address}")
                
                # معالجة الاتصال في thread منفصل
                connection_thread = threading.Thread(
                    target=self._handle_connection, 
                    args=(client_socket, address),
                    daemon=True
                )
                connection_thread.start()
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"خطأ في قبول الاتصال: {e}")
    
    def _handle_connection(self, client_socket, address):
        """معالجة اتصال عميل"""
        try:
            self.connections.append(client_socket)
            
            # إرسال رسالة ترحيب VNC
            welcome_message = "RFB 003.008\n".encode('utf-8')
            client_socket.send(welcome_message)
            
            # الاستماع للرسائل من العميل
            while self.is_running:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # معالجة بيانات VNC هنا
                logger.info(f"📤 استلام بيانات من {address}: {len(data)} bytes")
                
                # إرسال رد (محاكاة VNC)
                response = b"VNC Server Response"
                client_socket.send(response)
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الاتصال {address}: {e}")
        finally:
            if client_socket in self.connections:
                self.connections.remove(client_socket)
            client_socket.close()
            logger.info(f"🔌 انتهى الاتصال مع {address}")
    
    def stop(self):
        """إيقاف خادم VNC"""
        try:
            self.is_running = False
            
            # إغلاق جميع الاتصالات
            for connection in self.connections:
                connection.close()
            self.connections.clear()
            
            # إغلاق server socket
            if self.server_socket:
                self.server_socket.close()
            
            logger.info("⏹️ تم إيقاف خادم VNC")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف خادم VNC: {e}")
            return False
    
    def get_status(self):
        """الحصول على حالة الخادم"""
        return {
            'is_running': self.is_running,
            'host': self.host,
            'port': self.port,
            'connections': len(self.connections)
        }

# مثيل مشترك للخادم
vnc_server = SimpleVNCServer()

def start_vnc_server():
    """بدء خادم VNC"""
    return vnc_server.start()

def stop_vnc_server():
    """إيقاف خادم VNC"""
    return vnc_server.stop()

def get_vnc_status():
    """الحصول على حالة خادم VNC"""
    return vnc_server.get_status()

if __name__ == "__main__":
    # تشغيل الخادم للاختبار
    logging.basicConfig(level=logging.INFO)
    server = SimpleVNCServer()
    server.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()