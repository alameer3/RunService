#!/usr/bin/env python3
"""
VNC Solution for Replit Environment
حل VNC محسن لبيئة Replit
"""
import os
import sys
import time
import subprocess
import socket
from pathlib import Path

def setup_environment():
    """إعداد البيئة لـ Replit"""
    print("🔧 Setting up Replit environment...")
    
    # Set environment variables for Replit
    os.environ['DISPLAY'] = ':1'
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
    
    # Create necessary directories
    home_dir = Path.home()
    vnc_dir = home_dir / ".vnc"
    vnc_dir.mkdir(exist_ok=True)
    
    return True

def setup_vnc_password():
    """إعداد كلمة مرور VNC مبسطة"""
    print("🔑 Setting up VNC password...")
    
    vnc_dir = Path.home() / ".vnc"
    passwd_file = vnc_dir / "passwd"
    
    try:
        # Create password using x11vnc
        result = subprocess.run([
            'x11vnc', '-storepasswd', 'vnc123456', str(passwd_file)
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            os.chmod(passwd_file, 0o600)
            print("✅ VNC password set successfully")
            return True
        else:
            print(f"❌ Password setup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Password setup error: {e}")
        return False

def start_xvfb_simple():
    """تشغيل Xvfb مبسط"""
    print("🖥️ Starting Xvfb...")
    
    try:
        # Kill any existing Xvfb on display :1
        subprocess.run(['pkill', '-f', 'Xvfb.*:1'], capture_output=True)
        time.sleep(1)
        
        # Start Xvfb with minimal options
        xvfb_cmd = [
            'Xvfb', ':1',
            '-screen', '0', '1024x768x24',
            '-ac',
            '+extension', 'GLX',
            '+render',
            '-noreset'
        ]
        
        proc = subprocess.Popen(
            xvfb_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait and check if it started
        time.sleep(3)
        
        if proc.poll() is None:
            print("✅ Xvfb started successfully")
            return proc
        else:
            print("❌ Xvfb failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Xvfb error: {e}")
        return None

def start_vnc_simple():
    """تشغيل x11vnc مبسط"""
    print("🔌 Starting x11vnc...")
    
    passwd_file = Path.home() / ".vnc" / "passwd"
    
    try:
        # Kill any existing x11vnc
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        time.sleep(1)
        
        # Build x11vnc command
        vnc_cmd = [
            'x11vnc',
            '-display', ':1',
            '-rfbport', '5900',
            '-shared',
            '-forever',
            '-noxdamage',
            '-noxfixes',
            '-noxrandr',
            '-wait', '10',
            '-defer', '10'
        ]
        
        # Add password if exists
        if passwd_file.exists():
            vnc_cmd.extend(['-rfbauth', str(passwd_file)])
        else:
            vnc_cmd.append('-nopw')
        
        print(f"Starting: {' '.join(vnc_cmd)}")
        
        proc = subprocess.Popen(
            vnc_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Wait and check
        time.sleep(5)
        
        if proc.poll() is None:
            print("✅ x11vnc started successfully")
            return proc
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ x11vnc failed: {stderr.decode()[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ x11vnc error: {e}")
        return None

def check_port(port=5900):
    """فحص المنفذ"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def start_window_manager():
    """تشغيل مدير النوافذ"""
    print("🪟 Starting window manager...")
    
    try:
        env = os.environ.copy()
        env['DISPLAY'] = ':1'
        
        # Try openbox first
        proc = subprocess.Popen(
            ['openbox'],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        time.sleep(2)
        
        if proc.poll() is None:
            print("✅ Openbox started")
            return proc
        else:
            print("⚠️ Openbox failed, using twm fallback")
            # Fallback to twm
            proc = subprocess.Popen(
                ['twm'],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(2)
            return proc
            
    except Exception as e:
        print(f"❌ Window manager error: {e}")
        return None

def main():
    """الوظيفة الرئيسية"""
    print("🚀 VNC Replit Solution Starting...")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Setup password
    if not setup_vnc_password():
        print("⚠️ Password setup failed, continuing without password")
    
    # Start Xvfb
    xvfb_proc = start_xvfb_simple()
    if not xvfb_proc:
        print("❌ Cannot start Xvfb")
        sys.exit(1)
    
    # Start window manager
    wm_proc = start_window_manager()
    
    # Start VNC
    vnc_proc = start_vnc_simple()
    if not vnc_proc:
        print("❌ Cannot start VNC server")
        if xvfb_proc:
            xvfb_proc.terminate()
        sys.exit(1)
    
    # Verify port is open
    time.sleep(3)
    if check_port(5900):
        print("✅ VNC Server is running on port 5900")
        print("🔗 Connect with: localhost:5900")
        print("🔑 Password: vnc123456")
    else:
        print("❌ Port 5900 is not accessible")
    
    # Keep running
    try:
        print("\n🎯 VNC Server is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(30)
            
            # Check if processes are still running
            if vnc_proc.poll() is not None:
                print("⚠️ VNC process stopped")
                break
            if xvfb_proc.poll() is not None:
                print("⚠️ Xvfb process stopped")
                break
                
            # Print status
            if check_port(5900):
                print("📡 VNC Server is healthy")
            else:
                print("⚠️ VNC Server port not responding")
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    
    # Cleanup
    for proc in [vnc_proc, wm_proc, xvfb_proc]:
        if proc and proc.poll() is None:
            proc.terminate()
    
    print("✅ VNC Server stopped")

if __name__ == "__main__":
    main()