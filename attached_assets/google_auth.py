"""
PyTrade - Google Authentication Module

This module provides Google OAuth2 authentication functionality for the PyTrade application.
It handles the complete OAuth flow with Google, including authorization, token exchange, 
user profile retrieval, and session management.

Key features:
- Google OAuth 2.0 authentication flow implementation
- Secure user authentication and authorization
- User profile data retrieval from Google
- Session management and persistence
- Secure logout functionality
- Environment-aware configuration (development/production)

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""
import json
import os

import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

# These will be set from environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Get the application domain from environment variables
APP_DOMAIN = os.environ.get("APP_DOMAIN", "apps.pykara.ai/py-trade")
REDIRECT_URL = f'https://{APP_DOMAIN}/google_login/callback'

# Print the actual URL being used for easier debugging
print(f"Using redirect URL: {REDIRECT_URL}")

# Display setup instructions to the user
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {REDIRECT_URL} to Authorized redirect URIs
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None
google_auth = Blueprint("google_auth", __name__)

# User model will be imported from main app

@google_auth.route("/google_login")
def login():
    """
    Initiate the Google OAuth login flow
    """
    if not client:
        return "Google OAuth credentials not configured", 500
    
    print(f"Google login initiated, Client ID: {GOOGLE_CLIENT_ID[:8]}...")
    print(f"Using redirect URL: {REDIRECT_URL}")
        
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Using the exact redirect URL we've registered with Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=REDIRECT_URL,
        scope=["openid", "email", "profile"],
    )
    print(f"Redirecting to Google: {request_uri}")
    return redirect(request_uri)


@google_auth.route("/google_login/callback")
def callback():
    """
    Handle the callback from Google OAuth
    """
    print(f"Google callback received, URL: {request.url}")
    
    if not client:
        return "Google OAuth credentials not configured", 500
    
    # Check for error in the callback
    if 'error' in request.args:
        error = request.args.get('error')
        print(f"Error in Google callback: {error}")
        return f"Authentication failed: {error}", 400
        
    code = request.args.get("code")
    print(f"Auth code received: {code[:8]}..." if code else "No auth code received")
    
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Using the exact redirect URL we've registered with Google for consistency
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=REDIRECT_URL,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        users_email = userinfo["email"]
        users_name = userinfo["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Find or create the user in the database
    from attached_assets.simplified_pytrade import User, db
    
    user = None
    
    # Check if user exists, otherwise create new user
    # For simplified version, we'll just create a new user
    if not user:
        user = User(None, users_name, users_email)
        db.session.add(user)
        db.session.commit()

    login_user(user)

    return redirect(url_for("home"))


@google_auth.route("/logout")
@login_required
def logout():
    """
    Handle user logout
    """
    logout_user()
    return redirect(url_for("home"))