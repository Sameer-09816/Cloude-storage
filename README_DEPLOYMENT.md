# Cloud Storage App - VPS Deployment Guide

![VPS Specifications](file:///C:/Users/sagar/.gemini/antigravity/brain/9d564082-a18b-4425-bd5a-bea1995ebdc1/uploaded_image_1764848422520.png)

## 🚀 Quick Deploy to Your Linode VPS

### VPS Details
- **IP Address**: `172.105.47.128`
- **CPUs**: 2 Cores
- **RAM**: 4 GB
- **Storage**: 80 GB
- **Region**: Mumbai, India

### Fast Deployment (Automated)

```bash
# 1. Connect to your VPS
ssh root@172.105.47.128

# 2. Upload the application code to VPS
# (Use SCP, SFTP, or Git to transfer files)

# 3. Run the deployment script
cd /path/to/cloud-storage
chmod +x deploy.sh
sudo bash deploy.sh
```

The script will automatically:
- Install all dependencies (Python, Nginx, etc.)
- Set up virtual environment
- Configure Nginx reverse proxy
- Create systemd service for auto-start
- Configure firewall
- Start the application

### Manual Deployment Steps

If you prefer manual deployment:

#### 1. Connect to VPS
```bash
ssh root@172.105.47.128
```

#### 2. Update System
```bash
sudo apt-get update && sudo apt-get upgrade -y
```

#### 3. Install Dependencies
```bash
sudo apt-get install -y python3 python3-pip python3-venv nginx git build-essential python3-dev libopencv-dev python3-opencv
```

#### 4. Create Application Directory
```bash
sudo mkdir -p /var/www/cloud-storage
cd /var/www/cloud-storage
```

#### 5. Upload Application Files
Transfer all files from your local machine to `/var/www/cloud-storage`:
- `app.py`
- `downloader.py`
- `config.py`
- `gunicorn_config.py`
- `requirements.txt`
- `templates/` folder
- `static/` folder

#### 6. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 7. Create Storage Directories
```bash
mkdir -p uploads downloads static/thumbnails
chmod 755 uploads downloads static/thumbnails
```

#### 8. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

#### 9. Setup Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/cloud-storage
sudo ln -s /etc/nginx/sites-available/cloud-storage /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

#### 10. Setup Systemd Service
```bash
sudo cp cloud-storage.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start cloud-storage
sudo systemctl enable cloud-storage
```

#### 11. Configure Firewall
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## 🎯 Access Your App

After deployment, access your app at:
- **URL**: `http://172.105.47.128`
- **Login**: `Sameerkom16@gmail.com`
- **Password**: `Sameerkom16@123`

## 📊 Performance Optimizations

### Download Speed Enhancements
- ✅ **8MB Chunk Size**: Increased from 1MB to 8MB for faster downloads
- ✅ **Connection Pooling**: Reuses HTTP connections for better performance
- ✅ **Concurrent Downloads**: Supports multiple simultaneous downloads
- ✅ **5 Retry Attempts**: Auto-retry with exponential backoff
- ✅ **60s Timeout**: Extended timeout for large files

### Server Configuration
- **Gunicorn Workers**: 4 workers (optimized for 2 CPU cores)
- **Max Upload Size**: 5GB
- **Nginx Buffer**: Disabled for streaming
- **Auto-restart**: On crashes or reboots

## 🔧 Useful Commands

### Check Service Status
```bash
sudo systemctl status cloud-storage
```

### View Live Logs
```bash
# Application logs
sudo journalctl -u cloud-storage -f

# Nginx access logs
sudo tail -f /var/log/nginx/cloud-storage-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/cloud-storage-error.log
```

### Restart Services
```bash
# Restart application
sudo systemctl restart cloud-storage

# Restart Nginx
sudo systemctl restart nginx
```

### Update Application
```bash
cd /var/www/cloud-storage
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt
sudo systemctl restart cloud-storage
```

## 🔒 Security Considerations

### Recommended Next Steps:
1. **Add SSL Certificate** (Let's Encrypt):
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Change Default Password**:
   Edit the `.env` file and update `ADMIN_PASSWORD`

3. **Generate New Secret Key**:
   ```bash
   openssl rand -hex 32
   ```
   Update `SECRET_KEY` in `.env`

4. **Configure Rate Limiting** (optional):
   Add to Nginx config for DDoS protection

## 📁 File Structure on VPS

```
/var/www/cloud-storage/
├── app.py                    # Main application
├── downloader.py             # Download logic
├── config.py                 # Configuration
├── gunicorn_config.py        # Gunicorn settings
├── requirements.txt          # Python dependencies
├── venv/                     # Virtual environment
├── templates/                # HTML templates
│   ├── index.html
│   └── login.html
├── static/                   # Static assets
│   ├── style.css
│   ├── script.js
│   └── thumbnails/          # Auto-generated
├── uploads/                  # User uploads
├── downloads/                # URL downloads
└── .env                      # Environment variables (secret)
```

## 🐛 Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo journalctl -u cloud-storage -n 50

# Verify Python environment
source /var/www/cloud-storage/venv/bin/activate
python -c "import flask; print('OK')"
```

### Nginx 502 Error
```bash
# Check if Gunicorn is running
sudo systemctl status cloud-storage

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Upload Fails
```bash
# Check disk space
df -h

# Check permissions
ls -la /var/www/cloud-storage/uploads
```

### Download Slow
- Check VPS network speed
- Monitor CPU/RAM usage: `htop`
- Check if multiple downloads are running

## 📈 Monitoring

### Resource Usage
```bash
# CPU and RAM
htop

# Disk usage
df -h
du -sh /var/www/cloud-storage/*

# Network
iftop
```

### Performance
- **Expected Download Speed**: Up to VPS network limit
- **Concurrent Users**: 10-20 (with current 4 workers)
- **Max File Size**: 5GB (configurable)

## 🎉 Success!

Your cloud storage app is now production-ready and optimized for your Linode VPS!

**Test Download Performance**:
1. Login to the app
2. Use "Download from URL" feature
3. Monitor download speed in progress bar
4. Downloads should be significantly faster with 8MB chunks

**Need Help?**
- Check logs: `sudo journalctl -u cloud-storage -f`
- Restart app: `sudo systemctl restart cloud-storage`
- Review configuration files
