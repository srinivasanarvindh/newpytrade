# PyTrade CWP Deployment Checklist

Use this checklist to ensure all steps are completed when deploying PyTrade on a server with Control Web Panel (CWP) and Nginx.

## Pre-Deployment

- [ ] CWP is installed and configured on the server
- [ ] Domain (apps.pykara.ai) is set up in CWP
- [ ] SSL certificate is installed for the domain
- [ ] Python 3.8+ is installed on the server
- [ ] Node.js is installed for building Angular
- [ ] Server has at least 2GB of RAM and 10GB of free disk space
- [ ] Required API keys and secrets are available (Google OAuth, Alpha Vantage)

## Initial Setup

- [ ] Domain account is created in CWP
- [ ] Web directory structure is created in /home/apps.pykara.ai/public_html
- [ ] PyTrade code is transferred to /home/apps.pykara.ai/public_html/py-trade
- [ ] Log directory is created at /home/apps.pykara.ai/logs/pytrade
- [ ] Python virtual environment is created at /home/apps.pykara.ai/pytrade_venv
- [ ] Required Python dependencies are installed in the virtual environment
- [ ] Environment variables are set in .env file

## Angular Frontend

- [ ] Node.js dependencies are installed (npm install)
- [ ] Angular application is built (npm run build)
- [ ] Verify that the /dist directory is created and contains index.html
- [ ] Verify that all static assets (CSS, JS, images) are included in the build

## Backend Configuration

- [ ] SystemD service file is created at /etc/systemd/system/pytrade.service
- [ ] Service file has correct paths and user/group settings
- [ ] Service is enabled to start on boot (systemctl enable pytrade.service)
- [ ] Service is started and running (systemctl start pytrade.service)
- [ ] Service logs are being written to the correct location

## Nginx Configuration

- [ ] CWP Nginx configuration includes the PyTrade locations
- [ ] Configuration has correct paths for the Angular frontend files
- [ ] API proxy is configured correctly to pass to Flask backend (port 5001)
- [ ] WebSocket proxy is configured correctly (port 5003)
- [ ] Configuration is tested (nginx -t) and valid
- [ ] Nginx is restarted to apply the new configuration

## Final Testing

- [ ] Website loads correctly at https://apps.pykara.ai/py-trade
- [ ] Angular routes work correctly (no 404 errors when navigating)
- [ ] API endpoints are accessible (e.g., /py-trade/api/indices)
- [ ] WebSocket connection works for real-time data
- [ ] Google OAuth login functions correctly
- [ ] No errors appear in browser console
- [ ] No errors in Flask backend logs
- [ ] No errors in Nginx error logs

## Security

- [ ] Sensitive files (.env, .git) are not accessible from the web
- [ ] All connections use HTTPS
- [ ] API endpoints are properly protected if required
- [ ] File permissions are set correctly (755 for directories, 644 for files)
- [ ] SELinux permissions are set if SELinux is enabled

## Maintenance Plan

- [ ] Regular backup procedure is established
- [ ] Update process is documented
- [ ] Monitoring is set up for the service
- [ ] Log rotation is configured
- [ ] Contact information is available for support

## Documentation

- [ ] Deployment details are documented
- [ ] Server configuration is documented
- [ ] Admin access details are securely stored
- [ ] Troubleshooting guide is available

---

## Quick Reference Commands

### Service Management

```bash
# Start the service
systemctl start pytrade.service

# Stop the service
systemctl stop pytrade.service

# Restart the service
systemctl restart pytrade.service

# Check service status
systemctl status pytrade.service

# View service logs
journalctl -u pytrade.service
```

### Nginx Management

```bash
# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# Check Nginx status
systemctl status nginx

# View Nginx error logs
tail -f /var/log/nginx/error.log
```

### File Locations

- Angular frontend: `/home/apps.pykara.ai/public_html/py-trade/dist`
- Flask backend: `/home/apps.pykara.ai/public_html/py-trade/attached_assets/simplified_pytrade.py`
- Python virtual environment: `/home/apps.pykara.ai/pytrade_venv`
- Service logs: `/home/apps.pykara.ai/logs/pytrade/`
- Nginx configuration: `/usr/local/cwpsrv/conf/cwp_apps.pykara.ai.conf` or `/etc/nginx/conf.d/vhost_apps.pykara.ai.conf`
- Service configuration: `/etc/systemd/system/pytrade.service`
- Environment variables: `/home/apps.pykara.ai/public_html/py-trade/.env`