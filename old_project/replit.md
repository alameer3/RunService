# مشروع متصفح VNC للسيرفر

## Overview

A project to set up a lightweight desktop environment with a web browser accessible via VNC on an Ubuntu/Debian server. The system is designed to run on servers with 1GB RAM and to start automatically after reboot. The business vision is to provide a highly accessible, lightweight remote desktop solution for server environments, enabling users to perform browser-based tasks efficiently without a full GUI installation. This project aims to tap into the market for cost-effective cloud computing and remote administration tools.

## User Preferences

- أسلوب التواصل المفضل: لغة عربية واضحة ومنظمة
- التركيز على الحلول الخفيفة والموثوقة
- يفضل التثبيت التلقائي والإعداد المبسط
- الحفاظ على ترتيب المشروع: عدم إضافة ملفات جديدة إلا عند الضرورة القصوى

## Migration Status
✅ **تمت الهجرة بنجاح إلى Replit** - 9 أغسطس 2025
- تم إعداد قاعدة بيانات PostgreSQL
- تم تشغيل تطبيق Flask على المنفذ 5000  
- تمت تهيئة الخدمات المتقدمة (WebSocket، الأمان، السحابة)
- واجهة إدارة VNC تعمل بنجاح

## System Architecture

The system is built around providing a lightweight, VNC-accessible desktop environment.

### Desktop Environment
- **LXDE**: Chosen for its minimal resource consumption, ideal for servers with limited memory.
- **Xvfb**: A virtual framebuffer for running the display server without a physical monitor.
- **VNC Server**: Utilizes `x11vnc` for remote access, secured with a password.

### Web Browsers
- **Firefox ESR**: The primary stable and lightweight browser.
- **Chromium**: Included as an alternative for sites requiring specific Chromium functionalities.

### Service Management
- **systemd**: Used for automatic service startup and management after reboots.

### UI/UX Decisions
The project emphasizes a clean, intuitive Arabic user interface for management tasks, with a focus on ease of use for VNC control and system monitoring. The web interface for managing the VNC server is built using Flask, ensuring a modular and well-structured application.

### Feature Specifications
- Automatic installation and setup of all components.
- Password-protected VNC access.
- Automatic startup of the VNC environment on system reboot.
- Operational efficiency on 1GB RAM servers.
- User-friendly interface for VNC and system management.
- Integration of an administrative dashboard and advanced settings page for VNC configuration and system monitoring.
- Enhanced system monitoring capabilities (CPU, memory, disk usage).

### Technical Implementations
- **Flask Web Application**: Provides the core web interface for managing the VNC server and monitoring the system. It follows modular design with separate files for `main`, `app` setup, `routes`, and `models`.
- **Database**: PostgreSQL is used for data persistence, including VNC session tracking and logs.
- **VNC Server Management**: Python scripts (`vnc_networking.py`, `vnc_status.py`) are used to manage and monitor the VNC server lifecycle.
- **System Utilities**: Bash scripts (`install.sh`, `manage-vnc.sh`, `quick-setup.sh`) handle initial setup and VNC service management.

## External Dependencies

- **Operating System**: Ubuntu/Debian distributions are targeted for deployment.
- **VNC Client Software**: Standard VNC client applications are used to connect to the server (e.g., TigerVNC Viewer, RealVNC Viewer).
- **PostgreSQL**: Used as the primary database for application data.
- **Python Libraries**: `Flask` for the web application, `psutil` for system monitoring.
- **Linux Packages**: `xvfb`, `x11vnc`, `openbox`, `firefox-esr`, `chromium`, `systemd`.