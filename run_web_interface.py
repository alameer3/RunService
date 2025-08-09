#!/usr/bin/env python3
"""
Web Interface Runner - تشغيل واجهة الويب على منفذ 8080
"""

import os
import sys
from web_vnc_interface import WebVNCInterface

def main():
    """تشغيل واجهة الويب"""
    print("🌐 تشغيل واجهة VNC Web على المنفذ 8080...")
    
    web_interface = WebVNCInterface()
    
    try:
        web_interface.run(host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        print("✅ تم إيقاف واجهة الويب")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()