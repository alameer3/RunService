#!/usr/bin/env python3
"""
VNC Server optimized for Replit Networking Tab
تشغيل خادم VNC بحيث يظهر في تبويب الشبكة
"""
import subprocess
import sys
import time
import socket
import os

def is_port_available(port):
    """فحص توفر المنفذ"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except:
        return False

def main():
    VNC_PORT = 5901
    
    print("🚀 Starting VNC Server for Replit Networking...")
    
    # فحص توفر المنفذ
    if not is_port_available(VNC_PORT):
        print(f"❌ Port {VNC_PORT} is already in use")
        # محاولة إيقاف العمليات السابقة
        subprocess.run(["pkill", "-f", "x11vnc"], capture_output=True)
        subprocess.run(["pkill", "-f", "Xvfb"], capture_output=True)
        time.sleep(2)
    
    # تشغيل الخادم
    try:
        result = subprocess.run([
            sys.executable, 'vnc_server_direct.py'
        ], timeout=None)
        
        if result.returncode == 0:
            print("✅ VNC Server started successfully")
        else:
            print("❌ VNC Server failed to start")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down VNC Server...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()