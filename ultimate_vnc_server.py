#!/usr/bin/env python3
"""
خادم VNC محاكي متكامل مع عرض بصري حقيقي
"""
import socket
import threading
import time
import struct
import random
import sys
import logging

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vnc_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UltimateVNCServer:
    def __init__(self, port=5900, width=1024, height=768):
        self.port = port
        self.width = width
        self.height = height
        self.running = False
        self.clients = []
        self.framebuffer = self.create_initial_desktop()
        logger.info(f"إنشاء خادم VNC على المنفذ {port} بدقة {width}x{height}")
        
    def create_initial_desktop(self):
        """إنشاء سطح مكتب أولي جذاب"""
        logger.info("إنشاء سطح المكتب الأولي...")
        framebuffer = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # إنشاء تدرج لوني جميل
                if y < 50:  # شريط علوي
                    pixel = self.rgb_to_pixel(52, 73, 94)  # رمادي داكن
                elif y > self.height - 50:  # شريط سفلي (taskbar)
                    pixel = self.rgb_to_pixel(44, 62, 80)  # أزرق داكن
                else:  # المنطقة الرئيسية
                    # تدرج من الأزرق إلى البنفسجي
                    blue_ratio = (self.height - y) / self.height
                    purple_ratio = y / self.height
                    
                    r = int(52 + purple_ratio * 100)
                    g = int(152 - purple_ratio * 50)
                    b = int(219 - blue_ratio * 50)
                    
                    # إضافة نمط للنوافذ
                    if 100 < x < 400 and 100 < y < 300:  # نافذة 1
                        if y < 130:  # شريط العنوان
                            pixel = self.rgb_to_pixel(41, 128, 185)
                        else:  # محتوى النافذة
                            pixel = self.rgb_to_pixel(236, 240, 241)
                    elif 500 < x < 800 and 200 < y < 400:  # نافذة 2
                        if y < 230:  # شريط العنوان
                            pixel = self.rgb_to_pixel(231, 76, 60)
                        else:  # محتوى النافذة
                            pixel = self.rgb_to_pixel(46, 204, 113)
                    else:
                        pixel = self.rgb_to_pixel(r, g, b)
                
                row.append(pixel)
            framebuffer.append(row)
        
        # إضافة أيقونات على سطح المكتب
        self.add_desktop_icons(framebuffer)
        logger.info("تم إنشاء سطح المكتب بنجاح")
        return framebuffer
    
    def add_desktop_icons(self, framebuffer):
        """إضافة أيقونات سطح المكتب"""
        icons = [
            (50, 80, "📁"),   # مجلد
            (150, 80, "🌐"),  # متصفح
            (250, 80, "⚙️"),   # إعدادات
            (350, 80, "📝"),  # محرر نصوص
        ]
        
        for x, y, icon in icons:
            self.draw_icon(framebuffer, x, y, icon)
    
    def draw_icon(self, framebuffer, x, y, icon_char):
        """رسم أيقونة على سطح المكتب"""
        # رسم خلفية الأيقونة
        for dy in range(-20, 21):
            for dx in range(-20, 21):
                if 0 <= x + dx < self.width and 0 <= y + dy < self.height:
                    if dx*dx + dy*dy <= 400:  # دائرة
                        framebuffer[y + dy][x + dx] = self.rgb_to_pixel(255, 255, 255)
    
    def rgb_to_pixel(self, r, g, b):
        """تحويل RGB إلى تنسيق البكسل"""
        return (r << 16) | (g << 8) | b
    
    def pixel_to_bytes(self, pixel):
        """تحويل البكسل إلى بايتات"""
        return struct.pack('>I', pixel)
    
    def handle_client(self, client_socket, addr):
        """التعامل مع عميل VNC"""
        logger.info(f"عميل VNC متصل من {addr}")
        
        try:
            # 1. Protocol Version Handshake
            client_socket.send(b'RFB 003.008\n')
            client_version = client_socket.recv(12)
            logger.info(f"إصدار العميل: {client_version.decode().strip()}")
            
            # 2. Security Handshake
            # إرسال أنواع الأمان المدعومة
            security_types = struct.pack('B', 1)  # عدد الأنواع
            security_types += struct.pack('B', 1)  # نوع None
            client_socket.send(security_types)
            
            # استقبال اختيار العميل
            chosen_security = client_socket.recv(1)
            
            # إرسال نتيجة الأمان
            client_socket.send(struct.pack('>I', 0))  # نجح
            
            # 3. Client Initialization
            client_init = client_socket.recv(1)
            shared_flag = client_init[0] if client_init else 0
            logger.info(f"مشاركة الشاشة: {'نعم' if shared_flag else 'لا'}")
            
            # 4. Server Initialization
            self.send_server_init(client_socket)
            
            # 5. Normal Protocol Messages
            self.handle_normal_protocol(client_socket, addr)
            
        except Exception as e:
            logger.error(f"خطأ مع العميل {addr}: {e}")
        finally:
            client_socket.close()
            logger.info(f"انقطع الاتصال مع العميل {addr}")
    
    def send_server_init(self, client_socket):
        """إرسال رسالة Server Initialization"""
        logger.info("إرسال معلومات الخادم للعميل")
        
        # أبعاد الشاشة
        server_init = struct.pack('>HH', self.width, self.height)
        
        # تنسيق البكسل
        pixel_format = struct.pack('>BBBBHHHBBBX',
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
        
        # اسم سطح المكتب
        desktop_name = "Ubuntu Desktop في المتصفح - يعمل بواسطة Python"
        server_init += struct.pack('>I', len(desktop_name))
        server_init += desktop_name.encode('utf-8')
        
        client_socket.send(server_init)
        logger.info("تم إرسال معلومات الخادم")
    
    def handle_normal_protocol(self, client_socket, addr):
        """التعامل مع الرسائل العادية"""
        logger.info(f"بدء البروتوكول العادي مع {addr}")
        
        # إرسال الإطار الأولي
        self.send_framebuffer_update(client_socket, full_update=True)
        
        while self.running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                self.process_client_message(client_socket, data, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"خطأ في معالجة الرسالة من {addr}: {e}")
                break
    
    def process_client_message(self, client_socket, data, addr):
        """معالجة رسائل العميل"""
        if len(data) == 0:
            return
        
        msg_type = data[0]
        
        if msg_type == 0:  # SetPixelFormat
            logger.info(f"{addr}: تغيير تنسيق البكسل")
            
        elif msg_type == 2:  # SetEncodings
            num_encodings = struct.unpack('>H', data[2:4])[0]
            logger.info(f"{addr}: تعيين {num_encodings} ترميز")
            
        elif msg_type == 3:  # FramebufferUpdateRequest
            incremental = data[1]
            x, y, w, h = struct.unpack('>HHHH', data[2:10])
            logger.info(f"{addr}: طلب تحديث {'تزايدي' if incremental else 'كامل'}")
            
            # إرسال تحديث
            if incremental:
                self.send_partial_update(client_socket, x, y, w, h)
            else:
                self.send_framebuffer_update(client_socket, full_update=True)
                
        elif msg_type == 4:  # KeyEvent
            down_flag = data[1]
            key = struct.unpack('>I', data[4:8])[0]
            logger.info(f"{addr}: مفتاح {'مضغوط' if down_flag else 'مرفوع'}: {key}")
            
            # تحديث الشاشة عند الكتابة
            self.animate_keypress(client_socket, key)
            
        elif msg_type == 5:  # PointerEvent
            button_mask = data[1]
            x, y = struct.unpack('>HH', data[2:6])
            logger.info(f"{addr}: نقر فأرة في ({x}, {y}) أزرار: {button_mask}")
            
            # تحديث الشاشة عند النقر
            self.animate_mouse_click(client_socket, x, y, button_mask)
    
    def send_framebuffer_update(self, client_socket, full_update=False):
        """إرسال تحديث كامل للشاشة"""
        logger.info("إرسال تحديث الشاشة...")
        
        # رأس الرسالة
        header = struct.pack('>BBH', 0, 0, 1)  # FramebufferUpdate, padding, 1 rectangle
        
        # رأس المستطيل
        rect_header = struct.pack('>HHHHI', 0, 0, self.width, self.height, 0)  # Raw encoding
        
        # بيانات البكسلات
        pixel_data = b''
        for row in self.framebuffer:
            for pixel in row:
                pixel_data += self.pixel_to_bytes(pixel)
        
        try:
            client_socket.send(header + rect_header + pixel_data)
            logger.info("تم إرسال تحديث الشاشة بنجاح")
        except Exception as e:
            logger.error(f"خطأ في إرسال تحديث الشاشة: {e}")
    
    def send_partial_update(self, client_socket, x, y, w, h):
        """إرسال تحديث جزئي"""
        # إنشاء تحديث بصري بسيط
        header = struct.pack('>BBH', 0, 0, 1)
        rect_header = struct.pack('>HHHHI', x, y, min(w, 100), min(h, 100), 0)
        
        # إنشاء بكسلات عشوائية ملونة
        pixel_data = b''
        for _ in range(min(w, 100) * min(h, 100)):
            color = random.randint(0, 0xFFFFFF)
            pixel_data += self.pixel_to_bytes(color)
        
        try:
            client_socket.send(header + rect_header + pixel_data)
        except Exception as e:
            logger.error(f"خطأ في إرسال التحديث الجزئي: {e}")
    
    def animate_keypress(self, client_socket, key):
        """تحريك عند الضغط على مفتاح"""
        # إنشاء تأثير بصري للكتابة
        x = random.randint(100, self.width - 100)
        y = random.randint(100, self.height - 100)
        
        header = struct.pack('>BBH', 0, 0, 1)
        rect_header = struct.pack('>HHHHI', x, y, 50, 20, 0)
        
        # لون مختلف للمفاتيح
        color = 0x00FF00 if key < 128 else 0xFF0000
        pixel_data = self.pixel_to_bytes(color) * (50 * 20)
        
        try:
            client_socket.send(header + rect_header + pixel_data)
            logger.info(f"تأثير بصري للمفتاح {key}")
        except:
            pass
    
    def animate_mouse_click(self, client_socket, x, y, button_mask):
        """تحريك عند النقر بالفأرة"""
        if button_mask & 1:  # زر أيسر
            # رسم دائرة حول موقع النقر
            header = struct.pack('>BBH', 0, 0, 1)
            rect_header = struct.pack('>HHHHI', max(0, x-25), max(0, y-25), 50, 50, 0)
            
            # لون أحمر للنقر
            pixel_data = self.pixel_to_bytes(0xFF0000) * (50 * 50)
            
            try:
                client_socket.send(header + rect_header + pixel_data)
                logger.info(f"تأثير بصري للنقر في ({x}, {y})")
                
                # إرسال تأثير ثاني بعد وقت قصير
                time.sleep(0.1)
                pixel_data = self.pixel_to_bytes(0x00FF00) * (50 * 50)
                client_socket.send(header + rect_header + pixel_data)
                
            except:
                pass
    
    def start(self):
        """بدء تشغيل الخادم"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"خادم VNC المتكامل يعمل على المنفذ {self.port}")
            logger.info(f"دقة الشاشة: {self.width}x{self.height}")
            logger.info("في انتظار اتصالات العملاء...")
            
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
                    break
                    
        except Exception as e:
            logger.error(f"خطأ في بدء الخادم: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """إيقاف الخادم"""
        logger.info("إيقاف خادم VNC...")
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()

if __name__ == "__main__":
    # إنشاء مجلد السجلات
    import os
    os.makedirs('logs', exist_ok=True)
    
    server = UltimateVNCServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم بواسطة المستخدم")
        server.stop()