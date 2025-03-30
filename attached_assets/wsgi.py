"""
PyTrade - WSGI Entry Point

This file serves as the WSGI entry point for the PyTrade application,
allowing it to be served by production WSGI servers like Gunicorn or uWSGI.
It imports the Flask application from simplified_pytrade.py.

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""

import sys
import os

# Add the directory containing simplified_pytrade.py to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'attached_assets')))

# Import the app from the simplified_pytrade module
from simplified_pytrade import app as application

# This allows the application to be imported by WSGI servers
if __name__ == '__main__':
    application.run()