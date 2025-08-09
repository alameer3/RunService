# Project Overview

## Overview

This is a VNC-based remote desktop environment project that provides a complete Ubuntu 22.04 desktop experience accessible through a web browser. The system creates a containerized virtual desktop environment with LXDE desktop manager, accessible via noVNC web interface, and secured with Cloudflare tunneling capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Containerization Strategy
- **Base System**: Ubuntu 22.04 LTS for stability and long-term support
- **Desktop Environment**: LXDE chosen for lightweight resource usage while maintaining full desktop functionality
- **Display Management**: Xvfb (X Virtual Framebuffer) for headless display server operations

### Remote Access Architecture
- **VNC Server**: x11vnc provides the core screen sharing functionality with password protection
- **Web Interface**: noVNC (v1.2.0) enables browser-based access without requiring VNC client software
- **WebSocket Bridge**: websockify handles the protocol translation between HTTP/WebSocket and VNC

### Security and Networking
- **Authentication**: Basic password protection (default: 123456) for VNC access
- **Tunnel Solution**: Cloudflare's cloudflared for secure external access and bypassing firewall restrictions
- **Network Tools**: Built-in utilities (net-tools, netcat) for connectivity troubleshooting

### Browser Integration
- **Web Browser**: Chromium browser manually installed (avoiding snap packages for container compatibility)
- **Package Management**: Direct .deb installation to ensure proper integration with the containerized environment

### System Configuration
- **Timezone**: Configured for Asia/Riyadh timezone with proper locale settings
- **Non-interactive Setup**: All installations configured to avoid user prompts during container builds
- **Process Management**: Designed for headless operation with automated service startup

## External Dependencies

### Core Infrastructure
- **Docker**: Container runtime environment for system deployment
- **Ubuntu Package Repositories**: System packages and security updates source

### Remote Access Services
- **noVNC Project**: Open-source HTML5 VNC client (GitHub: novnc/noVNC)
- **Websockify**: WebSocket-to-TCP proxy service (GitHub: novnc/websockify)
- **Cloudflare**: cloudflared binary for tunnel creation and external access

### Desktop Components
- **LXDE Desktop**: Lightweight desktop environment from Ubuntu repositories
- **X11 System**: X Window System components for graphical interface
- **Chromium Browser**: Web browser from Ubuntu security repositories

### Development Tools
- **Python 3**: Runtime environment with pip package manager
- **Git**: Version control system for repository management
- **System Utilities**: Network diagnostic and file management tools