#!/usr/bin/env python3
"""
فحص وتشخيص شامل لمكونات VNC في بيئة Replit
"""
import os
import subprocess
import sys
import time
import socket

def run_command(cmd, timeout=10):
    """تشغيل أمر مع مهلة زمنية"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                              text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)

def check_binary(name):
    """فحص وجود برنامج"""
    ret, stdout, stderr = run_command(f"which {name}")
    if ret == 0:
        version_ret, version_out, _ = run_command(f"{name} --help 2>&1 | head -3")
        return True, stdout.strip(), version_out
    return False, "", ""

def test_display():
    """فحص العرض"""
    print("🖥️  فحص العرض...")
    
    # فحص DISPLAY الحالي
    current_display = os.environ.get('DISPLAY', 'غير محدد')
    print(f"   العرض الحالي: {current_display}")
    
    # فحص العروض المتاحة
    ret, stdout, stderr = run_command("ls /tmp/.X*-lock 2>/dev/null || echo 'لا توجد عروض نشطة'")
    print(f"   العروض النشطة: {stdout.strip()}")
    
    return True

def test_xvfb():
    """اختبار Xvfb"""
    print("🖼️  اختبار Xvfb...")
    
    # قتل أي Xvfb موجود
    run_command("pkill -f 'Xvfb :99'")
    time.sleep(2)
    
    try:
        # تشغيل Xvfb على العرض :99
        process = subprocess.Popen([
            'Xvfb', ':99', 
            '-screen', '0', '1024x768x24',
            '-ac', '+extension', 'GLX'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if process.poll() is None:
            print("   ✅ Xvfb يعمل بنجاح على :99")
            
            # اختبار الاتصال
            os.environ['DISPLAY'] = ':99'
            ret, out, err = run_command("xdpyinfo | head -5")
            if ret == 0:
                print("   ✅ يمكن الاتصال بالعرض :99")
                print(f"      معلومات العرض: {out.split()[0] if out else 'غير متوفر'}")
            else:
                print("   ❌ لا يمكن الاتصال بالعرض")
            
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ فشل Xvfb: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"   ❌ خطأ في Xvfb: {e}")
        return False

def test_x11vnc():
    """اختبار x11vnc"""
    print("🔌 اختبار x11vnc...")
    
    # إنشاء عرض وهمي أولاً
    print("   بدء Xvfb للاختبار...")
    xvfb_process = subprocess.Popen([
        'Xvfb', ':98', 
        '-screen', '0', '1024x768x24', '-ac'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    if xvfb_process.poll() is not None:
        print("   ❌ لا يمكن بدء Xvfb للاختبار")
        return False
    
    try:
        os.environ['DISPLAY'] = ':98'
        
        # اختبار x11vnc بدون كلمة مرور
        print("   اختبار x11vnc...")
        vnc_process = subprocess.Popen([
            'x11vnc', '-display', ':98', 
            '-rfbport', '5901',  # منفذ مختلف للاختبار
            '-once', '-nopw',
            '-desktop', 'Test-VNC'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(5)
        
        # فحص المنفذ
        port_open = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5901))
                port_open = result == 0
        except:
            pass
        
        if port_open:
            print("   ✅ x11vnc يعمل بنجاح على المنفذ 5901")
            vnc_success = True
        else:
            print("   ❌ x11vnc لا يعمل")
            stdout, stderr = vnc_process.communicate()
            print(f"      الإخراج: {stderr.decode()[:200]}")
            vnc_success = False
        
        # تنظيف
        vnc_process.terminate()
        xvfb_process.terminate()
        try:
            vnc_process.wait(timeout=5)
            xvfb_process.wait(timeout=5)
        except:
            pass
        
        return vnc_success
        
    except Exception as e:
        print(f"   ❌ خطأ في x11vnc: {e}")
        if xvfb_process.poll() is None:
            xvfb_process.terminate()
        return False

def test_password():
    """اختبار إنشاء كلمة مرور VNC"""
    print("🔑 اختبار كلمة مرور VNC...")
    
    passwd_file = "/tmp/test_vnc_passwd"
    
    # طريقة 1: x11vnc
    ret, out, err = run_command(f"x11vnc -storepasswd testpass {passwd_file}")
    if ret == 0 and os.path.exists(passwd_file):
        print("   ✅ x11vnc -storepasswd يعمل")
        os.remove(passwd_file)
        return True
    
    # طريقة 2: vncpasswd
    ret, out, err = run_command(f"echo 'testpass' | vncpasswd -f > {passwd_file}")
    if ret == 0 and os.path.exists(passwd_file):
        print("   ✅ vncpasswd يعمل")
        os.remove(passwd_file)
        return True
    
    print("   ❌ لا يمكن إنشاء كلمة مرور VNC")
    return False

def test_firefox():
    """اختبار Firefox"""
    print("🦊 اختبار Firefox...")
    
    # بدء Xvfb للاختبار
    xvfb_process = subprocess.Popen([
        'Xvfb', ':97', 
        '-screen', '0', '1024x768x24', '-ac'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    if xvfb_process.poll() is not None:
        print("   ❌ لا يمكن بدء Xvfb لاختبار Firefox")
        return False
    
    try:
        env = os.environ.copy()
        env['DISPLAY'] = ':97'
        
        # اختبار Firefox
        firefox_process = subprocess.Popen([
            'firefox', '--version'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        
        stdout, stderr = firefox_process.communicate(timeout=10)
        
        if firefox_process.returncode == 0:
            print(f"   ✅ Firefox متوفر: {stdout.decode().strip()}")
            firefox_success = True
        else:
            print("   ❌ Firefox غير متوفر")
            firefox_success = False
        
        xvfb_process.terminate()
        xvfb_process.wait()
        
        return firefox_success
        
    except Exception as e:
        print(f"   ❌ خطأ في Firefox: {e}")
        if xvfb_process.poll() is None:
            xvfb_process.terminate()
        return False

def main():
    """الاختبار الرئيسي"""
    print("=" * 60)
    print("🔍 تشخيص شامل لمكونات VNC في بيئة Replit")
    print("=" * 60)
    
    # فحص البرامج المطلوبة
    programs = ['Xvfb', 'x11vnc', 'firefox', 'openbox', 'vncpasswd']
    available_programs = {}
    
    print("🔍 فحص البرامج المطلوبة:")
    for prog in programs:
        available, path, version = check_binary(prog)
        available_programs[prog] = available
        if available:
            print(f"   ✅ {prog}: {path}")
            if version:
                print(f"      {version.split()[0] if version else ''}")
        else:
            print(f"   ❌ {prog}: غير متوفر")
    
    print()
    
    # اختبارات مفصلة
    tests = [
        ("فحص العرض", test_display),
        ("اختبار Xvfb", test_xvfb),
        ("اختبار x11vnc", test_x11vnc),
        ("اختبار كلمة المرور", test_password),
        ("اختبار Firefox", test_firefox)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ خطأ غير متوقع: {e}")
            results[test_name] = False
    
    # تقرير النتائج
    print("\n" + "=" * 60)
    print("📊 تقرير النتائج:")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_tests = len(results)
    success_rate = (success_count / total_tests) * 100
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name}: {status}")
    
    print(f"\n📈 معدل النجاح: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    # توصيات
    print("\n💡 التوصيات:")
    if not available_programs['Xvfb']:
        print("   ❗ Xvfb غير متوفر - مطلوب لـ VNC")
    if not available_programs['x11vnc']:
        print("   ❗ x11vnc غير متوفر - مطلوب لـ VNC server")
    if success_rate >= 80:
        print("   ✅ النظام جاهز لتشغيل VNC مع بعض التحسينات")
    elif success_rate >= 60:
        print("   ⚠️  النظام يحتاج تحسينات لتشغيل VNC")
    else:
        print("   ❌ النظام يحتاج إصلاحات كبيرة لتشغيل VNC")
    
    print("=" * 60)

if __name__ == "__main__":
    main()