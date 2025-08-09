#!/bin/bash

echo "🔧 تثبيت المتطلبات الإضافية"
echo "=========================="

# تثبيت pip dependencies
echo "📦 [1/4] تثبيت مكتبات Python..."
pip3 install --user websockify || pip install --user websockify

# تثبيت fonts عربية إضافية
echo "🔤 [2/4] تثبيت الخطوط العربية..."
if command -v apt >/dev/null 2>&1; then
    sudo apt install -y \
        fonts-dejavu \
        fonts-liberation \
        fonts-droid-fallback \
        fonts-noto \
        fonts-amiri \
        || echo "⚠️ بعض الخطوط قد لا تكون متاحة"
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y \
        dejavu-fonts \
        liberation-fonts \
        google-noto-fonts \
        || echo "⚠️ بعض الخطوط قد لا تكون متاحة"
fi

# إعداد locale للعربية
echo "🌍 [3/4] إعداد اللغة العربية..."
if command -v locale-gen >/dev/null 2>&1; then
    sudo locale-gen ar_SA.UTF-8 2>/dev/null || true
    sudo locale-gen en_US.UTF-8 2>/dev/null || true
fi

# تحسين أداء Chromium
echo "🚀 [4/4] تحسين إعدادات Chromium..."
mkdir -p ~/.config/chromium/Default
cat > ~/.config/chromium/Default/Preferences << 'EOF'
{
   "browser": {
      "check_default_browser": false,
      "show_home_button": true
   },
   "default_search_provider_data": {
      "template_url_data": {
         "keyword": "google.com",
         "short_name": "Google",
         "url": "https://www.google.com/search?q={searchTerms}"
      }
   },
   "homepage": "https://www.google.com",
   "homepage_is_newtabpage": false,
   "session": {
      "restore_on_startup": 1
   }
}
EOF

echo ""
echo "✅ تم تثبيت المتطلبات الإضافية بنجاح!"
echo "يمكنك الآن تشغيل ./start.sh"
