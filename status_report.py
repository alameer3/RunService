#!/usr/bin/env python3
"""
Status Report - تقرير حالة نظام VNC متعدد الواجهات
"""

import subprocess
import sys

def check_vnc_status():
    """فحص حالة خوادم VNC"""
    print("🔍 فحص حالة خوادم VNC...")
    print("="*60)
    
    interfaces = [
        (5900, "الواجهة الرئيسية"),
        (5901, "واجهة الويب"), 
        (5902, "واجهة الموبايل"),
        (5903, "واجهة المراقبة")
    ]
    
    running_count = 0
    
    for port, description in interfaces:
        # فحص وجود عملية VNC على المنفذ
        result = subprocess.run([
            "pgrep", "-f", f"rfbport {port}"
        ], capture_output=True)
        
        status = "✅ يعمل" if result.returncode == 0 else "❌ متوقف"
        print(f"  {description} (:{port}) - {status}")
        
        if result.returncode == 0:
            running_count += 1
    
    print("="*60)
    print(f"📊 الإجمالي: {running_count}/{len(interfaces)} واجهات تعمل")
    
    # فحص الشاشة الافتراضية
    xvfb_result = subprocess.run([
        "pgrep", "-f", "Xvfb"
    ], capture_output=True)
    
    xvfb_status = "✅ يعمل" if xvfb_result.returncode == 0 else "❌ متوقف"
    print(f"🖥️ الشاشة الافتراضية (Xvfb) - {xvfb_status}")
    
    # معلومات إضافية
    print("\n📋 معلومات الاتصال:")
    print("🔑 كلمة المرور: vnc123456")
    print("🖥️ العرض: :1")
    print("📱 التطبيقات: Firefox, Chromium, XTerm")
    
    if running_count > 0:
        print(f"\n🎯 النظام جاهز! يمكن الاتصال عبر VNC Viewer إلى أي من المنافذ المتاحة.")
        return True
    else:
        print(f"\n❌ لا توجد خوادم VNC تعمل!")
        return False

def main():
    return check_vnc_status()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)