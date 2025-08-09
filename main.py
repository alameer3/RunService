#!/usr/bin/env python3
"""
Ubuntu Desktop VNC Server for Replit
A web-based Ubuntu desktop environment using VNC and noVNC
"""

import os
import sys
import subprocess
import socket
import threading
import time
import logging
import signal
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VNCDesktopServer:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Server ports
        self.http_port = 5000
        self.vnc_port = 5900
        self.websocket_port = 6080
        
        # Process tracking
        self.processes = []
        self.running = False
        
        logger.info("VNC Desktop Server initialized")
        
    def cleanup_processes(self):
        """Clean up existing processes"""
        logger.info("Cleaning up existing processes...")
        
        # Kill processes by name
        process_names = [
            "python3.*vnc", "websockify", "http.server", 
            "oneclick", "ultimate_vnc", "fixed_vnc"
        ]
        
        for name in process_names:
            try:
                subprocess.run(f"pkill -f '{name}'", shell=True, capture_output=True)
            except:
                pass
                
        time.sleep(2)
        
    def check_port(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0  # Port is available if connection fails
        except:
            return False
            
    def start_vnc_server(self):
        """Start the VNC server"""
        logger.info("Starting VNC server...")
        
        # Check if we have the VNC server script
        if (self.base_dir / "fixed_vnc_server.py").exists():
            vnc_script = "fixed_vnc_server.py"
        elif (self.base_dir / "ultimate_vnc_server.py").exists():
            vnc_script = "ultimate_vnc_server.py"
        else:
            logger.error("No VNC server script found")
            return False
            
        try:
            # Start VNC server
            vnc_process = subprocess.Popen(
                [sys.executable, vnc_script],
                stdout=open(self.logs_dir / "vnc_server.log", "w"),
                stderr=subprocess.STDOUT
            )
            self.processes.append(vnc_process)
            
            # Wait for VNC server to start
            time.sleep(3)
            
            # Check if VNC port is listening
            if not self.check_port(self.vnc_port):
                logger.error("VNC server failed to start")
                return False
                
            logger.info(f"VNC server started (PID: {vnc_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start VNC server: {e}")
            return False
            
    def start_websockify(self):
        """Start websockify proxy"""
        logger.info("Starting websockify proxy...")
        
        try:
            # Start websockify
            websock_process = subprocess.Popen([
                sys.executable, "-m", "websockify",
                f"0.0.0.0:{self.websocket_port}",
                f"127.0.0.1:{self.vnc_port}"
            ], stdout=open(self.logs_dir / "websockify.log", "w"),
               stderr=subprocess.STDOUT)
               
            self.processes.append(websock_process)
            
            # Wait for websockify to start
            time.sleep(2)
            
            logger.info(f"Websockify started (PID: {websock_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start websockify: {e}")
            return False
            
    def start_http_server(self):
        """Start HTTP server for web interface"""
        logger.info("Starting HTTP server...")
        
        try:
            # Change to noVNC directory if it exists
            novnc_dir = self.base_dir / "noVNC"
            if novnc_dir.exists():
                os.chdir(novnc_dir)
                
            # Start HTTP server
            http_process = subprocess.Popen([
                sys.executable, "-m", "http.server", str(self.http_port),
                "--bind", "0.0.0.0"
            ], stdout=open(self.logs_dir / "http_server.log", "w"),
               stderr=subprocess.STDOUT)
               
            self.processes.append(http_process)
            
            # Return to base directory
            os.chdir(self.base_dir)
            
            time.sleep(2)
            logger.info(f"HTTP server started on port {self.http_port} (PID: {http_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            return False
            
    def create_status_page(self):
        """Create a status/welcome page"""
        status_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ubuntu Desktop VNC - Status</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .status {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .link {{ display: inline-block; background: #007cba; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
        .link:hover {{ background: #005a87; }}
        .info {{ background: #f0f8ff; padding: 15px; border-left: 4px solid #007cba; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Ubuntu Desktop VNC Server</h1>
        
        <div class="status">
            <h3>✅ Server Status: Running</h3>
            <p>The Ubuntu Desktop VNC server is running and ready for connections.</p>
        </div>
        
        <h3>🌐 Access Options</h3>
        <div style="text-align: center;">
            <a href="/vnc.html" class="link">🖥️ Open Desktop</a>
            <a href="/vnc_lite.html" class="link">📱 Mobile View</a>
        </div>
        
        <div class="info">
            <h4>🔐 Connection Details</h4>
            <ul>
                <li><strong>VNC Server:</strong> 127.0.0.1:{self.vnc_port}</li>
                <li><strong>WebSocket:</strong> 127.0.0.1:{self.websocket_port}</li>
                <li><strong>Web Interface:</strong> Port {self.http_port}</li>
                <li><strong>Default Password:</strong> 123456</li>
            </ul>
        </div>
        
        <div class="info">
            <h4>📋 Features</h4>
            <ul>
                <li>Full Ubuntu Desktop Environment (LXDE)</li>
                <li>Web browser access - no VNC client needed</li>
                <li>Pre-installed Chromium browser</li>
                <li>Copy/paste support</li>
                <li>Mobile device compatible</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Ubuntu Desktop VNC Server | Powered by noVNC v1.2.0</p>
        </div>
    </div>
</body>
</html>"""
        
        # Save status page
        status_path = self.base_dir / "noVNC" / "index.html"
        if status_path.parent.exists():
            with open(status_path, 'w') as f:
                f.write(status_html)
            logger.info("Status page created")
                
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.stop()
        sys.exit(0)
        
    def stop(self):
        """Stop all processes"""
        logger.info("Stopping all processes...")
        self.running = False
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
                    
        self.cleanup_processes()
        logger.info("All processes stopped")
        
    def start(self):
        """Start the complete VNC desktop server"""
        logger.info("Starting Ubuntu Desktop VNC Server...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Clean up any existing processes
        self.cleanup_processes()
        
        # Check dependencies
        try:
            import websockify
            logger.info("✅ websockify available")
        except ImportError:
            logger.error("❌ websockify not available")
            return False
            
        # Check noVNC
        if not (self.base_dir / "noVNC").exists():
            logger.error("❌ noVNC directory not found")
            return False
            
        logger.info("✅ noVNC directory found")
        
        # Start services
        success = True
        
        if not self.start_vnc_server():
            success = False
            
        if success and not self.start_websockify():
            success = False
            
        if success:
            self.create_status_page()
            
        if success and not self.start_http_server():
            success = False
            
        if not success:
            logger.error("Failed to start some services")
            self.stop()
            return False
            
        self.running = True
        logger.info("🎉 Ubuntu Desktop VNC Server started successfully!")
        logger.info(f"🌐 Access your desktop at: http://0.0.0.0:{self.http_port}")
        logger.info("🔐 Default VNC password: 123456")
        
        # Keep server running
        try:
            while self.running:
                time.sleep(10)
                # Basic health check
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"Process {i} died, restarting server...")
                        self.stop()
                        return self.start()
                        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            
        self.stop()
        return True

def main():
    """Main entry point"""
    server = VNCDesktopServer()
    server.start()

if __name__ == "__main__":
    main()