# نظام VNC Desktop المتطور

## Overview
نظام VNC Desktop احترافي ومتكامل يوفر بيئة سطح مكتب Linux كاملة عبر الويب. النظام مصمم ليكون حلاً شاملاً للوصول البعيد مع واجهة تحكم متطورة ومراقبة شاملة. يهدف المشروع إلى توفير حل فعال وموثوق للوصول عن بعد مع التركيز على الأداء، الأمان، وسهولة الاستخدام.

## User Preferences
- أسلوب التواصل: لغة عربية واضحة ومهنية
- التطوير: نظام احترافي متكامل بدون أخطاء
- الواجهة: تصميم متطور وسهل الاستخدام
- الأداء: استقرار وموثوقية عالية

## System Architecture

### Frontend
- **Framework**: Flask (Jinja2 templates)
- **Styling**: Bootstrap 5 (RTL for Arabic), Custom CSS (gradients, advanced animations)
- **Interactivity**: jQuery + AJAX, WebSocket for real-time updates
- **Icons**: Font Awesome

### VNC System (Migrated to Replit Native)
- **Virtual Display**: Xvfb (multi-resolution support) - Native Replit
- **VNC Server**: x11vnc (password protected) - Native Replit
- **Desktop Environment**: Lightweight desktop solutions compatible with Replit
- **Browser Support**: Firefox ESR + Chromium - System packages
- **Web Viewer**: Integrated web interface through Flask
- **Process Management**: Python-based VNC manager with automatic monitoring, auto-restart on errors
- **Security**: Password protection, session management, comprehensive audit logging
- **Migration Status**: Successfully migrated from Docker to native Replit environment (2025-08-09)

### Backend
- **Language**: Python 3.11+
- **Framework**: Flask + Extensions (SQLAlchemy, SocketIO)
- **Database**: PostgreSQL with SQLAlchemy ORM (migration support)
- **Real-time Communication**: Flask-SocketIO
- **System Integration**: Linux package management, service orchestration, resource optimization, advanced error handling
- **API**: RESTful API design for control and data retrieval

### Core Features
- **Control Panel**: Real-time server status, session management, advanced display/performance settings, detailed logs.
- **Application Management**: One-click software installation, pre-configured application library, package/dependency management, settings backup.
- **Monitoring & Analytics**: Resource usage monitoring, performance analysis, detailed usage reports, smart problem alerts.
- **UI/UX Decisions**: Responsive design, multi-language support (Arabic focus), professional Bootstrap 5 UI.

## External Dependencies

### Operating System
- Ubuntu/Debian Linux
- X11 Window System
- VNC Protocol Support

### Python Packages
- Flask + Extensions
- SQLAlchemy + PostgreSQL driver
- psutil
- requests
- Flask-SocketIO

### Linux Packages
- xvfb
- x11vnc
- lxde-core
- firefox-esr
- chromium
- build-essential

### Third-Party Services/Integrations
- **Cloudflare Tunnel**: For external access to Dockerized VNC (e.g., `xxx.trycloudflare.com`).
- **Lavalink Server (Optional Integration)**: Java-based music server for Discord bots. Supports YouTube, Spotify, Apple Music, Deezer, SoundCloud, Twitch, JioSaavn, Yandex Music, VK Music, Tidal, Qobuz. (Note: This is a separate project that could be integrated but is not directly part of the core VNC system functionality).