# تعليمات تشغيل مشروع VNC Desktop على السيرفر البعيد

## نظرة عامة
هذا المشروع يوفر واجهة ويب لإدارة خادم VNC Desktop، مما يسمح لك بالوصول لسطح مكتب كامل عن بُعد مع متصفح ومحطة طرفية.

## متطلبات السيرفر

### الحد الأدنى للمواصفات
- **الذاكرة**: 1 جيجا رام (موصى به 2 جيجا)
- **المعالج**: أي معالج حديث
- **المساحة**: 2-5 جيجا للتثبيت
- **نظام التشغيل**: Ubuntu 20.04+ أو Debian 11+

### المنافذ المطلوبة
- **5000**: واجهة الويب (Flask)
- **5901**: خادم VNC Desktop
- **22**: SSH (للإدارة)

## طريقة التشغيل على السيرفر

### 1. رفع الملفات
```bash
# رفع جميع ملفات المشروع إلى السيرفر
scp -r * user@your-server:/home/user/vnc-desktop/
```

### 2. تثبيت المتطلبات التلقائي
```bash
cd /home/user/vnc-desktop/
chmod +x install.sh
sudo ./install.sh
```

### 3. إعداد قاعدة البيانات
```bash
# إعداد PostgreSQL (إذا لم يكن مثبت)
sudo apt install postgresql postgresql-contrib python3-psycopg2
sudo -u postgres createdb vnc_desktop
sudo -u postgres psql -c "CREATE USER vncuser WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vnc_desktop TO vncuser;"

# تعيين متغير البيئة
export DATABASE_URL="postgresql://vncuser:your_password@localhost/vnc_desktop"
```

### 4. تثبيت مكتبات Python
```bash
pip3 install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator
```

### 5. تشغيل التطبيق
```bash
# الطريقة السريعة (للتطوير)
python3 -c "from app import app; app.run(host='0.0.0.0', port=5000)"

# الطريقة المهنية (للإنتاج)
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

### 6. تشغيل خادم VNC (عند الحاجة)
```bash
python3 vnc_server.py
```

## الوصول للنظام

### من المتصفح
- افتح: `http://your-server-ip:5000`
- استخدم الواجهة لبدء/إيقاف خادم VNC

### من برنامج VNC
- العنوان: `your-server-ip:5901`
- كلمة المرور: `vnc123456`

## أتمتة التشغيل (systemd)

### إنشاء خدمة Flask
```bash
sudo tee /etc/systemd/system/vnc-web.service > /dev/null <<EOF
[Unit]
Description=VNC Desktop Web Interface
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/vnc-desktop
Environment=DATABASE_URL=postgresql://vncuser:your_password@localhost/vnc_desktop
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vnc-web.service
sudo systemctl start vnc-web.service
```

## الأمان

### جدار الحماية
```bash
# السماح للمنافذ المطلوبة فقط
sudo ufw allow 22      # SSH
sudo ufw allow 5000    # Web Interface
sudo ufw allow 5901    # VNC
sudo ufw --force enable
```

### تحديث كلمة مرور VNC
عدّل `VNC_PASSWORD` في ملف `routes.py`:
```python
VNC_PASSWORD = "كلمة_مرور_قوية_جديدة"
```

## استكشاف الأخطاء

### فحص حالة الخدمات
```bash
# حالة واجهة الويب
sudo systemctl status vnc-web.service

# حالة قاعدة البيانات
sudo systemctl status postgresql

# العمليات النشطة
ps aux | grep -E "(python|vnc|Xvfb)"
```

### السجلات
```bash
# سجلات واجهة الويب
journalctl -u vnc-web.service -f

# سجلات VNC
tail -f ~/.vnc/*.log
```

## الميزات المتوفرة

### واجهة الويب
- ✅ مراقبة حالة خادم VNC
- ✅ بدء/إيقاف الخادم
- ✅ عرض معلومات الاتصال
- ✅ روابط تحميل برامج VNC
- ✅ عرض السجلات

### سطح المكتب
- ✅ متصفح Firefox مع Google
- ✅ محطة طرفية (Terminal)
- ✅ مدير ملفات بسيط
- ✅ بيئة سطح مكتب خفيفة (OpenBox)

### قاعدة البيانات
- ✅ تتبع جلسات VNC
- ✅ سجل العمليات والاتصالات
- ✅ إحصائيات الاستخدام

---

**ملاحظة**: هذا المشروع مُحسَّن للعمل على سيرفرات بذاكرة محدودة (1 جيجا رام) ويوفر تجربة سطح مكتب سريعة وموثوقة عن بُعد.