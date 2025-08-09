# بيئة سطح مكتب VNC للسيرفر

## نظرة عامة

هذا المشروع يوفر حلاً متكاملاً لإعداد بيئة سطح مكتب خفيفة مع متصفح ويب يمكن الوصول إليها عبر VNC على سيرفر Ubuntu/Debian. النظام مُحسَّن ليعمل على سيرفرات بذاكرة 1 جيجا رام فقط مع تشغيل تلقائي بعد إعادة التشغيل.

## الميزات الرئيسية

- 🖥️ **بيئة سطح مكتب خفيفة**: LXDE محسنة للسيرفرات
- 🌐 **متصفحات متعددة**: Firefox ESR و Chromium
- 🔐 **آمن ومحمي**: حماية بكلمة مرور VNC
- ⚡ **تشغيل تلقائي**: بدء تلقائي مع النظام
- 💾 **استهلاك ذاكرة منخفض**: يعمل على 1 جيجا رام
- 🔧 **سهولة الإدارة**: أدوات إدارة متقدمة

## متطلبات النظام

- **نظام التشغيل**: Ubuntu 18.04+ أو Debian 9+
- **الذاكرة**: 1 GB RAM (مُوصى بـ 2 GB)
- **المساحة**: 2 GB مساحة فارغة
- **الشبكة**: اتصال إنترنت للتثبيت
- **الأذونات**: صلاحيات sudo

## التثبيت السريع

### التثبيت التلقائي (مُوصى به)

```bash
# تنزيل وتشغيل سكريبت التثبيت
curl -sSL https://raw.githubusercontent.com/your-repo/vnc-desktop/main/install.sh | sudo bash
```

أو:

```bash
# تنزيل وفحص السكريبت قبل التشغيل
wget https://raw.githubusercontent.com/your-repo/vnc-desktop/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

### التثبيت اليدوي

1. **استنساخ المستودع**:
   ```bash
   git clone https://github.com/your-repo/vnc-desktop.git
   cd vnc-desktop
   ```

2. **تشغيل سكريبت التثبيت**:
   ```bash
   sudo ./install.sh
   ```

3. **بدء الخدمات**:
   ```bash
   sudo ./manage-vnc.sh start
   ```

## الاستخدام

### الاتصال بسطح المكتب

بعد التثبيت، يمكنك الاتصال بسطح المكتب باستخدام:

- **العنوان**: `server-ip:5901`
- **كلمة المرور**: `vnc123456`
- **المنفذ**: `5901`

### برامج VNC المدعومة

- **VNC Viewer** (RealVNC) - الأفضل
- **TigerVNC Viewer**
- **TightVNC Viewer**
- **Remmina** (Linux)
- **Screen Sharing** (macOS)

### إدارة الخدمات

استخدم سكريبت `manage-vnc.sh` لإدارة الخدمات:

```bash
# عرض حالة الخدمات
./manage-vnc.sh status

# بدء الخدمات
./manage-vnc.sh start

# إيقاف الخدمات
./manage-vnc.sh stop

# إعادة تشغيل الخدمات
./manage-vnc.sh restart

# تغيير كلمة المرور
./manage-vnc.sh password

# عرض معلومات الاتصال
./manage-vnc.sh info
```

### بدء سطح المكتب يدوياً

يمكنك استخدام سكريبت `start-desktop.sh` لبدء سطح المكتب يدوياً:

```bash
./start-desktop.sh
```

## إعدادات متقدمة

### تخصيص دقة الشاشة

عدل الملف `/home/vncuser/.vnc/xstartup`:

```bash
# تغيير دقة الشاشة إلى 1280x720
Xvfb :1 -screen 0 1280x720x24
```

### تغيير المنفذ

عدل ملف الخدمة `/etc/systemd/system/vncserver.service`:

```bash
# تغيير المنفذ من 5901 إلى 5902
ExecStart=/usr/bin/x11vnc ... -rfbport 5902 ...
```

### إضافة تطبيقات للبدء التلقائي

عدل الملف `/home/vncuser/.vnc/xstartup`:

```bash
# إضافة تطبيق للبدء التلقائي
/path/to/application &
```

## استكشاف الأخطاء

### الخدمات لا تبدأ

```bash
# فحص السجلات
./manage-vnc.sh logs

# فحص حالة الخدمات
systemctl status vncserver.service
systemctl status xvfb.service
```

### لا يمكن الاتصال بـ VNC

1. **تحقق من المنفذ**:
   ```bash
   netstat -tlnp | grep 5901
   ```

2. **تحقق من جدار الحماية**:
   ```bash
   sudo ufw allow 5901
   # أو
   sudo iptables -A INPUT -p tcp --dport 5901 -j ACCEPT
   ```

3. **تحقق من العمليات**:
   ```bash
   ps aux | grep vnc
   ```

### بطء في الاستجابة

1. **تقليل جودة الألوان**:
   - في VNC Viewer، اختر "Medium" أو "Low"

2. **تقليل دقة الشاشة**:
   ```bash
   # تحرير /home/vncuser/.vnc/xstartup
   Xvfb :1 -screen 0 800x600x16
   ```

3. **إغلاق التطبيقات غير المستخدمة**

### مشاكل المتصفح

```bash
# إعادة تعيين إعدادات Firefox
rm -rf /home/vncuser/.mozilla/firefox/*/sessionstore*

# تشغيل Firefox في الوضع الآمن
firefox --safe-mode
```

## المجلدات والملفات المهمة

```
/home/vncuser/.vnc/          # إعدادات VNC
├── passwd                   # كلمة مرور VNC المشفرة
└── xstartup                 # سكريبت بدء سطح المكتب

/etc/systemd/system/         # خدمات النظام
├── vncserver.service        # خدمة VNC Server
└── xvfb.service            # خدمة العرض الافتراضي

/var/log/                   # سجلات النظام
├── vncserver.log           # سجلات VNC
└── xvfb.log               # سجلات العرض الافتراضي
```

## الأمان

### تغيير كلمة المرور الافتراضية

```bash
# استخدام أداة الإدارة
./manage-vnc.sh password

# أو يدوياً
echo "new-password" | sudo -u vncuser x11vnc -storepasswd /home/vncuser/.vnc/passwd
```

### تقييد الوصول

#### حسب عنوان IP

عدل `/etc/systemd/system/vncserver.service`:

```bash
ExecStart=/usr/bin/x11vnc ... -allow 192.168.1.0/24
```

#### استخدام SSH Tunnel

```bash
# على الجهاز المحلي
ssh -L 5901:localhost:5901 user@server-ip

# ثم اتصل بـ localhost:5901
```

## الأداء والتحسين

### تحسين LXDE

```bash
# تعطيل المؤثرات البصرية
# في /home/vncuser/.config/lxsession/LXDE/desktop.conf
[GTK]
sNet/ThemeName=Clearlooks
sNet/IconThemeName=nuoveXT2
```

### تحسين Firefox

```bash
# إعدادات منخفضة الذاكرة في about:config
browser.cache.disk.enable=false
browser.cache.memory.enable=true
browser.cache.memory.capacity=32768
```

### تحسين النظام

```bash
# تقليل استخدام المبادلة
echo 'vm.swappiness=10' >> /etc/sysctl.conf

# تحسين الذاكرة
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
```

## التحديث

```bash
# تحديث الحزم
sudo apt update && sudo apt upgrade -y

# إعادة تشغيل الخدمات
./manage-vnc.sh restart
```

## إلغاء التثبيت

```bash
# إيقاف الخدمات
sudo systemctl stop vncserver.service xvfb.service
sudo systemctl disable vncserver.service xvfb.service

# حذف الملفات
sudo rm -f /etc/systemd/system/vncserver.service
sudo rm -f /etc/systemd/system/xvfb.service
sudo userdel -r vncuser

# حذف الحزم (اختياري)
sudo apt remove --purge lxde-core x11vnc xvfb firefox-esr
```

## المساهمة

نرحب بمساهماتك! يرجى:

1. فتح Issue لمناقشة التغييرات المقترحة
2. إنشاء Fork للمستودع
3. إنشاء Branch للميزة الجديدة
4. إرسال Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## الدعم

- **GitHub Issues**: لتقارير الأخطاء والطلبات
- **Wiki**: للوثائق المفصلة
- **Discussions**: للأسئلة والمناقشات

---

**ملاحظة**: هذا المشروع مُحسَّن للاستخدام على السيرفرات. للاستخدام على أجهزة سطح المكتب، فضل استخدام حلول سطح المكتب التقليدية.