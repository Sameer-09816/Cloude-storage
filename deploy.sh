#!/bin/bash
#
# Deployment script for Cloud Storage App on Linode VPS
# Run this script on your VPS: bash deploy.sh
#

set -e  # Exit on error

echo "================================"
echo "Cloud Storage Deployment Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="cloud-storage"
APP_DIR="/var/www/${APP_NAME}"
USER="www-data"
VENV_DIR="${APP_DIR}/venv"
LOG_DIR="/var/log/${APP_NAME}"

# Step 1: Update system
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    git \
    build-essential \
    python3-dev \
    libopencv-dev \
    python3-opencv

# Step 3: Create application directory
echo -e "${YELLOW}Step 3: Setting up application directory...${NC}"
sudo mkdir -p ${APP_DIR}
sudo mkdir -p ${LOG_DIR}
sudo chown -R ${USER}:${USER} ${APP_DIR}
sudo chown -R ${USER}:${USER} ${LOG_DIR}

# Step 4: Create virtual environment
echo -e "${YELLOW}Step 4: Creating Python virtual environment...${NC}"
cd ${APP_DIR}
sudo -u ${USER} python3 -m venv ${VENV_DIR}

# Step 5: Upload/Copy application files
echo -e "${YELLOW}Step 5: Copying application files...${NC}"
echo "Please manually copy your application files to: ${APP_DIR}"
echo "Files needed: app.py, downloader.py, config.py, gunicorn_config.py"
echo "Folders needed: templates/, static/, uploads/, downloads/"
read -p "Press ENTER when files are copied..."

# Step 6: Install Python dependencies
echo -e "${YELLOW}Step 6: Installing Python dependencies...${NC}"
cd ${APP_DIR}
sudo -u ${USER} ${VENV_DIR}/bin/pip install --upgrade pip
sudo -u ${USER} ${VENV_DIR}/bin/pip install -r requirements.txt

# Step 7: Create upload/download directories
echo -e "${YELLOW}Step 7: Creating storage directories...${NC}"
sudo -u ${USER} mkdir -p ${APP_DIR}/uploads
sudo -u ${USER} mkdir -p ${APP_DIR}/downloads
sudo -u ${USER} mkdir -p ${APP_DIR}/static/thumbnails
sudo chmod 755 ${APP_DIR}/uploads
sudo chmod 755 ${APP_DIR}/downloads
sudo chmod 755 ${APP_DIR}/static/thumbnails

# Step 8: Configure Nginx
echo -e "${YELLOW}Step 8: Configuring Nginx...${NC}"
sudo cp ${APP_DIR}/nginx.conf /etc/nginx/sites-available/${APP_NAME}
sudo ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Step 9: Configure Systemd service
echo -e "${YELLOW}Step 9: Setting up Systemd service...${NC}"
sudo cp ${APP_DIR}/cloud-storage.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start ${APP_NAME}
sudo systemctl enable ${APP_NAME}

# Step 10: Configure firewall
echo -e "${YELLOW}Step 10: Configuring firewall...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (for future SSL)
sudo ufw --force enable

# Step 11: Set environment variables
echo -e "${YELLOW}Step 11: Setting environment variables...${NC}"
sudo bash -c "cat > ${APP_DIR}/.env << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_EMAIL=Sameerkom16@gmail.com
ADMIN_PASSWORD=Sameerkom16@123
HOST=0.0.0.0
PORT=5000
EOF"
sudo chown ${USER}:${USER} ${APP_DIR}/.env
sudo chmod 600 ${APP_DIR}/.env

# Step 12: Check status
echo -e "${YELLOW}Step 12: Checking service status...${NC}"
sudo systemctl status ${APP_NAME} --no-pager

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Your app is now running at: http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo journalctl -u ${APP_NAME} -f"
echo "  - Restart app: sudo systemctl restart ${APP_NAME}"
echo "  - Check status: sudo systemctl status ${APP_NAME}"
echo "  - Nginx logs: sudo tail -f /var/log/nginx/cloud-storage-*.log"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test the application at http://$(curl -s ifconfig.me)"
echo "2. Login with: Sameerkom16@gmail.com / Sameerkom16@123"
echo "3. Configure SSL certificate (optional but recommended)"
echo ""
