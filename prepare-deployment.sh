#!/bin/bash
# Script to prepare PyTrade for deployment to apps.pykara.ai/py-trade

# Create deployment directories
mkdir -p deploy/frontend
mkdir -p deploy/backend

# Build the Angular frontend
echo "Building Angular frontend for production..."
cd .
npx ng build --configuration production --base-href '/py-trade/'

# Copy frontend build files
echo "Copying frontend build files..."
cp -r dist/* deploy/frontend/

# Copy backend files
echo "Copying backend files..."
cp -r attached_assets/* deploy/backend/
cp .env deploy/backend/
cp pyproject.toml deploy/backend/
cp proxy.conf.json deploy/backend/

# Create necessary configuration files
echo "Creating configuration files..."

# Create wsgi.py file
cat > deploy/backend/wsgi.py << 'EOF'
import sys
import os

# Add application directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
from simplified_pytrade import app as application
EOF

# Create systemd service file
cat > deploy/pytrade.service << 'EOF'
[Unit]
Description=PyTrade Flask Application
After=network.target

[Service]
User=apps.pykara.ai
Group=apps.pykara.ai
WorkingDirectory=/home/apps.pykara.ai/public_html/py-trade
Environment="PATH=/home/apps.pykara.ai/pytrade_venv/bin"
ExecStart=/home/apps.pykara.ai/pytrade_venv/bin/python /home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py
Restart=always
RestartSec=10

# Log files
StandardOutput=append:/home/apps.pykara.ai/logs/pytrade/pytrade_stdout.log
StandardError=append:/home/apps.pykara.ai/logs/pytrade/pytrade_stderr.log

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration file for proxy
cat > deploy/pytrade-nginx-config.conf << 'EOF'
# PyTrade Nginx configuration for apps.pykara.ai/py-trade
location /py-trade {
    alias /home/apps.pykara.ai/public_html/py-trade/dist;
    try_files $uri $uri/ /py-trade/index.html =404;
    index index.html;
}

# API Proxy Configuration
location /py-trade/api {
    proxy_pass http://127.0.0.1:5001/api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location /py-trade/google_login {
    proxy_pass http://127.0.0.1:5001/google_login;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

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
EOF

# Create installation instructions
cat > deploy/INSTALL.txt << 'EOF'
PyTrade Deployment Instructions
==============================

1. Create necessary directories:
   mkdir -p /home/apps.pykara.ai/public_html/py-trade/dist
   mkdir -p /home/apps.pykara.ai/logs/pytrade
   mkdir -p /home/apps.pykara.ai/pytrade_venv

2. Upload the "frontend" folder contents to: /home/apps.pykara.ai/public_html/py-trade/dist
3. Upload the "backend" folder contents to: /home/apps.pykara.ai/public_html/py-trade/attached_assets
4. Upload the Nginx configuration file to: /usr/local/cwpsrv/conf/cwp_apps.pykara.ai.conf (or use CWP to add it)
5. Upload the systemd service file to: /etc/systemd/system/pytrade.service

6. Set up the Python environment:
   cd /home/apps.pykara.ai/
   python3 -m venv pytrade_venv
   source pytrade_venv/bin/activate
   pip install -r /home/apps.pykara.ai/public_html/py-trade/requirements.txt
   deactivate

7. Set proper permissions:
   chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/public_html/py-trade
   chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/pytrade_venv
   chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/logs/pytrade
   chmod -R 755 /home/apps.pykara.ai/public_html/py-trade
   chmod +x /home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py

8. Start the service:
   sudo systemctl daemon-reload
   sudo systemctl enable pytrade.service
   sudo systemctl start pytrade.service

9. Restart Nginx:
   sudo systemctl restart nginx

10. Test your deployment by visiting: https://apps.pykara.ai/py-trade
EOF

# Create a README file
cat > deploy/README.md << 'EOF'
# PyTrade Deployment Package

This package contains everything needed to deploy PyTrade to a Control Web Panel (CWP) server.

## Package Contents

- `frontend/` - Angular frontend build files
- `backend/` - Flask backend files
- `pytrade.service` - Systemd service configuration
- `pytrade-nginx-config.conf` - Nginx proxy configuration
- `INSTALL.txt` - Step by step installation instructions

Follow the instructions in INSTALL.txt to complete the deployment.
EOF

# Create zip file
echo "Creating deployment package..."
cd deploy
zip -r ../pytrade-deployment.zip ./*
cd ..

echo "Deployment package created: pytrade-deployment.zip"
echo "Upload this package to your CWP server and follow the instructions in INSTALL.txt"