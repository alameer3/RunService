"""
Routes for the VNC Desktop web interface
"""
import os
import subprocess
import socket
import time
from datetime import datetime
from flask import render_template, jsonify, request, redirect, url_for
from app import app, db
from models import VNCSession, ConnectionLog

# VNC server configuration
VNC_PORT = 5901
VNC_PASSWORD = "vnc123456" 
SCREEN_RESOLUTION = "1024x768"

# Get Replit URL for external access
def get_repl_url():
    """Get the external Replit URL for VNC access"""
    import os
    repl_slug = os.getenv('REPL_SLUG', 'vnc-desktop')
    repl_owner = os.getenv('REPL_OWNER', 'user')
    
    # Replit format: https://repl-slug--repl-owner.replit.app:PORT
    return f"https://{repl_slug}--{repl_owner}.replit.app"

def check_vnc_status():
    """Check VNC server status"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', VNC_PORT))
            return result == 0
    except:
        return False

def log_action(action, success=True, message="", client_ip="127.0.0.1"):
    """Log actions to database"""
    try:
        log = ConnectionLog()
        log.action = action
        log.success = success
        log.message = message
        log.client_ip = client_ip
        db.session.add(log)
        db.session.commit()
    except:
        pass  # Don't break if logging fails

def start_vnc_server():
    """Start VNC server using the VNC Desktop Server workflow"""
    try:
        # Kill any existing VNC processes first
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        time.sleep(2)
        
        # Start VNC server in background
        subprocess.Popen(['python3', 'vnc_server.py'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        log_action('start', True, 'VNC server started successfully')
        return True
    except Exception as e:
        app.logger.error(f"Error starting VNC server: {e}")
        log_action('start', False, f'Failed to start VNC server: {e}')
        return False

def stop_vnc_server():
    """Stop VNC server"""
    try:
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        
        log_action('stop', True, 'VNC server stopped successfully')
        return True
    except Exception as e:
        app.logger.error(f"Error stopping VNC server: {e}")
        log_action('stop', False, f'Failed to stop VNC server: {e}')
        return False

def update_session_status():
    """Update or create VNC session record"""
    try:
        session = VNCSession.query.first()
        if not session:
            session = VNCSession()
            session.session_name = 'Desktop Session'
            session.vnc_port = VNC_PORT
            session.screen_resolution = SCREEN_RESOLUTION
            db.session.add(session)
        
        session.is_active = check_vnc_status()
        session.last_accessed = datetime.utcnow()
        db.session.commit()
        return session
    except:
        return None

@app.route('/')
def home():
    """Main page"""
    server_status = check_vnc_status()
    update_session_status()
    
    # Get external access URLs
    repl_url = get_repl_url()
    external_vnc_url = f"{repl_url}:{VNC_PORT}"
    
    return render_template('index.html',
                         server_status=server_status,
                         vnc_port=VNC_PORT,
                         vnc_password=VNC_PASSWORD,
                         screen_resolution=SCREEN_RESOLUTION,
                         repl_url=repl_url,
                         external_vnc_url=external_vnc_url)

@app.route('/api/status')
def api_status():
    """API endpoint for server status"""
    return jsonify({
        'status': check_vnc_status(),
        'port': VNC_PORT,
        'password': VNC_PASSWORD,
        'resolution': SCREEN_RESOLUTION
    })

@app.route('/start', methods=['POST'])
def start_server():
    """Start VNC server"""
    if start_vnc_server():
        return jsonify({'success': True, 'message': 'تم بدء تشغيل خادم VNC بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في بدء تشغيل خادم VNC'}), 500

@app.route('/stop', methods=['POST'])
def stop_server():
    """Stop VNC server"""
    if stop_vnc_server():
        return jsonify({'success': True, 'message': 'تم إيقاف خادم VNC بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في إيقاف خادم VNC'}), 500

@app.route('/logs')
def show_logs():
    """Show server logs"""
    try:
        # Get process information
        logs = []
        
        # Check VNC processes
        try:
            result = subprocess.run(['pgrep', '-f', 'x11vnc'], capture_output=True, text=True)
            if result.stdout.strip():
                logs.append("=== عمليات VNC النشطة ===")
                logs.append(result.stdout)
            else:
                logs.append("=== لا توجد عمليات VNC نشطة ===")
        except:
            pass
        
        # Check Xvfb processes
        try:
            result = subprocess.run(['pgrep', '-f', 'Xvfb'], capture_output=True, text=True)
            if result.stdout.strip():
                logs.append("\n=== عمليات Xvfb النشطة ===")
                logs.append(result.stdout)
        except:
            pass
        
        # Get recent database logs
        try:
            recent_logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(10).all()
            if recent_logs:
                logs.append("\n=== سجلات قاعدة البيانات (آخر 10 عمليات) ===")
                for log in recent_logs:
                    status = "✅" if log.success else "❌"
                    logs.append(f"{log.timestamp} {status} {log.action}: {log.message}")
        except:
            logs.append("\n=== لا يمكن قراءة سجلات قاعدة البيانات ===")
        
        if not logs:
            logs.append("لا توجد سجلات متاحة")
        
        return '\n'.join(logs)
        
    except Exception as e:
        return f"خطأ في قراءة السجلات: {e}"

@app.route('/download')
def download_page():
    """Download page for VNC clients"""
    return render_template('download.html')

@app.route('/external-access')
def external_access():
    """External access information page"""
    server_status = check_vnc_status()
    repl_url = get_repl_url()
    external_vnc_url = f"{repl_url}:{VNC_PORT}"
    
    return render_template('external-access.html',
                         server_status=server_status,
                         vnc_port=VNC_PORT,
                         vnc_password=VNC_PASSWORD,
                         screen_resolution=SCREEN_RESOLUTION,
                         repl_url=repl_url,
                         external_vnc_url=external_vnc_url)

@app.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    try:
        session = VNCSession.query.first()
        recent_logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(20).all()
        
        return render_template('dashboard.html',
                             session=session,
                             server_status=check_vnc_status(),
                             recent_logs=recent_logs)
    except:
        return redirect(url_for('home'))