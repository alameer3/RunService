# دليل النشر على سيرفر بعيد

## خيارات النشر

### 1. النشر على Replit (الحل الأسهل)

يمكنك نشر هذا المشروع على Replit ليعمل كسيرفر بعيد:

1. **تفعيل النشر**:
   - اضغط على زر "Deploy" في Replit
   - اختر "Autoscale Deployment"
   - سيحصل المشروع على رابط عام مثل: `https://your-project.replit.app`

2. **الوصول للخادم**:
   - VNC سيكون متاح على: `your-project.replit.app:5901`
   - واجهة الويب: `https://your-project.replit.app`

### 2. النشر على VPS أو سيرفر خاص

#### متطلبات السيرفر:
- Ubuntu 18.04+ أو Debian 9+
- 1-2 GB RAM
- 2 GB مساحة فارغة
- اتصال إنترنت

#### خطوات التثبيت على السيرفر:

```bash
# 1. اتصل بالسيرفر عبر SSH
ssh username@your-server-ip

# 2. نزل الملفات
git clone https://github.com/your-username/vnc-desktop.git
cd vnc-desktop

# 3. تشغيل التثبيت التلقائي
sudo ./install.sh

# 4. بدء الخدمات
sudo ./manage-vnc.sh start
```

### 3. فتح المنافذ المطلوبة

#### على السيرفر (ufw):
```bash
sudo ufw allow 5901/tcp  # VNC
sudo ufw allow 5000/tcp  # واجهة الويب
sudo ufw allow ssh
sudo ufw enable
```

#### على السيرفر (iptables):
```bash
sudo iptables -A INPUT -p tcp --dport 5901 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### 4. الاتصال من جهازك

#### باستخدام VNC Viewer:
1. نزل VNC Viewer من: https://www.realvnc.com/download/viewer/
2. اتصل بـ: `server-ip:5901`
3. كلمة المرور: `vnc123456`

#### عبر واجهة الويب:
- افتح: `http://server-ip:5000`

## الأمان والحماية

### تغيير كلمة المرور:
```bash
./manage-vnc.sh password
```

### تشفير الاتصال بـ SSH Tunnel:
```bash
# على جهازك المحلي
ssh -L 5901:localhost:5901 username@server-ip

# ثم اتصل بـ VNC على: localhost:5901
```

### تقييد الوصول حسب IP:
```bash
sudo ufw allow from YOUR_IP_ADDRESS to any port 5901
```

## مراقبة النظام

### فحص حالة الخدمات:
```bash
./manage-vnc.sh status
```

### عرض السجلات:
```bash
./manage-vnc.sh logs
```

### إعادة التشغيل:
```bash
./manage-vnc.sh restart
```

## استكشاف الأخطاء

### مشكلة الاتصال:
1. تأكد من فتح المنافذ
2. فحص حالة الخدمات
3. تحقق من جدار الحماية

### بطء الاستجابة:
1. قلل جودة الألوان في VNC Viewer
2. استخدم SSH Tunnel للتشفير
3. تأكد من سرعة الإنترنت

## النشر السحابي

### AWS EC2:
1. أنشئ EC2 instance (Ubuntu)
2. افتح المنافذ في Security Groups
3. اتبع خطوات التثبيت أعلاه

### Digital Ocean:
1. أنشئ Droplet (Ubuntu)
2. استخدم Cloud Firewall لفتح المنافذ
3. اتبع خطوات التثبيت

### Google Cloud:
1. أنشئ VM Instance
2. افتح المنافذ في Firewall rules
3. اتبع خطوات التثبيت