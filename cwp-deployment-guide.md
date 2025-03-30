# PyTrade CWP-Nginx Deployment Guide

This guide provides step-by-step instructions for deploying the PyTrade AI Trading Platform using Control Web Panel (CWP) with Nginx as the web server.

## Overview

The PyTrade platform consists of two main components:
1. **Angular Frontend**: Static files served by Nginx
2. **Flask Backend**: Python API server running as a service

The application will be accessible at the URL: https://apps.pykara.ai/py-trade

## Prerequisites

- Control Web Panel (CWP) installed and running
- Python 3.8 or newer
- Node.js 14 or newer (for building Angular)
- Access to CWP admin interface
- Domain configured in CWP (apps.pykara.ai)

## Deployment Steps

### 1. Prepare the Server Environment

1. Log in to your server via SSH:
   ```bash
   ssh root@your_server_ip
   ```

2. Install required dependencies:
   ```bash
   yum install -y python3 python3-devel python3-pip nginx git
   # For Ubuntu/Debian based systems
   # apt install -y python3 python3-dev python3-pip nginx git
   ```

3. Install Node.js and npm (if not already installed):
   ```bash
   curl -sL https://rpm.nodesource.com/setup_16.x | bash -
   yum install -y nodejs
   # For Ubuntu/Debian based systems
   # curl -sL https://deb.nodesource.com/setup_16.x | bash -
   # apt install -y nodejs
   ```

### 2. Create Web Domain in CWP

1. Log in to Control Web Panel admin interface
2. Navigate to "Account Functions" > "Create Account"
3. Create a new account or use an existing one
4. Set up the domain as apps.pykara.ai
5. Enable SSL for the domain (Let's Encrypt or custom certificate)

### 3. Deploy the Application Files

1. Navigate to the web document root (determined by CWP):
   ```bash
   cd /home/apps.pykara.ai/public_html
   ```

2. Create a 'py-trade' directory for PyTrade:
   ```bash
   mkdir -p py-trade
   cd py-trade
   ```

3. Clone or copy the PyTrade files to this directory:
   ```bash
   # If using git:
   git clone https://your-repository-url.git .
   
   # Or copy files directly:
   # cp -r /path/to/pytrade/* .
   ```

4. Build the Angular frontend:
   ```bash
   npm install
   npm run build
   ```

5. Set up Python virtual environment:
   ```bash
   cd /home/apps.pykara.ai
   python3 -m venv pytrade_venv
   source pytrade_venv/bin/activate
   pip install -U pip
   pip install -r public_html/py-trade/requirements.txt
   pip install gunicorn gevent
   deactivate
   ```

6. Create necessary directories:
   ```bash
   mkdir -p /home/apps.pykara.ai/logs/pytrade
   ```

### 4. Create a CWP Python Application (Optional)

If CWP supports Python applications:

1. In CWP, go to "Python Apps" section
2. Create a new Python application
3. Set the path to your application: `/home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py`
4. Set the virtual environment path: `/home/apps.pykara.ai/pytrade_venv`
5. Configure the application to run as a daemon

### 5. Configure the PyTrade Service

If not using CWP's built-in Python app functionality:

1. Create a service file:
   ```bash
   vi /etc/systemd/system/pytrade.service
   ```

2. Add the following content:
   ```ini
   [Unit]
   Description=PyTrade AI Trading Platform
   After=network.target

   [Service]
   User=apps.pykara.ai
   Group=apps.pykara.ai
   WorkingDirectory=/home/apps.pykara.ai/public_html/py-trade
   Environment="PATH=/home/apps.pykara.ai/pytrade_venv/bin"
   ExecStart=/home/apps.pykara.ai/pytrade_venv/bin/python /home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   systemctl daemon-reload
   systemctl enable pytrade.service
   systemctl start pytrade.service
   ```

### 6. Configure Nginx through CWP

1. In CWP, navigate to "Nginx Vhosts" section
2. Find your domain (apps.pykara.ai) and click "Edit"
3. Add the following to the domain's Nginx configuration (either through CWP interface or by editing the file directly):

   ```nginx
   # For the Angular frontend:
   location /py-trade {
       alias /home/apps.pykara.ai/public_html/py-trade/dist;
       try_files $uri $uri/ /py-trade/index.html =404;
       index index.html;
   }

   # For the Flask API:
   location /py-trade/api {
       proxy_pass http://127.0.0.1:5001/api;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 120s;
   }

   # For WebSockets:
   location /py-trade/ws {
       proxy_pass http://127.0.0.1:5003;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 86400;
   }
   ```

4. Save the configuration

5. Alternatively, you can edit the Nginx configuration file manually:
   ```bash
   vi /etc/nginx/conf.d/vhost_apps.pykara.ai.conf
   # or
   vi /usr/local/cwpsrv/conf/cwp_apps.pykara.ai.conf  # (location may vary based on CWP installation)
   ```

6. Restart Nginx:
   ```bash
   systemctl restart nginx
   # or
   service nginx restart
   ```

### 7. Set Up Environment Variables

Create a `.env` file for environment variables:

```bash
vi /home/apps.pykara.ai/public_html/py-trade/.env
```

Add required environment variables:
```
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

### 8. Setup Automated Service Start Script

Create a script to make service setup easier:

```bash
vi /home/apps.pykara.ai/public_html/py-trade/cwp-deployment.sh
```

Add the following content:

```bash
#!/bin/bash

# PyTrade Deployment Script for CWP
echo "Setting up PyTrade service..."

# Create directories
mkdir -p /home/apps.pykara.ai/logs/pytrade

# Setup virtual environment if not exists
if [ ! -d "/home/apps.pykara.ai/pytrade_venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv /home/apps.pykara.ai/pytrade_venv
    source /home/apps.pykara.ai/pytrade_venv/bin/activate
    pip install -U pip
    pip install -r /home/apps.pykara.ai/public_html/py-trade/requirements.txt
    pip install gunicorn gevent
    deactivate
fi

# Create service file
cat > /etc/systemd/system/pytrade.service << EOL
[Unit]
Description=PyTrade AI Trading Platform
After=network.target

[Service]
User=apps.pykara.ai
Group=apps.pykara.ai
WorkingDirectory=/home/apps.pykara.ai/public_html/py-trade
Environment="PATH=/home/apps.pykara.ai/pytrade_venv/bin"
ExecStart=/home/apps.pykara.ai/pytrade_venv/bin/python /home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/public_html/py-trade
chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/logs/pytrade
chmod -R 755 /home/apps.pykara.ai/public_html/py-trade
chmod +x /home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py

# Enable and start service
systemctl daemon-reload
systemctl enable pytrade.service
systemctl restart pytrade.service

echo "PyTrade service has been set up and started."
echo "Service status:"
systemctl status pytrade.service

echo "Next steps:"
echo "1. Configure Nginx in CWP to serve the application"
echo "2. Set up environment variables in /home/apps.pykara.ai/public_html/py-trade/.env"
echo "3. Access your application at https://apps.pykara.ai/py-trade"
```

Make the script executable:
```bash
chmod +x /home/apps.pykara.ai/public_html/py-trade/cwp-deployment.sh
```

### 9. Verify Deployment

1. Check if the service is running:
   ```bash
   systemctl status pytrade.service
   ```

2. Test the API endpoint:
   ```bash
   curl http://127.0.0.1:5001/api/indices
   ```

3. Check Nginx configuration:
   ```bash
   nginx -t
   ```

4. Test the website by visiting: https://apps.pykara.ai/py-trade

## Troubleshooting

### 1. Service Issues

If the service fails to start:
```bash
systemctl status pytrade.service
journalctl -u pytrade.service
```

Common issues:
- File paths or permissions
- Python dependencies
- Environment variables missing

### 2. Nginx Configuration Issues

If Nginx fails to load the site:
```bash
nginx -t
tail -f /var/log/nginx/error.log
```

Common issues:
- Path to Angular files incorrect
- Proxy configuration issues
- SSL certificate problems

### 3. Permission Issues

Check ownership and permissions:
```bash
ls -la /home/apps.pykara.ai/public_html/py-trade
ls -la /home/apps.pykara.ai/pytrade_venv
```

Fix permissions:
```bash
chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/public_html/py-trade
chmod -R 755 /home/apps.pykara.ai/public_html/py-trade
```

### 4. SELinux Issues (if applicable)

If SELinux is enabled:
```bash
setsebool -P httpd_can_network_connect 1
```

## Maintenance

### Updating the Application

1. Pull or copy the new files:
   ```bash
   cd /home/apps.pykara.ai/public_html/py-trade
   git pull  # if using git
   ```

2. Rebuild the Angular frontend if needed:
   ```bash
   npm install
   npm run build
   ```

3. Update Python dependencies if needed:
   ```bash
   source /home/apps.pykara.ai/pytrade_venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

4. Restart the service:
   ```bash
   systemctl restart pytrade.service
   ```

### Logs

- Service logs: `journalctl -u pytrade.service`
- Application logs: `/home/apps.pykara.ai/logs/pytrade/`
- Nginx access logs: `/var/log/nginx/apps.pykara.ai.access.log`
- Nginx error logs: `/var/log/nginx/apps.pykara.ai.error.log`

## Service Management Commands

- Start: `systemctl start pytrade.service`
- Stop: `systemctl stop pytrade.service`
- Restart: `systemctl restart pytrade.service`
- Status: `systemctl status pytrade.service`
- Enable at boot: `systemctl enable pytrade.service`
- Disable at boot: `systemctl disable pytrade.service`