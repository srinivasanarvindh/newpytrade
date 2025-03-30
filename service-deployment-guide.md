# PyTrade Service Deployment Guide

This document provides instructions for deploying PyTrade as a systemd service on a Linux server. When set up as a service, PyTrade will start automatically when the server boots up and restart automatically if it crashes.

## Deployment Files

The following files are provided for deployment:

1. `pytrade.service` - Systemd service configuration
2. `pytrade_nginx.conf` - Nginx site configuration for reverse proxy
3. `wsgi.py` - WSGI entry point for the Flask application
4. `gunicorn_config.py` - Gunicorn configuration for production deployment
5. `setup_pytrade_service.sh` - Deployment automation script

## Prerequisites

- Ubuntu 20.04 LTS or newer (or similar Linux distribution)
- Python 3.8 or newer
- Nginx
- Systemd
- Root or sudo access
- SSL certificate for your domain (Let's Encrypt recommended)

## Deployment Steps

### 1. Prepare Your Environment

Make sure your server has the necessary software installed:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx
```

### 2. Obtain SSL Certificates

If you don't already have SSL certificates, you can get them for free from Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d apps.pykara.ai
```

### 3. Deploy Using the Automated Script

The easiest way to deploy PyTrade is to use the provided deployment script:

1. Copy all PyTrade files to your server
2. Make the deployment script executable:
   ```bash
   chmod +x setup_pytrade_service.sh
   ```
3. Run the deployment script:
   ```bash
   sudo ./setup_pytrade_service.sh
   ```

The script will:
- Copy files to the appropriate locations
- Set up a Python virtual environment
- Install required dependencies
- Configure systemd and Nginx
- Start the PyTrade service
- Display the status of the service

### 4. Manual Deployment Steps

If you prefer to deploy manually or the automated script doesn't work for your environment, follow these steps:

1. Copy the application files to the server:
   ```bash
   sudo mkdir -p /home/apps.pykara.ai/public_html/py-trade
   sudo cp -r ./* /home/apps.pykara.ai/public_html/py-trade/
   ```

2. Set up a Python virtual environment:
   ```bash
   sudo mkdir -p /home/apps.pykara.ai/pytrade_venv
   sudo python3 -m venv /home/apps.pykara.ai/pytrade_venv
   sudo /home/apps.pykara.ai/pytrade_venv/bin/pip install -U pip
   sudo /home/apps.pykara.ai/pytrade_venv/bin/pip install -r /home/apps.pykara.ai/public_html/py-trade/requirements.txt
   sudo /home/apps.pykara.ai/pytrade_venv/bin/pip install gunicorn gevent
   ```

3. Create log directories:
   ```bash
   sudo mkdir -p /home/apps.pykara.ai/logs/pytrade
   sudo chown -R apps.pykara.ai:apps.pykara.ai /home/apps.pykara.ai/logs/pytrade
   ```

4. Install the systemd service:
   ```bash
   sudo cp pytrade.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable pytrade.service
   sudo systemctl start pytrade.service
   ```

5. Configure Nginx in CWP:
   ```bash
   # For CWP installations, copy to the appropriate location
   sudo cp pytrade_nginx.conf /usr/local/cwpsrv/conf/cwp_apps.pykara.ai.conf
   # Or if using standard Nginx configuration
   sudo cp pytrade_nginx.conf /etc/nginx/conf.d/vhost_apps.pykara.ai.conf
   
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 5. Set Up Environment Variables

Create a `.env` file in the deployment directory with any necessary environment variables:

```bash
sudo vi /home/apps.pykara.ai/public_html/py-trade/.env
```

Add environment variables like:
```
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

### 6. Verify Deployment

Check if the service is running:
```bash
sudo systemctl status pytrade.service
```

Check the service logs:
```bash
sudo journalctl -u pytrade.service
```

Check the Nginx configuration:
```bash
sudo nginx -t
```

Visit the site in your browser: https://apps.pykara.ai/py-trade

## Troubleshooting

### 1. Service Won't Start

Check the logs for detailed error messages:
```bash
sudo journalctl -u pytrade.service
```

Common issues:
- Python dependencies missing
- Permission problems
- Path configuration errors

### 2. Nginx Configuration Problems

If Nginx fails to start or gives a configuration error:
```bash
sudo nginx -t
```

Common issues:
- SSL certificate paths incorrect
- Syntax errors in the configuration
- Port conflicts

### 3. Application Errors

Check the application logs:
```bash
sudo tail -f /home/apps.pykara.ai/logs/pytrade/pytrade_stderr.log
sudo tail -f /home/apps.pykara.ai/logs/pytrade/pytrade_stdout.log
```

### 4. Updating the Application

To update the application:
1. Copy new files to the deployment directory
2. Restart the service:
   ```bash
   sudo systemctl restart pytrade.service
   ```

## Service Management Commands

- Start the service: `sudo systemctl start pytrade.service`
- Stop the service: `sudo systemctl stop pytrade.service`
- Restart the service: `sudo systemctl restart pytrade.service`
- Check status: `sudo systemctl status pytrade.service`
- View logs: `sudo journalctl -u pytrade.service`
- Enable at boot: `sudo systemctl enable pytrade.service`
- Disable at boot: `sudo systemctl disable pytrade.service`