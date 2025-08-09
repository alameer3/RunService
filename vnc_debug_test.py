#!/usr/bin/env python3
"""
VNC Debug Test - فحص تفصيلي لمشاكل VNC
"""
import subprocess
import os
import time

def test_xvfb():
    """اختبار Xvfb"""
    print("=== Testing Xvfb ===")
    try:
        # Test if Xvfb exists
        result = subprocess.run(['which', 'Xvfb'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Xvfb not found")
            return False
        
        print(f"✅ Xvfb found at: {result.stdout.strip()}")
        
        # Try to start Xvfb
        print("Starting Xvfb on display :99...")
        proc = subprocess.Popen([
            'Xvfb', ':99', 
            '-screen', '0', '1024x768x24',
            '-ac', '-nolisten', 'tcp'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if proc.poll() is None:
            print("✅ Xvfb started successfully")
            proc.terminate()
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Xvfb failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Xvfb test error: {e}")
        return False

def test_x11vnc():
    """اختبار x11vnc"""
    print("\n=== Testing x11vnc ===")
    try:
        # Test if x11vnc exists
        result = subprocess.run(['which', 'x11vnc'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ x11vnc not found")
            return False
        
        print(f"✅ x11vnc found at: {result.stdout.strip()}")
        
        # Get version
        result = subprocess.run(['x11vnc', '-version'], capture_output=True, text=True)
        print(f"Version info: {result.stderr[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ x11vnc test error: {e}")
        return False

def test_environment():
    """اختبار البيئة"""
    print("\n=== Testing Environment ===")
    
    # Check if running in container/sandbox
    if os.path.exists('/.dockerenv'):
        print("🐳 Running in Docker container")
    elif os.path.exists('/nix'):
        print("❄️ Running in Nix environment (Replit)")
    else:
        print("🖥️ Running on regular system")
    
    # Check permissions
    import pwd
    user = pwd.getpwuid(os.getuid()).pw_name
    print(f"User: {user}")
    print(f"UID: {os.getuid()}")
    
    # Check /tmp permissions
    try:
        test_file = '/tmp/vnc_test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ /tmp is writable")
    except:
        print("❌ /tmp is not writable")

def test_display_env():
    """اختبار متغير DISPLAY"""
    print("\n=== Testing Display Environment ===")
    
    display = os.environ.get('DISPLAY')
    print(f"Current DISPLAY: {display}")
    
    # Set test display
    os.environ['DISPLAY'] = ':99'
    print("Set DISPLAY to :99")
    
    return True

def test_simple_vnc():
    """اختبار VNC مبسط"""
    print("\n=== Testing Simple VNC Setup ===")
    
    try:
        # Start minimal Xvfb
        print("Starting minimal Xvfb...")
        xvfb_proc = subprocess.Popen([
            'Xvfb', ':99', '-screen', '0', '800x600x16'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        time.sleep(2)
        
        if xvfb_proc.poll() is not None:
            _, stderr = xvfb_proc.communicate()
            print(f"❌ Xvfb failed: {stderr.decode()}")
            return False
        
        # Try x11vnc with minimal options
        print("Starting minimal x11vnc...")
        os.environ['DISPLAY'] = ':99'
        
        vnc_proc = subprocess.Popen([
            'x11vnc', '-display', ':99', '-rfbport', '5900',
            '-nopw', '-forever', '-shared'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if vnc_proc.poll() is None:
            print("✅ VNC started successfully!")
            print("Stopping processes...")
            vnc_proc.terminate()
            xvfb_proc.terminate()
            return True
        else:
            stdout, stderr = vnc_proc.communicate()
            print(f"❌ VNC failed: {stderr.decode()}")
            xvfb_proc.terminate()
            return False
        
    except Exception as e:
        print(f"❌ Simple VNC test error: {e}")
        return False

def main():
    print("🔍 VNC Debug Test - فحص تفصيلي")
    print("=" * 50)
    
    results = []
    
    results.append(("Environment", test_environment()))
    results.append(("Display Env", test_display_env()))
    results.append(("Xvfb", test_xvfb()))
    results.append(("x11vnc", test_x11vnc()))
    results.append(("Simple VNC", test_simple_vnc()))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15}: {status}")
    
    if all(result for _, result in results):
        print("\n🎉 All tests passed! VNC should work.")
    else:
        print("\n⚠️ Some tests failed. VNC may not work properly.")

if __name__ == "__main__":
    main()