# Multi-stage Docker build for VNC Desktop Server
# بناء Docker متعدد المراحل لخادم سطح مكتب VNC

# مرحلة البناء
FROM ubuntu:22.04 AS builder

# تجنب التفاعل أثناء التثبيت
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# تثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# إنشاء بيئة Python افتراضية
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# نسخ متطلبات Python وتثبيتها
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# مرحلة التشغيل
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# تثبيت التبعيات النهائية
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    # VNC وسطح المكتب
    x11vnc \
    xvfb \
    openbox \
    lxde-core \
    firefox-esr \
    chromium-browser \
    # أدوات النظام
    curl \
    wget \
    git \
    nano \
    htop \
    net-tools \
    # تطوير
    build-essential \
    # تنظيف
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# نسخ البيئة الافتراضية من مرحلة البناء
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# إنشاء مستخدم غير root
RUN useradd -m -u 1000 -s /bin/bash vncuser && \
    usermod -aG sudo vncuser

# إعداد مجلد العمل
WORKDIR /app

# نسخ الكود المصدر
COPY --chown=vncuser:vncuser . .

# إعداد صلاحيات الملفات
RUN chmod +x *.sh && \
    chmod +x *.py && \
    mkdir -p /home/vncuser/.vnc && \
    chown -R vncuser:vncuser /home/vncuser/.vnc

# التبديل للمستخدم غير root
USER vncuser

# إعداد VNC password
RUN mkdir -p /home/vncuser/.vnc && \
    echo "vnc123456" | x11vnc -storepasswd /home/vncuser/.vnc/passwd

# فضح المنافذ
EXPOSE 5000 5900 6379

# نقطة الدخول الرئيسية
COPY docker/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER vncuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["web"]