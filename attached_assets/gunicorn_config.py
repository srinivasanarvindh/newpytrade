"""
PyTrade - Gunicorn Configuration

This file contains the Gunicorn configuration for serving the PyTrade Flask application
in a production environment. It configures worker processes, logging, and other
production-level settings.

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""

# Bind to this socket
bind = "127.0.0.1:5001"

# Number of worker processes
# A common formula is 2-4 x $(NUM_CORES)
workers = 4

# Worker type
worker_class = "gevent"

# Timeout (in seconds)
timeout = 120

# Log level
loglevel = "info"

# Log file locations
accesslog = "/var/log/pytrade/access.log"
errorlog = "/var/log/pytrade/error.log"

# Process name
proc_name = "pytrade_gunicorn"

# Prevent server header from being shown
server_name = "PyTrade Server"

# Redirect stdout/stderr to log file
capture_output = True

# Daemonize the Gunicorn process (run in background)
daemon = False  # We'll let systemd manage this

# Increase maximum requests per worker before recycling
max_requests = 1000
max_requests_jitter = 100

# Pre-load application code before forking workers
preload_app = True