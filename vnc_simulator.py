#!/usr/bin/env python3
import socket
import threading
import time
import struct
import os

class AdvancedVNCSimulator:
    def __init__(self, port=5900):
        self.port = port
        self.running = False
        self.clients = []
        
    def rfb_send_string(self, sock, msg):
        """إرسال نص بتنسيق RFB"""
        sock.send(struct.pack('>I', len(msg)))
        sock.send(msg.encode('utf-8'))
    
    def handle_client(self, client_socket, addr):
        """التعامل مع عميل VNC"""
        try:
            print(f"VNC client connected from {addr}")
            
            # إرسال إصدار البروتوكول
            client_socket.send(b'RFB 003.008\n')
            
            # استقبال إصدار العميل
            client_version = client_socket.recv(12)
            print(f"Client version: {client_version}")
            
            # إرسال أنواع الأمان المدعومة
            security_types = struct.pack('B', 1)  # عدد الأنواع
            security_types += struct.pack('B', 1)  # نوع None (بدون كلمة مرور)
            client_socket.send(security_types)
            
            # استقبال اختيار نوع الأمان
            chosen_security = client_socket.recv(1)
            
            # إرسال نتيجة الأمان (نجح)
            client_socket.send(struct.pack('>I', 0))
            
            # استقبال رسالة ClientInit
            client_init = client_socket.recv(1)
            
            # إرسال ServerInit
            # أبعاد الشاشة
            width, height = 1024, 768
            server_init = struct.pack('>HH', width, height)
            
            # تنسيق البكسل
            pixel_format = struct.pack('>BBBBHHHBBB',
                32,  # bits-per-pixel
                24,  # depth
                0,   # big-endian-flag
                1,   # true-colour-flag
                255, # red-max
                255, # green-max
                255, # blue-max
                16,  # red-shift
                8,   # green-shift
                0    # blue-shift
            )
            server_init += pixel_format
            server_init += b'\x00\x00\x00'  # padding
            
            # اسم سطح المكتب
            desktop_name = "Ubuntu Desktop Demo"
            server_init += struct.pack('>I', len(desktop_name))
            server_init += desktop_name.encode('utf-8')
            
            client_socket.send(server_init)
            
            # إرسال إطار أولي (شاشة زرقاء مع نص)
            self.send_initial_frame(client_socket, width, height)
            
            # الحفاظ على الاتصال
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    # معالجة رسائل العميل هنا
                    self.handle_client_message(client_socket, data, width, height)
                except:
                    break
                    
        except Exception as e:
            print(f"خطأ في التعامل مع العميل: {e}")
        finally:
            client_socket.close()
            print(f"Client {addr} disconnected")
    
    def send_initial_frame(self, client_socket, width, height):
        """إرسال إطار أولي يحتوي على نص ترحيبي"""
        try:
            # إنشاء صورة بسيطة (شاشة زرقاء مع مربعات)
            frame_data = b''
            for y in range(height):
                for x in range(width):
                    # إنشاء نمط لوني بسيط
                    if (x // 50 + y // 50) % 2 == 0:
                        # أزرق فاتح
                        pixel = struct.pack('>I', 0x4A90E2FF)[:3]
                    else:
                        # أزرق داكن
                        pixel = struct.pack('>I', 0x2E5F99FF)[:3]
                    frame_data += pixel + b'\x00'  # إضافة بايت رابع
            
            # إرسال FramebufferUpdate
            message_type = 0  # FramebufferUpdate
            padding = 0
            num_rectangles = 1
            
            header = struct.pack('>BBHH', 
                message_type, 
                padding, 
                num_rectangles,
                0  # padding إضافي
            )
            
            # مستطيل البيانات
            rect_header = struct.pack('>HHHHI',
                0,      # x-position
                0,      # y-position  
                width,  # width
                height, # height
                0       # encoding-type (Raw)
            )
            
            client_socket.send(header + rect_header + frame_data)
            
        except Exception as e:
            print(f"خطأ في إرسال الإطار: {e}")
    
    def handle_client_message(self, client_socket, data, width, height):
        """معالجة رسائل العميل"""
        if len(data) == 0:
            return
            
        msg_type = data[0]
        
        if msg_type == 2:  # SetEncodings
            print("Received SetEncodings")
        elif msg_type == 3:  # FramebufferUpdateRequest
            print("Received FramebufferUpdateRequest")
            # إرسال تحديث مبسط
            self.send_simple_update(client_socket, width, height)
        elif msg_type == 4:  # KeyEvent
            print("Received KeyEvent")
        elif msg_type == 5:  # PointerEvent
            print("Received PointerEvent")
    
    def send_simple_update(self, client_socket, width, height):
        """إرسال تحديث بسيط للشاشة"""
        try:
            # إرسال مستطيل صغير بلون مختلف
            import random
            color = random.randint(0, 0xFFFFFF)
            
            message_type = 0
            num_rectangles = 1
            
            header = struct.pack('>BBH', message_type, 0, num_rectangles)
            
            # مستطيل صغير في موقع عشوائي
            x = random.randint(0, width - 100)
            y = random.randint(0, height - 100)
            w, h = 100, 100
            
            rect_header = struct.pack('>HHHHI', x, y, w, h, 0)
            
            # بيانات المستطيل
            pixel_data = b''
            for _ in range(w * h):
                pixel_data += struct.pack('>I', color)[:3] + b'\x00'
            
            client_socket.send(header + rect_header + pixel_data)
            
        except Exception as e:
            print(f"خطأ في إرسال التحديث: {e}")
    
    def start(self):
        """بدء تشغيل الخادم"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f'VNC Simulator بدأ على المنفذ {self.port}')
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
            except:
                break
    
    def stop(self):
        """إيقاف الخادم"""
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()

if __name__ == "__main__":
    server = AdvancedVNCSimulator()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nإيقاف VNC Simulator...")
        server.stop()
