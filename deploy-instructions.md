# Deployment Guide for PyTrade on CWP (Control Web Panel)

This guide provides instructions for deploying the PyTrade application to a server using Control Web Panel at the URL apps.pykara.ai/py-trade.

## Prerequisites

- Access to your Control Web Panel (CWP) account
- SSH access to your server (if available)
- Git installed on your server (for cloning the project)
- Node.js/npm installed on your server (for Angular build)
- Python 3.x installed on your server
- Database credentials (if applicable)

## Deployment Steps

### 1. Prepare Your Angular App for Production

On your local machine or on Replit:

```bash
# Navigate to your project directory
cd /path/to/pytrade

# Build the Angular app for production with the correct base href
npx ng build --configuration production --base-href '/py-trade/'
```

The build output will be in the `dist/` directory.

### 2. Set Up the Directory Structure on Your Server

Use CWP or SSH to create the necessary directories:

```bash
# Create application directory
mkdir -p /home/apps.pykara.ai/public_html/py-trade
```

### 3. Deploy Backend (Flask)

Upload these Python files and directories to your server:
- `attached_assets/` folder (contains Python backend files)
- Requirements file (requirements.txt or pyproject.toml)

### 4. Deploy Frontend (Angular)

Upload the contents of the `dist/` directory (from your Angular build) to:
```
/home/apps.pykara.ai/public_html/py-trade/dist/
```

### 5. Configure Web Server

Using Control Web Panel, set up a subdomain for your application:

1. Log in to your CWP panel
2. Go to 'Domains' > 'Subdomains'
3. Create a new subdomain: `apps.pykara.ai`
4. Set the document root to: `/home/apps.pykara.ai/public_html`
5. Enable SSL if needed

### 6. Set Up Python Environment

Using SSH or the CWP terminal:

```bash
# Navigate to your application directory
cd /home/apps.pykara.ai/public_html/py-trade

# Create a virtual environment (optional but recommended)
python3 -m venv /home/apps.pykara.ai/pytrade_venv
source /home/apps.pykara.ai/pytrade_venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 7. Configure WSGI Application

Create a WSGI configuration file in your application directory:

```python
# wsgi.py
import sys
import os

# Add application directory to path
sys.path.insert(0, '/home/apps.pykara.ai/public_html/py-trade')

# Import the Flask application
from attached_assets.simplified_pytrade import app as application
```

### 8. Configure Proxy Settings

Use CWP to set up a reverse proxy that will route API requests to your Flask application:

1. In CWP, go to 'Web Server' > 'Apache Configuration' or 'Nginx Configuration'
2. Add the following to the virtual host configuration for `apps.pykara.ai`:

```nginx
# For Nginx:
location /py-trade/api {
    proxy_pass http://localhost:5001/api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location /py-trade/google_login {
    proxy_pass http://localhost:5001/google_login;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location /py-trade/ws {
    proxy_pass http://localhost:5003;
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

### 9. Start Flask Application using Gunicorn or uWSGI

Set up a systemd service to run your Flask application:

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/pytrade.service
```

Add the following content:

```
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

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pytrade.service
sudo systemctl start pytrade.service
```

### 10. Update Environment Variables

Create a `.env` file in your application directory to store environment variables:

```
FLASK_APP=attached_assets/simplified_pytrade.py
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
REPLIT_DEV_DOMAIN=apps.pykara.ai/py-trade
```

### 11. Final Steps and Verification

1. Restart your web server:
   ```bash
   sudo systemctl restart nginx  # or apache2/httpd depending on your system
   ```

2. Test your application by navigating to `https://apps.pykara.ai/py-trade` in your browser

## Troubleshooting

- Check web server error logs: `/var/log/httpd/error_log` or similar
- Check application logs: Look for output in the systemd journal using `journalctl -u pytrade`
- Ensure all file permissions are set correctly
- Verify that all required ports are open in your firewall

## Maintenance

- Set up regular backups of your application code and database
- Monitor application performance and logs
- Keep dependencies updated to address security issues