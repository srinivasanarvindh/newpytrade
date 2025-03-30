#!/bin/bash

# PyTrade Deployment Script for Control Web Panel (CWP)
# This script automates the deployment of PyTrade on a server using Control Web Panel with Nginx
# Author: PyTrade Team
# Date: March 25, 2025

# Exit on any error
set -e

# Configuration
DOMAIN="apps.pykara.ai"
APP_DIR="/home/$DOMAIN/public_html/py-trade"
VENV_DIR="/home/$DOMAIN/pytrade_venv"
LOG_DIR="/home/$DOMAIN/logs/pytrade"
USER="$DOMAIN"
GROUP="$DOMAIN"
PORT_FLASK=5001
PORT_WEBSOCKET=5003
PYTHON_APP="attached_assets/simplified_pytrade.py"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root" >&2
  exit 1
fi

# Display banner
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║             PyTrade CWP Deployment Script                  ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# Create directories
echo "Creating necessary directories..."
mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$VENV_DIR"

# Setup virtual environment
if [ ! -f "$VENV_DIR/bin/activate" ]; then
  echo "Setting up Python virtual environment..."
  python3 -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  pip install --upgrade pip
  
  if [ -f "$APP_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies from requirements.txt..."
    pip install -r "$APP_DIR/requirements.txt"
  else
    echo "Installing common Python dependencies..."
    pip install flask flask-cors flask-login flask-wtf gunicorn gevent yfinance pandas numpy nsepython nsetools bsedata python-dotenv websockets requests
  fi
  
  deactivate
else
  echo "Python virtual environment already exists."
fi

# Create systemd service file
echo "Creating systemd service file for PyTrade..."
cat > /etc/systemd/system/pytrade.service << EOL
[Unit]
Description=PyTrade AI Trading Platform
After=network.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python $APP_DIR/$PYTHON_APP
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
systemctl daemon-reload

# Check if Nginx config directory exists
NGINX_CONF_DIR="/etc/nginx/conf.d"
CWP_NGINX_CONF_DIR="/usr/local/cwpsrv/conf"

if [ -d "$NGINX_CONF_DIR" ]; then
  NGINX_CONFIG_PATH="$NGINX_CONF_DIR/vhost_$DOMAIN.conf"
elif [ -d "$CWP_NGINX_CONF_DIR" ]; then
  NGINX_CONFIG_PATH="$CWP_NGINX_CONF_DIR/cwp_$DOMAIN.conf"
else
  echo "Could not determine Nginx configuration directory."
  echo "You'll need to manually configure Nginx for this domain."
  NGINX_CONFIG_PATH=""
fi

# Create Nginx configuration
if [ -n "$NGINX_CONFIG_PATH" ]; then
  echo "Creating Nginx configuration for $DOMAIN..."
  
  # Check if the file exists and contains our configuration already
  if grep -q "/py-trade {" "$NGINX_CONFIG_PATH" 2>/dev/null; then
    echo "Nginx configuration for PyTrade already exists."
  else
    # Backup the original config
    cp "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_PATH.bak.$(date +%Y%m%d%H%M%S)"
    
    # Find the end of the server block
    if [ -f "$NGINX_CONFIG_PATH" ]; then
      # Insert our configuration before the closing brace of the server block
      sed -i '/}/i \
    # PyTrade Angular frontend\
    location /py-trade {\
        alias '"$APP_DIR"'/dist;\
        try_files $uri $uri/ /py-trade/index.html =404;\
        index index.html;\
    }\
\
    # PyTrade Flask API\
    location /py-trade/api {\
        proxy_pass http://127.0.0.1:'"$PORT_FLASK"'/api;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 120s;\
    }\
\
    # PyTrade WebSocket\
    location /py-trade/ws {\
        proxy_pass http://127.0.0.1:'"$PORT_WEBSOCKET"';\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 86400;\
    }' "$NGINX_CONFIG_PATH"
    else
      echo "Nginx configuration file does not exist yet. You'll need to create it manually."
    fi
  fi
fi

# Set permissions
echo "Setting permissions..."
chown -R "$USER:$GROUP" "$APP_DIR"
chown -R "$USER:$GROUP" "$VENV_DIR"
chown -R "$USER:$GROUP" "$LOG_DIR"
chmod -R 755 "$APP_DIR"
chmod +x "$APP_DIR/$PYTHON_APP"

# Enable SELinux permissions if SELinux is enabled
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
  echo "Configuring SELinux permissions..."
  setsebool -P httpd_can_network_connect 1
fi

# Enable and start PyTrade service
echo "Enabling and starting PyTrade service..."
systemctl enable pytrade.service
systemctl restart pytrade.service

# Check service status
echo "PyTrade service status:"
systemctl status pytrade.service

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
  echo "Creating .env file template..."
  cat > "$APP_DIR/.env" << EOL
# PyTrade Environment Variables
# Add your API keys and secrets below

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here

# Alpha Vantage API Key (for stock data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Optional: MongoDB connection string (if using MongoDB)
# MONGODB_URI=mongodb://username:password@hostname:port/database

# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=generate_a_strong_secret_key_here
EOL

  echo "Please update the .env file with your API keys and secrets."
fi

# Restart Nginx
echo "Restarting Nginx..."
if command -v systemctl &> /dev/null; then
  systemctl restart nginx
else
  service nginx restart
fi

# Done
echo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║             PyTrade Deployment Complete!                   ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Your PyTrade application should now be accessible at:"
echo "https://$DOMAIN/py-trade"
echo
echo "Important paths:"
echo "- Application files: $APP_DIR"
echo "- Python virtual environment: $VENV_DIR"
echo "- Log directory: $LOG_DIR"
echo "- Service config: /etc/systemd/system/pytrade.service"
echo
echo "Next steps:"
echo "1. Build the Angular frontend (cd $APP_DIR && npm install && npm run build)"
echo "2. Configure your environment variables in $APP_DIR/.env"
echo "3. Restart the PyTrade service: systemctl restart pytrade.service"
echo
echo "For any issues, check the service logs with: journalctl -u pytrade.service"
echo