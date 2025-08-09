# 🌐 قاعدة Ubuntu
FROM ubuntu:22.04

# ✅ تجاوز الإعداد التفاعلي + تثبيت tzdata وتحديد المنطقة الزمنية
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Riyadh /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# ✅ تثبيت Chromium يدويًا (بدون Snap)
RUN apt update && apt install -y \
    wget \
    && wget -q https://security.ubuntu.com/ubuntu/pool/universe/c/chromium-browser/chromium-browser_114.0.5735.90-0ubuntu1~snap1_amd64.deb && \
    apt install -y ./chromium-browser_114.0.5735.90-0ubuntu1~snap1_amd64.deb || true && \
    rm -f chromium-browser_114.0.5735.90-0ubuntu1~snap1_amd64.deb && \
    ln -sf /usr/bin/chromium /usr/bin/chromium-browser || true

# 🛠️ تثبيت الأدوات الأساسية وسطح المكتب و VNC و noVNC
RUN apt update && apt install -y \
    lxde \
    x11vnc \
    xvfb \
    git \
    python3 \
    python3-pip \
    curl \
    net-tools \
    netcat \
    tzdata \
    && apt clean

# 🔐 إعداد كلمة مرور VNC
RUN mkdir -p /root/.vnc && \
    x11vnc -storepasswd 123456 /root/.vnc/passwd

# 🌀 تحميل noVNC و websockify
RUN rm -rf /opt/noVNC && \
    git clone --branch v1.2.0 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    chmod +x /opt/noVNC/utils/launch.sh

# 🌐 تحميل cloudflared
RUN wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# ⏱️ تعيين التوقيت يدويًا لتجنب التفاعل
RUN ln -sf /usr/share/zoneinfo/Asia/Riyadh /etc/localtime && \
    echo "Asia/Riyadh" > /etc/timezone && \
    DEBIAN_FRONTEND=noninteractive apt install -y tzdata

# ✅ إصلاح صلاحيات مجلد X11 لتجنب تحذير Xvfb
RUN mkdir -p /tmp/.X11-unix && \
    chown root:root /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix

# 🖥️ نسخ سكربت التشغيل
COPY ./start.sh /start.sh
RUN chmod +x /start.sh

# ✅ إعداد تشغيل Chromium تلقائيًا مع سطح المكتب
RUN mkdir -p /root/.config/lxsession/LXDE && \
    echo "@chromium-browser --no-sandbox --disable-gpu" > /root/.config/lxsession/LXDE/autostart

# 🔥 بدء التشغيل
CMD ["/start.sh"]