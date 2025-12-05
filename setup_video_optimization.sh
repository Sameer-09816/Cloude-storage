#!/bin/bash

# Ultra-Fast Video Streaming Setup Script
# Optimized for Linode VPS (172.105.43.10)
# This script installs FFmpeg and optimizes system for video streaming

set -e

echo "================================================"
echo "Ultra-Fast Video Streaming Setup"
echo "================================================"

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install FFmpeg for video optimization
echo "Installing FFmpeg for video optimization..."
sudo apt-get install -y ffmpeg

# Verify FFmpeg installation
if command -v ffmpeg &> /dev/null; then
    echo "FFmpeg installed successfully!"
    ffmpeg -version | head -n 1
else
    echo "WARNING: FFmpeg installation failed. Video optimization won't work."
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv nginx

# Optimize system for video streaming
echo "Optimizing system for video streaming..."

# Increase file watchers for better performance
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Optimize network settings
echo "Optimizing network settings..."
sudo tee -a /etc/sysctl.conf << EOF
# Network optimizations for video streaming
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_window_scaling = 1
EOF

sudo sysctl -p

echo "================================================"
echo "System optimization complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Run the main deploy.sh script"
echo "2. Videos will be automatically optimized for web streaming"
echo "3. Enjoy ultra-fast video playback!"
