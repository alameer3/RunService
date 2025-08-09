#!/usr/bin/env python3
"""
VNC Workflow Script - for continuous VNC server operation
سكريبت تشغيل خادم VNC بشكل مستمر
"""
import os
import sys
import subprocess

def main():
    """تشغيل خادم VNC كـ workflow مستمر"""
    print("🚀 Starting VNC Workflow...")
    
    # تشغيل خادم VNC
    try:
        result = subprocess.call([sys.executable, 'vnc_networking.py'])
        if result != 0:
            print("VNC Server exited with error")
            sys.exit(1)
    except KeyboardInterrupt:
        print("VNC Server interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Error running VNC Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()