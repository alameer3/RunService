from app import app  # noqa: F401
import subprocess
import threading
import time
import os

def start_vnc_background():
    """Start VNC server in background thread"""
    def run_vnc():
        while True:
            try:
                print("🚀 Starting VNC Server in background...")
                process = subprocess.Popen(['python3', 'vnc_networking.py'])
                process.wait()
                print("⚠️ VNC Server stopped, restarting in 10 seconds...")
                time.sleep(10)
            except Exception as e:
                print(f"VNC error: {e}")
                time.sleep(10)
    
    # Start VNC in background thread
    vnc_thread = threading.Thread(target=run_vnc, daemon=True)
    vnc_thread.start()
    print("✅ VNC Server started in background")

# Start VNC when app starts
if os.getenv('ENABLE_VNC', 'true').lower() == 'true':
    pass  # Disabled automatic VNC start to prevent conflicts
import routes  # noqa: F401