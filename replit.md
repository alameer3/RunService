# Overview

This is a web-based Ubuntu desktop environment that runs a full LXDE desktop accessible through a web browser using VNC and noVNC technologies. The project enables users to access a complete Ubuntu desktop remotely without installing any local applications, featuring Chromium browser pre-installed and optional public access through Cloudflare tunnels.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Containerization Strategy
The system uses Docker containerization with Ubuntu 22.04 as the base image to ensure consistent deployment across different environments. This approach isolates the desktop environment and provides easy portability.

## Desktop Environment
- **Display Server**: Uses LXDE (Lightweight X11 Desktop Environment) for optimal performance in containerized environments
- **Virtual Display**: Implements Xvfb (X Virtual Framebuffer) to create a virtual X server without requiring physical display hardware
- **Remote Access**: Utilizes x11vnc server to capture the virtual desktop and make it accessible over VNC protocol

## Web Interface Architecture
- **noVNC Integration**: Implements noVNC v1.2.0 as the primary web-based VNC client, eliminating the need for users to install VNC client software
- **WebSocket Bridge**: Uses websockify to translate between VNC protocol and WebSocket connections, enabling browser-based access
- **Security Layer**: Implements VNC password authentication (default: 123456) for basic access control

## Network Architecture
- **Public Tunneling**: Integrates Cloudflared for optional public internet access through Cloudflare tunnels
- **Port Management**: Uses standard VNC ports with web interface redirection for seamless browser access
- **Cross-Platform Compatibility**: Designed to work across desktop, mobile, and tablet devices through responsive web interface

## Application Layer
- **Pre-installed Browser**: Includes Chromium browser installed via manual .deb package to avoid snap dependencies
- **Package Management**: Uses APT package manager with non-interactive configuration to prevent installation prompts
- **Timezone Configuration**: Pre-configured for Asia/Riyadh timezone with automatic daylight saving handling

## Deployment Strategy
- **Setup Scripts**: Provides automated setup and startup scripts (setup.sh, start.sh) for easy deployment
- **Permission Management**: Includes proper file permission configuration for executable scripts
- **Environment Variables**: Uses DEBIAN_FRONTEND=noninteractive to ensure automated installation without user prompts

# External Dependencies

## Core System Dependencies
- **Ubuntu 22.04**: Base operating system image
- **LXDE Desktop Environment**: Lightweight desktop environment package
- **Xvfb**: Virtual framebuffer X server for headless operation
- **x11vnc**: VNC server for X11 display sharing

## Web Technologies
- **noVNC v1.2.0**: HTML5 VNC client from GitHub (novnc/noVNC)
- **websockify**: WebSocket-to-TCP proxy from GitHub (novnc/websockify)
- **Python3**: Runtime environment for websockify and noVNC components

## Browser Integration
- **Chromium Browser**: Manual installation via Ubuntu security repository .deb package
- **Browser Dependencies**: Associated libraries and dependencies for Chromium functionality

## Network Services
- **Cloudflared**: Latest version from GitHub releases (cloudflare/cloudflared)
- **Network Utilities**: net-tools and netcat for network diagnostics and management

## Development Tools
- **Git**: Version control system for downloading noVNC and websockify
- **curl**: HTTP client for various network operations
- **wget**: File download utility for package retrieval

## System Utilities
- **tzdata**: Timezone data package for accurate time configuration
- **Python3-pip**: Package installer for Python dependencies (though not actively used in current setup)