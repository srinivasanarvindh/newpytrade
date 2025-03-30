#!/bin/bash
# PyTrade Service Setup Script
# This script sets up PyTrade as a systemd service for automatic startup

set -e

# Default paths - adjust as needed
DEPLOY_PATH="/home/apps.pykara.ai/public_html/py-trade"
VENV_PATH="/home/apps.pykara.ai/pytrade_venv"
SYSTEMD_PATH="/etc/systemd/system"
NGINX_PATH="/etc/nginx/sites-available"
LOG_PATH="/home/apps.pykara.ai/logs/pytrade"

# Create necessary directories
echo "Creating directories..."
sudo mkdir -p $DEPLOY_PATH
sudo mkdir -p $LOG_PATH

# Copy configuration files
echo "Copying configuration files..."
sudo cp pytrade.service $SYSTEMD_PATH/
sudo cp pytrade_nginx.conf $NGINX_PATH/pytrade
sudo ln -sf $NGINX_PATH/pytrade /etc/nginx/sites-enabled/

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    sudo python3 -m venv $VENV_PATH
fi

sudo $VENV_PATH/bin/pip install -U pip
sudo $VENV_PATH/bin/pip install -r requirements.txt
sudo $VENV_PATH/bin/pip install gunicorn gevent

# Copy application files
echo "Copying application files..."
sudo cp -r ./* $DEPLOY_PATH/

# Set permissions
echo "Setting permissions..."
sudo chown -R apps.pykara.ai:apps.pykara.ai $DEPLOY_PATH
sudo chown -R apps.pykara.ai:apps.pykara.ai $LOG_PATH
sudo chown -R apps.pykara.ai:apps.pykara.ai $VENV_PATH
sudo chmod -R 755 $DEPLOY_PATH

# Enable and start the service
echo "Enabling and starting PyTrade service..."
sudo systemctl daemon-reload
sudo systemctl enable pytrade.service
sudo systemctl start pytrade.service

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "--------------------------------------"
echo "PyTrade service setup complete!"
echo "Service status:"
sudo systemctl status pytrade.service
echo "--------------------------------------"
echo "Nginx configuration status:"
sudo nginx -t
echo "--------------------------------------"
echo "To check logs:"
echo "  Backend logs: sudo journalctl -u pytrade.service"
echo "  Access logs: sudo tail -f $LOG_PATH/access.log"
echo "  Error logs: sudo tail -f $LOG_PATH/error.log"
echo "--------------------------------------"