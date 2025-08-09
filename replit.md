# VNC Desktop Server

## Overview

This project provides a complete VNC desktop environment solution for servers, featuring a lightweight desktop accessible via VNC with web browser support. The system is optimized to run on servers with limited resources (1GB RAM) and includes automatic startup, web-based management interface, and advanced monitoring capabilities. The project includes both Arabic and English interfaces with a focus on ease of use and reliability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Application Framework
- **Flask**: Core web framework providing the management interface for VNC server control
- **SQLAlchemy**: Database ORM with PostgreSQL support for session management and logging
- **Jinja2 Templates**: Arabic-first template system with responsive design

### VNC Server Architecture
- **Xvfb**: Virtual framebuffer X11 server for headless operation, configured for 1024x768x24 resolution
- **x11vnc**: VNC server implementation with password protection (default: vnc123456)
- **LXDE/Openbox**: Lightweight desktop environment chosen for minimal memory footprint
- **Multi-browser Support**: Firefox ESR and Chromium integration

### Real-time Communication
- **WebSocket Integration**: Flask-SocketIO for real-time status updates and monitoring
- **Event-driven Updates**: Live VNC server status, connection monitoring, and system metrics

### Performance & Monitoring
- **Performance Monitor**: System resource tracking (CPU, memory, disk usage)
- **Connection Logging**: Comprehensive audit trail for security and analytics
- **Health Checks**: Automated system health monitoring with port availability checks

### Security Implementation
- **Rate Limiting**: Request throttling to prevent abuse
- **IP-based Security**: Failed attempt tracking with automatic blocking
- **Session Management**: Secure session handling with admin authentication
- **Input Validation**: VNC password and resolution validation

### Background Processing
- **Celery Workers**: Asynchronous task processing for maintenance and monitoring
- **Scheduled Tasks**: Automated cleanup, health checks, and backup operations
- **Queue Management**: Task prioritization with dedicated queues for different operations

### Data Storage Strategy
- **PostgreSQL**: Primary database for persistent data (sessions, logs, configurations)
- **Redis Cache**: High-performance caching and session storage
- **File-based Configs**: JSON configuration files for VNC-specific settings

### Deployment Architecture
- **Docker Support**: Containerized deployment with docker-compose configuration
- **Systemd Integration**: Service management for automatic startup and recovery
- **Process Management**: Multi-process architecture with proper cleanup and monitoring

### Network Configuration
- **Port Management**: VNC on 5900, Web interface on 5000, with Replit domain integration
- **External Access**: Dynamic URL generation for external VNC client connections
- **Proxy Support**: Nginx integration for production deployments

## External Dependencies

### Core System Dependencies
- **X11 Libraries**: Xvfb, x11vnc, xauth for virtual display management
- **Desktop Environment**: LXDE, Openbox, desktop file utilities
- **Network Tools**: netstat, lsof for port monitoring and network diagnostics

### Python Package Dependencies
- **Web Framework**: Flask, Flask-SQLAlchemy, Flask-SocketIO
- **Database**: psycopg2-binary for PostgreSQL connectivity
- **Caching**: redis-py for Redis integration
- **Background Tasks**: Celery for asynchronous processing
- **System Monitoring**: psutil for system metrics
- **Security**: bcrypt, cryptography for password handling

### Cloud Integrations
- **AWS Services**: S3 for backup storage, CloudWatch for monitoring, SNS for notifications
- **Backup Solutions**: Automated database and configuration backups to cloud storage
- **Monitoring**: Integration with cloud-based monitoring services

### Development and Testing
- **Process Management**: subprocess, signal handling for VNC server lifecycle
- **Network Testing**: socket programming for port availability and connectivity tests
- **Logging**: Python logging with multiple handlers for debugging and production

### Browser Dependencies
- **Firefox ESR**: Primary web browser with Arabic language support
- **Chromium**: Secondary browser for compatibility testing
- **Browser Extensions**: Pre-configured for optimal VNC usage