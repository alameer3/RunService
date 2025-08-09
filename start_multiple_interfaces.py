#!/usr/bin/env python3
"""
Start Multiple VNC Interfaces - تشغيل واجهات VNC متعددة
ينشئ خوادم VNC متعددة على منافذ مختلفة لنفس الشاشة
"""

import os
import sys
import subprocess
import time
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_xvfb_running():
    """التأكد من تشغيل Xvfb"""
    logger.info("🖥️ التحقق من الشاشة الافتراضية...")
    
    # فحص إذا كان Xvfb يعمل
    result = subprocess.run(["pgrep", "-f", "Xvfb"], capture_output=True)
    
    if result.returncode == 0:
        logger.info("✅ Xvfb يعمل بالفعل")
        return True
    
    # تشغيل Xvfb جديد
    try:
        logger.info("🚀 تشغيل شاشة افتراضية جديدة...")
        
        cmd = [
            "Xvfb", ":1",
            "-screen", "0", "1024x768x24",
            "-ac", "+extension", "GLX"
        ]
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # إعداد متغير البيئة
        os.environ["DISPLAY"] = ":1"
        
        logger.info("✅ تم تشغيل Xvfb بنجاح")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل في تشغيل Xvfb: {e}")
        return False

def start_vnc_server(port, server_name, extra_params=[]):
    """تشغيل خادم VNC على منفذ محدد"""
    logger.info(f"🚀 تشغيل {server_name} على المنفذ {port}...")
    
    try:
        # إيقاف أي خدمة VNC موجودة على نفس المنفذ
        subprocess.run(["pkill", "-f", f"rfbport {port}"], capture_output=True)
        time.sleep(1)
        
        # بناء أمر تشغيل VNC
        cmd = [
            "x11vnc",
            "-display", ":1", 
            "-rfbport", str(port),
            "-passwd", "vnc123456",
            "-forever",
            "-shared", 
            "-noxdamage",
            "-noxfixes",
            "-noscr"
        ] + extra_params + ["-bg"]
        
        # تشغيل الأمر
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # انتظار بدء التشغيل
        time.sleep(2)
        
        # فحص نجاح التشغيل
        check_result = subprocess.run(
            ["pgrep", "-f", f"rfbport {port}"], 
            capture_output=True
        )
        
        if check_result.returncode == 0:
            logger.info(f"✅ {server_name} يعمل بنجاح على المنفذ {port}")
            return True
        else:
            logger.error(f"❌ فشل في تشغيل {server_name} على المنفذ {port}")
            if result.stderr:
                logger.error(f"خطأ: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل {server_name}: {e}")
        return False

def setup_vnc_password():
    """إعداد كلمة مرور VNC"""
    try:
        # إنشاء مجلد .vnc
        vnc_dir = os.path.expanduser("~/.vnc")
        os.makedirs(vnc_dir, exist_ok=True)
        
        # إعداد ملف كلمة المرور
        passwd_cmd = ["x11vnc", "-storepasswd", "vnc123456", f"{vnc_dir}/passwd"]
        subprocess.run(passwd_cmd, capture_output=True)
        
        logger.info("✅ تم إعداد كلمة مرور VNC")
        return True
        
    except Exception as e:
        logger.error(f"❌ فشل في إعداد كلمة مرور VNC: {e}")
        return False

def start_desktop_apps():
    """تشغيل تطبيقات سطح المكتب الأساسية"""
    logger.info("📱 تشغيل تطبيقات سطح المكتب...")
    
    apps = [
        # مدير النوافذ البسيط
        ["openbox", "--config-file", "/dev/null"],
        
        # محطات طرفية
        ["xterm", "-geometry", "80x24+10+10", "-title", "Terminal 1"],
        ["xterm", "-geometry", "80x24+500+10", "-title", "Terminal 2"],
        
        # متصفحات
        ["firefox-esr", "--new-instance"],
        ["chromium", "--no-sandbox", "--disable-gpu"]
    ]
    
    launched = 0
    for app in apps:
        try:
            subprocess.Popen(
                app,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=dict(os.environ, DISPLAY=":1")
            )
            logger.info(f"✅ تم تشغيل {app[0]}")
            launched += 1
            time.sleep(1)
        except FileNotFoundError:
            logger.warning(f"⚠️ التطبيق غير موجود: {app[0]}")
        except Exception as e:
            logger.warning(f"⚠️ فشل في تشغيل {app[0]}: {e}")
    
    logger.info(f"✅ تم تشغيل {launched}/{len(apps)} تطبيقات")

def main():
    """البرنامج الرئيسي"""
    logger.info("🚀 بدء تشغيل واجهات VNC متعددة...")
    
    # إعداد كلمة المرور
    if not setup_vnc_password():
        sys.exit(1)
    
    # التأكد من تشغيل الشاشة الافتراضية
    if not ensure_xvfb_running():
        logger.error("❌ فشل في تشغيل الشاشة الافتراضية")
        sys.exit(1)
    
    # تشغيل التطبيقات الأساسية
    start_desktop_apps()
    
    # تشغيل خوادم VNC المتعددة
    vnc_configs = [
        (5900, "الواجهة الرئيسية", []),
        (5901, "واجهة الويب", ["-http"]),
        (5902, "واجهة الموبايل", ["-scale", "0.8"]),
        (5903, "واجهة المراقبة", ["-viewonly"])
    ]
    
    successful_servers = 0
    for port, name, extra_params in vnc_configs:
        if start_vnc_server(port, name, extra_params):
            successful_servers += 1
    
    if successful_servers == 0:
        logger.error("❌ فشل في تشغيل أي خادم VNC")
        sys.exit(1)
    
    # طباعة معلومات الاتصال
    logger.info("\n" + "="*60)
    logger.info("🎯 تم تشغيل النظام بنجاح!")
    logger.info("="*60)
    logger.info("📡 معلومات الاتصال:")
    
    for port, name, _ in vnc_configs:
        # فحص حالة الخادم
        check_result = subprocess.run(
            ["pgrep", "-f", f"rfbport {port}"], 
            capture_output=True
        )
        
        status = "✅ يعمل" if check_result.returncode == 0 else "❌ متوقف"
        logger.info(f"  {name}: localhost:{port} - {status}")
    
    logger.info(f"🔑 كلمة المرور: vnc123456")
    logger.info("="*60)
    
    logger.info(f"✅ تم تشغيل {successful_servers}/{len(vnc_configs)} واجهات بنجاح")
    
    # بدء مراقبة الخدمات
    try:
        while True:
            time.sleep(30)
            
            # فحص دوري للخدمات
            running_count = 0
            for port, name, extra_params in vnc_configs:
                check_result = subprocess.run(
                    ["pgrep", "-f", f"rfbport {port}"], 
                    capture_output=True
                )
                
                if check_result.returncode == 0:
                    running_count += 1
                else:
                    logger.warning(f"⚠️ إعادة تشغيل {name} على المنفذ {port}")
                    start_vnc_server(port, name, extra_params)
            
            logger.info(f"📊 الحالة: {running_count}/{len(vnc_configs)} خوادم تعمل")
            
    except KeyboardInterrupt:
        logger.info("🛑 تم استلام إشارة الإيقاف...")
        
        # إيقاف جميع خوادم VNC
        logger.info("إيقاف خوادم VNC...")
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        
        logger.info("✅ تم إيقاف جميع الخدمات")
        
    except Exception as e:
        logger.error(f"❌ خطأ عام: {e}")
        # إيقاف الخدمات في حالة الخطأ
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        sys.exit(1)

if __name__ == "__main__":
    main()