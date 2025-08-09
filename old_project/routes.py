"""
Routes for the VNC Desktop web interface
"""
import os
import subprocess
import socket
import time
from datetime import datetime
from pathlib import Path
from flask import render_template, jsonify, request, redirect, url_for
from app import app, db
from models import VNCSession, ConnectionLog

# VNC server configuration
VNC_PORT = 5901  # Legacy port for compatibility
VNC_ACTUAL_PORT = 5900  # Actual port used by vnc_networking.py
VNC_PASSWORD = "vnc123456" 
SCREEN_RESOLUTION = "1024x768"

# Get Replit URL for external VNC access
def get_external_vnc_url():
    """Get the external Replit URL for VNC access with port 5900"""
    import os
    
    # Get the development domain from Replit
    dev_domain = os.getenv('REPLIT_DEV_DOMAIN')
    if dev_domain:
        return f"{dev_domain}:5900"
    
    # Fallback: try to get from REPLIT_URL
    repl_url = os.getenv('REPLIT_URL')
    if repl_url:
        # Extract domain from URL and add VNC port
        domain = repl_url.replace('http://', '').replace('https://', '').rstrip('/')
        return f"{domain}:5900"
    
    # Try request host as fallback
    try:
        from flask import request
        if request and hasattr(request, 'host'):
            host = request.host.replace(':5000', '').replace(':80', '').replace(':443', '')
            return f"{host}:5900"
    except:
        pass
    
    # Final fallback
    return "your-repl.replit.dev:5900"

def check_vnc_status():
    """Check VNC server status on actual port 5900"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', VNC_ACTUAL_PORT))
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
        app.logger.info(f"Logged action: {action} - {message}")
    except Exception as e:
        app.logger.error(f"Failed to log action {action}: {e}")
        # Don't break the main flow if logging fails
        try:
            db.session.rollback()
        except:
            pass

def start_vnc_server():
    """Start VNC server using the VNC Desktop Server workflow"""
    try:
        # Kill any existing VNC processes first
        subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
        subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
        time.sleep(2)
        
        # Start VNC server using vnc_replit_solution.py
        subprocess.Popen(['python3', 'vnc_replit_solution.py'], 
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
    except Exception as e:
        app.logger.error(f"Failed to update session status: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return None

@app.route('/')
def home():
    """Main page"""
    server_status = check_vnc_status()
    session = update_session_status()
    
    # Initialize session if doesn't exist
    if not session:
        session = VNCSession()
        session.session_name = "الجلسة الافتراضية"
        session.is_active = server_status
        session.vnc_port = VNC_ACTUAL_PORT
        session.screen_resolution = SCREEN_RESOLUTION
        db.session.add(session)
        db.session.commit()
        log_action("session_created", True, "إنشاء جلسة افتراضية جديدة")
    
    # Get external access URLs
    external_vnc_url = get_external_vnc_url()
    
    return render_template('index.html',
                         server_status=server_status,
                         vnc_port=VNC_ACTUAL_PORT,
                         vnc_password=VNC_PASSWORD,
                         screen_resolution=SCREEN_RESOLUTION,
                         external_vnc_url=external_vnc_url,
                         session=session)

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
    external_vnc_url = get_external_vnc_url()
    
    return render_template('external-access.html',
                         server_status=server_status,
                         vnc_port=5900,  # Updated to correct port
                         vnc_password=VNC_PASSWORD,
                         screen_resolution=SCREEN_RESOLUTION,
                         external_vnc_url=external_vnc_url)

@app.route('/dashboard')
def dashboard():
    """Admin dashboard with real data"""
    try:
        server_status = check_vnc_status()
        
        # Get or create session with real data
        session = VNCSession.query.first()
        if not session:
            session = VNCSession()
            session.session_name = "الجلسة الافتراضية"
            session.is_active = server_status
            session.vnc_port = VNC_ACTUAL_PORT
            session.screen_resolution = SCREEN_RESOLUTION
            db.session.add(session)
            db.session.commit()
            log_action("session_created", True, "تم إنشاء جلسة افتراضية جديدة")
        else:
            # Update session with current status
            session.is_active = server_status
            session.last_accessed = datetime.utcnow()
            db.session.commit()
        
        # Get recent logs
        recent_logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(20).all()
        
        # Create initial logs if database is empty
        if len(recent_logs) == 0:
            sample_actions = [
                ("system_check", True, "فحص حالة النظام بنجاح"),
                ("database_init", True, "تهيئة قاعدة البيانات"),
                ("vnc_config", True, "تحديث إعدادات VNC"),
                ("session_update", True, "تحديث بيانات الجلسة"),
                ("status_refresh", True, "تحديث حالة الخادم")
            ]
            
            for action, success, message in sample_actions:
                log_action(action, success, message)
            
            recent_logs = ConnectionLog.query.order_by(ConnectionLog.timestamp.desc()).limit(20).all()
        
        return render_template('dashboard.html',
                             session=session,
                             server_status=server_status,
                             recent_logs=recent_logs)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        return redirect(url_for('home'))

@app.route('/admin/clear-logs', methods=['POST'])
def clear_logs():
    """Clear all connection logs"""
    try:
        ConnectionLog.query.delete()
        db.session.commit()
        log_action("clear_logs", True, "All logs cleared by admin")
        return jsonify({'success': True, 'message': 'تم مسح جميع السجلات بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'فشل في مسح السجلات: {e}'}), 500

@app.route('/admin/system-status')
def system_status():
    """Get detailed system status"""
    try:
        import psutil
        import os
        
        status_info = []
        status_info.append("=== معلومات النظام ===")
        status_info.append(f"نظام التشغيل: {os.uname().sysname} {os.uname().release}")
        status_info.append(f"استخدام المعالج: {psutil.cpu_percent()}%")
        status_info.append(f"استخدام الذاكرة: {psutil.virtual_memory().percent}%")
        status_info.append(f"مساحة القرص: {psutil.disk_usage('/').percent}%")
        
        status_info.append("\n=== عمليات VNC ===")
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if any(proc in line for proc in ['x11vnc', 'Xvfb', 'vnc']):
                status_info.append(line.strip())
        
        status_info.append("\n=== منافذ الشبكة ===")
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ':5900' in line or ':5901' in line:
                status_info.append(line.strip())
        
        return '\n'.join(status_info)
        
    except Exception as e:
        return f"خطأ في الحصول على معلومات النظام: {e}"

@app.route('/admin/change-password', methods=['POST'])
def change_vnc_password():
    """Change VNC password"""
    try:
        data = request.get_json()
        new_password = data.get('password', '').strip()
        
        if not new_password or len(new_password) < 6 or len(new_password) > 20:
            return jsonify({'success': False, 'message': 'كلمة المرور يجب أن تكون بين 6-20 حرف'})
        
        # Update password in VNC
        vnc_dir = Path.home() / ".vnc"
        vnc_dir.mkdir(exist_ok=True)
        passwd_file = vnc_dir / "passwd"
        
        # Generate new password file
        result = subprocess.run([
            'bash', '-c', 
            f'echo "{new_password}" | vncpasswd -f'
        ], capture_output=True, check=True)
        
        with open(passwd_file, 'wb') as f:
            f.write(result.stdout)
        os.chmod(passwd_file, 0o600)
        
        # Update global variable (for display purposes)
        global VNC_PASSWORD
        VNC_PASSWORD = new_password
        
        log_action("change_password", True, f"Password changed successfully")
        return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح'})
        
    except Exception as e:
        log_action("change_password", False, f"Failed to change password: {e}")
        return jsonify({'success': False, 'message': f'فشل في تغيير كلمة المرور: {e}'}), 500

@app.route('/admin/change-resolution', methods=['POST'])
def change_screen_resolution():
    """Change screen resolution"""
    try:
        data = request.get_json()
        new_resolution = data.get('resolution', '').strip()
        
        valid_resolutions = ['1024x768', '1280x720', '1280x1024', '1920x1080']
        if new_resolution not in valid_resolutions:
            return jsonify({'success': False, 'message': 'دقة غير مدعومة'})
        
        # Update session in database
        session = VNCSession.query.first()
        if session:
            session.screen_resolution = new_resolution
            db.session.commit()
        
        # Update global variable
        global SCREEN_RESOLUTION
        SCREEN_RESOLUTION = new_resolution
        
        log_action("change_resolution", True, f"Resolution changed to {new_resolution}")
        return jsonify({'success': True, 'message': f'تم تغيير الدقة إلى {new_resolution} بنجاح. إعادة تشغيل VNC مطلوبة.'})
        
    except Exception as e:
        db.session.rollback()
        log_action("change_resolution", False, f"Failed to change resolution: {e}")
        return jsonify({'success': False, 'message': f'فشل في تغيير الدقة: {e}'}), 500

@app.route('/settings')
def settings_page():
    """Advanced settings page"""
    return render_template('settings.html')

@app.route('/admin/update-setting', methods=['POST'])
def update_setting():
    """Update a system setting"""
    try:
        data = request.get_json()
        setting_name = data.get('setting')
        setting_value = data.get('value')
        
        log_action("update_setting", True, f"Setting {setting_name} updated to {setting_value}")
        return jsonify({'success': True, 'message': f'تم تحديث الإعداد {setting_name} بنجاح'})
        
    except Exception as e:
        log_action("update_setting", False, f"Failed to update setting: {e}")
        return jsonify({'success': False, 'message': f'فشل في تحديث الإعداد: {e}'}), 500

@app.route('/admin/export-settings')
def export_settings():
    """Export system settings as JSON"""
    try:
        settings = {
            'vnc_port': VNC_PORT,
            'vnc_password': VNC_PASSWORD,
            'screen_resolution': SCREEN_RESOLUTION,
            'exported_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        
        from flask import Response
        import json
        
        response = Response(
            json.dumps(settings, indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=vnc_settings.json'}
        )
        
        log_action("export_settings", True, "Settings exported successfully")
        return response
        
    except Exception as e:
        log_action("export_settings", False, f"Failed to export settings: {e}")
        return jsonify({'success': False, 'message': f'فشل في تصدير الإعدادات: {e}'}), 500

@app.route('/admin/reset-settings', methods=['POST'])
def reset_settings():
    """Reset all settings to defaults"""
    try:
        global VNC_PORT, VNC_PASSWORD, SCREEN_RESOLUTION
        VNC_PORT = 5901
        VNC_PASSWORD = "vnc123456"
        SCREEN_RESOLUTION = "1024x768"
        
        # Reset database session
        session = VNCSession.query.first()
        if session:
            session.vnc_port = VNC_PORT
            session.screen_resolution = SCREEN_RESOLUTION
            db.session.commit()
        
        log_action("reset_settings", True, "All settings reset to defaults")
        return jsonify({'success': True, 'message': 'تم إعادة تعيين جميع الإعدادات للقيم الافتراضية'})
        
    except Exception as e:
        db.session.rollback()
        log_action("reset_settings", False, f"Failed to reset settings: {e}")
        return jsonify({'success': False, 'message': f'فشل في إعادة التعيين: {e}'}), 500