#!/usr/bin/env python3
"""
VNC Status Checker - فحص حالة خادم VNC
"""
import socket
import subprocess
import os

def check_vnc_status():
    """فحص حالة خادم VNC"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('127.0.0.1', 5900))
            return result == 0
    except:
        return False

def get_vnc_processes():
    """الحصول على عمليات VNC"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = []
        for line in result.stdout.split('\n'):
            if any(proc in line for proc in ['x11vnc', 'Xvfb', 'vnc']):
                lines.append(line.strip())
        return lines
    except:
        return []

def get_connection_info():
    """معلومات الاتصال"""
    repl_url = os.getenv('REPLIT_URL', 'localhost')
    if 'http' in repl_url:
        repl_url = repl_url.replace('https://', '').replace('http://', '')
    
    return {
        'host': repl_url,
        'port': 5900,
        'password': 'vnc123456',
        'resolution': '1024x768'
    }

def main():
    print("VNC Server Status Check")
    print("="*40)
    
    # فحص حالة VNC
    if check_vnc_status():
        print("✅ VNC Server is RUNNING")
        
        # معلومات الاتصال
        info = get_connection_info()
        print(f"🔗 Host: {info['host']}")
        print(f"🔌 Port: {info['port']}")
        print(f"🔑 Password: {info['password']}")
        print(f"📺 Resolution: {info['resolution']}")
        
        # العمليات النشطة
        processes = get_vnc_processes()
        if processes:
            print("\n🔄 Active Processes:")
            for proc in processes:
                print(f"   {proc}")
        
        print("\n✨ VNC Server is visible in Networking tab")
        
    else:
        print("❌ VNC Server is NOT running")
        print("Run: python3 vnc_networking.py")
    
    print("="*40)

if __name__ == "__main__":
    main()