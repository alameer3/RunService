#!/usr/bin/env python3
"""
خادم VNC محسن مع إصلاح مشاكل البروتوكول
"""
import socket
import threading
import time
import struct
import random
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedVNCServer:
    def __init__(self, port=5900, width=1024, height=768):
        self.port = port
        self.width = width
        self.height = height
        self.running = False
        self.clients = []
        self.framebuffer = self.create_desktop()
        
    def create_desktop(self):
        """إنشاء سطح مكتب ملون"""
        framebuffer = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # إنشاء نمط ملون جميل
                r = int(100 + (x / self.width) * 155)
                g = int(100 + (y / self.height) * 155) 
                b = int(200 - ((x + y) / (self.width + self.height)) * 100)
                
                # إضافة نوافذ وأيقونات
                if 50 < x < 300 and 50 < y < 200:  # نافذة
                    if y < 80:  # شريط العنوان
                        pixel = (65, 131, 215)  # أزرق
                    else:
                        pixel = (240, 240, 240)  # أبيض
                elif 400 < x < 650 and 300 < y < 450:  # نافذة أخرى
                    if y < 330:
                        pixel = (220, 78, 65)   # أحمر
                    else:
                        pixel = (255, 255, 255)
                else:
                    pixel = (r, g, b)
                    
                row.append(pixel)
            framebuffer.append(row)
        return framebuffer
    
    def handle_client(self, client_socket, addr):
        """التعامل مع عميل VNC بطريقة محسنة"""
        logger.info(f"عميل VNC متصل من {addr}")
        
        try:
            # 1. إرسال إصدار الخادم
            client_socket.send(b'RFB 003.008\n')
            
            # 2. استقبال إصدار العميل
            client_version = client_socket.recv(12)
            if not client_version:
                return
            logger.info(f"إصدار العميل: {client_version.decode().strip()}")
            
            # 3. تبادل الأمان - بدون كلمة مرور
            client_socket.send(struct.pack('B', 1))  # عدد أنواع الأمان
            client_socket.send(struct.pack('B', 1))  # نوع None
            
            # 4. استقبال اختيار العميل
            security_choice = client_socket.recv(1)
            if not security_choice:
                return
                
            # 5. إرسال نتيجة الأمان (نجح)
            client_socket.send(struct.pack('>I', 0))
            
            # 6. استقبال ClientInit
            client_init = client_socket.recv(1)
            if not client_init:
                return
                
            # 7. إرسال ServerInit
            self.send_server_init(client_socket)
            
            # 8. البروتوكول العادي
            self.handle_messages(client_socket, addr)
            
        except Exception as e:
            logger.error(f"خطأ مع العميل {addr}: {e}")
        finally:
            client_socket.close()
            logger.info(f"انقطع الاتصال مع {addr}")
    
    def send_server_init(self, client_socket):
        """إرسال معلومات الخادم"""
        # أبعاد الشاشة
        init_msg = struct.pack('>HH', self.width, self.height)
        
        # تنسيق البكسل (RGB888)
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
        pixel_format += b'\x00' * 3  # padding
        
        init_msg += pixel_format
        
        # اسم سطح المكتب
        desktop_name = "Ubuntu Desktop - Replit VNC"
        init_msg += struct.pack('>I', len(desktop_name))
        init_msg += desktop_name.encode('utf-8')
        
        client_socket.send(init_msg)
        logger.info("تم إرسال معلومات الخادم")
    
    def handle_messages(self, client_socket, addr):
        """معالجة رسائل العميل"""
        # إرسال الإطار الأولي
        self.send_framebuffer_update(client_socket)
        
        while self.running:
            try:
                client_socket.settimeout(1.0)
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                self.process_message(client_socket, data)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"خطأ في الرسالة من {addr}: {e}")
                break
    
    def process_message(self, client_socket, data):
        """معالجة رسالة واحدة"""
        if len(data) == 0:
            return
            
        msg_type = data[0]
        
        if msg_type == 0:  # SetPixelFormat
            logger.debug("SetPixelFormat")
            
        elif msg_type == 2:  # SetEncodings
            logger.debug("SetEncodings")
            
        elif msg_type == 3:  # FramebufferUpdateRequest
            incremental = data[1]
            if not incremental:
                self.send_framebuffer_update(client_socket)
            else:
                self.send_small_update(client_socket)
                
        elif msg_type == 4:  # KeyEvent
            down_flag = data[1]
            if len(data) >= 8:
                key = struct.unpack('>I', data[4:8])[0]
                logger.info(f"مفتاح: {key} {'مضغوط' if down_flag else 'مرفوع'}")
                self.animate_keypress(client_socket)
                
        elif msg_type == 5:  # PointerEvent
            if len(data) >= 6:
                button_mask = data[1]
                x, y = struct.unpack('>HH', data[2:6])
                logger.info(f"فأرة: ({x}, {y}) أزرار: {button_mask}")
                self.animate_mouse_click(client_socket, x, y)
    
    def send_framebuffer_update(self, client_socket):
        """إرسال تحديث كامل للشاشة"""
        try:
            # رأس الرسالة
            header = struct.pack('>BBH', 0, 0, 1)  # type=0, padding=0, rectangles=1
            
            # رأس المستطيل
            rect_header = struct.pack('>HHHHI', 0, 0, self.width, self.height, 0)
            
            # بيانات البكسلات
            pixel_data = b''
            for row in self.framebuffer:
                for r, g, b in row:
                    pixel_data += struct.pack('>BBBB', b, g, r, 0)  # BGRA
                    
            client_socket.send(header + rect_header + pixel_data)
            logger.debug("تم إرسال تحديث الشاشة")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال التحديث: {e}")
    
    def send_small_update(self, client_socket):
        """إرسال تحديث صغير"""
        try:
            x = random.randint(0, self.width - 50)
            y = random.randint(0, self.height - 50)
            w, h = 50, 50
            
            header = struct.pack('>BBH', 0, 0, 1)
            rect_header = struct.pack('>HHHHI', x, y, w, h, 0)
            
            # بكسلات عشوائية
            pixel_data = b''
            for _ in range(w * h):
                r = random.randint(0, 255)
                g = random.randint(0, 255) 
                b = random.randint(0, 255)
                pixel_data += struct.pack('>BBBB', b, g, r, 0)
                
            client_socket.send(header + rect_header + pixel_data)
            
        except Exception as e:
            logger.error(f"خطأ في التحديث الصغير: {e}")
    
    def animate_keypress(self, client_socket):
        """تأثير بصري للكتابة"""
        self.send_colored_rect(client_socket, 
                              random.randint(0, self.width-100), 
                              random.randint(0, self.height-50),
                              100, 50, (0, 255, 0))
    
    def animate_mouse_click(self, client_socket, x, y):
        """تأثير بصري للنقر"""
        self.send_colored_rect(client_socket, 
                              max(0, x-25), max(0, y-25),
                              50, 50, (255, 0, 0))
    
    def send_colored_rect(self, client_socket, x, y, w, h, color):
        """إرسال مستطيل ملون"""
        try:
            header = struct.pack('>BBH', 0, 0, 1)
            rect_header = struct.pack('>HHHHI', x, y, w, h, 0)
            
            r, g, b = color
            pixel_data = struct.pack('>BBBB', b, g, r, 0) * (w * h)
            
            client_socket.send(header + rect_header + pixel_data)
            
        except:
            pass
    
    def start(self):
        """بدء الخادم"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"خادم VNC محسن يعمل على المنفذ {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"خطأ في قبول الاتصال: {e}")
                        
        except Exception as e:
            logger.error(f"خطأ في بدء الخادم: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """إيقاف الخادم"""
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()

if __name__ == "__main__":
    import os
    os.makedirs('logs', exist_ok=True)
    
    server = FixedVNCServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
        server.stop()