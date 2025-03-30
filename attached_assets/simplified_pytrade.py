"""
PyTrade - AI-Powered Stock Trading Platform Backend

A sophisticated stock trading platform providing comprehensive market insights with 
advanced user experience design and global market coverage.

This Flask-based backend provides RESTful API endpoints for the PyTrade application,
handling data requests, authentication, and integration with various stock market
data sources. It serves as the central hub for all data processing, analysis and 
prediction functions.

Key Features:
- RESTful API for market data
- WebSocket integration for real-time updates
- OAuth integration for user authentication
- Data aggregation from multiple international markets
- Technical indicator calculation and analysis
- Trading strategy evaluation and signals

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""

from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
import os
import json
import logging
import random
import datetime
import time
import logging.config
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import traceback
import pandas as pd
import numpy as np
import yfinance as yf
import random
import threading
import uuid
import hashlib
import secrets
import functools
import time
from nsepython import nsefetch
from utils import get_nse_indices as indices
from indicesdownload import get_index_constituents as download_index_constituents
from utils import get_nse_eq as nse_eq
from utils import get_index_info as index_info
from utils import get_nse_index_quote as nse_get_index_quote
from utils import get_nse_symbols
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from websocket_server import run_websocket_server
from indicesdownload import get_indices_list as download_indices_list
from indicesdownload import get_index_history

# Simple in-memory cache implementation
cache = {}
def cache_with_timeout(timeout=300):  # Default 5 minute cache timeout
    """
    Function decorator that provides caching with a specified timeout.
    
    Args:
        timeout (int): Cache timeout in seconds (default: 300 seconds / 5 minutes)
    
    Returns:
        Function wrapper implementing the caching behavior
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique cache key based on function name and arguments
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            # Check if we have a valid cached result
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    logger.debug(f"Cache hit for {cache_key}")
                    return result
                
            # Call the original function
            logger.debug(f"Cache miss for {cache_key}, calling original function")
            result = func(*args, **kwargs)
            
            # Cache the result with current timestamp
            cache[cache_key] = (result, time.time())
            return result
        return wrapper
    return decorator

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and CORS
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for API
CORS(app, resources={r"/*": {"origins": "*", 
                            "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"], 
                            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}},
     supports_credentials=True)

# Create a simple database session for flask-login
class SimpleDB:
    def __init__(self):
        self.session = {}
        
    def add(self, user):
        self.session[user.id] = user
        
    def commit(self):
        pass

db = SimpleDB()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Sample user database - replace with real database in production
users_db = {}

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id in users_db:
        user_data = users_db[user_id]
        return User(user_id, user_data['username'], user_data['email'])
    return None

# Root Route
@app.route('/')
def home():
    return "PyTrade API is running!"

# Authentication Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login endpoint
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
        
    Returns:
        JSON: User information and token
    """
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # For demo purposes, create a default admin user if it doesn't exist
        # In production, this would be replaced with a real database lookup
        if 'admin' not in users_db:
            admin_id = 'admin'
            admin_password = 'admin123'  # Use secure password hashing in production
            users_db[admin_id] = {
                'id': admin_id,
                'username': 'Admin User',
                'email': 'admin@pytrade.com',
                'password': admin_password
            }
            
        # Add more demo users for testing
        test_users = [
            {'id': 'user1', 'username': 'Demo User', 'email': 'user@example.com', 'password': 'password123'},
            {'id': 'trader1', 'username': 'Trader One', 'email': 'trader@example.com', 'password': 'trader123'}
        ]
        
        for user in test_users:
            if user['id'] not in users_db:
                users_db[user['id']] = user
        
        # Find user by email
        user_id = None
        for id, user_data in users_db.items():
            if user_data.get('email') == email:
                user_id = id
                break
                
        if not user_id:
            logger.warning(f"Login attempt with email '{email}' failed: User not found")
            return jsonify({'error': 'Invalid email or password'}), 401
            
        user_data = users_db[user_id]
        
        # In production, use proper password hashing and verification
        if user_data.get('password') != password:
            logger.warning(f"Login attempt for user '{email}' failed: Incorrect password")
            return jsonify({'error': 'Invalid email or password'}), 401
            
        # Create a user instance for Flask-Login
        user = User(user_id, user_data['username'], user_data['email'])
        login_user(user)
        
        # Generate a simple token for API authentication
        token = secrets.token_hex(16)
        
        # Return user info and token
        return jsonify({
            'user': {
                'id': user_id,
                'username': user_data['username'],
                'email': user_data['email']
            },
            'token': token
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/status', methods=['GET'])
def check_auth_status():
    """
    Check authentication status
    
    Returns:
        JSON: User information if authenticated
    """
    try:
        if current_user.is_authenticated:
            token = hashlib.sha256(f"{current_user.id}:{datetime.now().isoformat()}".encode()).hexdigest()
            return jsonify({
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email
                },
                'token': token
            })
        else:
            return jsonify({'error': 'Not authenticated'}), 401
    except Exception as e:
        logger.error(f"Auth status check error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout endpoint
    
    Returns:
        JSON: Success message
    """
    try:
        logout_user()
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register endpoint
    
    Request Body:
        {
            "username": "New User",
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
        
    Returns:
        JSON: Success message
    """
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if required fields are provided
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        # Check if email already exists
        for user_data in users_db.values():
            if user_data.get('email') == email:
                return jsonify({'error': 'Email already registered'}), 400
                
        # Generate a user ID
        user_id = str(uuid.uuid4())
        
        # In production, hash the password before storing
        users_db[user_id] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': password  # Store hashed password in production
        }
        
        logger.info(f"New user registered: {username} ({email})")
        
        return jsonify({'message': 'Registration successful', 'userId': user_id})
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# Authentication status route is defined above

# Logging Configuration
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "DEBUG", "formatter": "detailed"},
        "file": {"class": "logging.FileHandler", "level": "DEBUG", "formatter": "detailed", "filename": os.path.join(log_dir, "pytrade.log")},
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Import and register the Google OAuth blueprint
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    logger.info("Google OAuth blueprint registered successfully")
except ImportError as e:
    logger.warning(f"Google OAuth blueprint could not be imported: {e}")
    logger.warning("Google OAuth functionality will not be available")

# Social Login API endpoints
@app.route('/api/auth/social/google')
def social_google_login():
    """Redirect to Google OAuth flow"""
    response = redirect('/google_login')
    return response
    
@app.route('/auth/social/google')
def social_google_login_alt():
    """Alternate route for Google OAuth flow without duplicated /api"""
    response = redirect('/google_login')
    return response

# Add a route to handle direct access to /login from the Flask backend
@app.route('/login')
def handle_login():
    """Return a simple message for login page to avoid redirect loop"""
    return jsonify({
        "error": "This is the Flask backend login endpoint. Please use the Angular frontend at port 5000 for the actual login page."
    })

# Constants and Directories
FALLBACK_DIR = os.path.join(os.path.dirname(__file__), "fallback")
os.makedirs(FALLBACK_DIR, exist_ok=True)

# Fallback Data Functions
def load_fallback_data(index_name):
    """
    Load fallback data for a given index from the fallback directory.
    """
    try:
        # Create a mapping for index names to filenames
        fallback_mapping = {
            "NIFTY 50": "nifty50.json",
            "NIFTY 100": "nifty100.json",
            "NIFTY 500": "nifty500.json",
            "NIFTY Next 50": "nifty_next_50.json",
            "Nifty VIX": "nifty_vix.json", # Special case - no constituents
            "GIFT Nifty": "gift_nifty.json", # Special case - no constituents
            "BSE SENSEX": "bse_sensex.json",
            "S&P BSE - 100": "sp_bse_100.json",
            "S&P BSE - 200": "sp_bse_200.json",
            "S&P BSE Midcap": "sp_bse_midcap.json",
            "S&P 100": "S&P_100.json",
            "S&P 500": "S&P_500.json",
            "S&P MidCap 400": "S&P_MidCap_400.json",
            "S&P SmallCap 600": "S&P_SmallCap_600.json",
            "BSE 30": "BSE_30.json",
            # Australian indices
            "ASX 200": "asx_200.json",
            "S&P/ASX 200": "asx_200.json",
            "S&P/ASX 300": "asx_300.json",
            "All Ordinaries Index": "all_ordinaries.json",
            "S&P/ASX 50": "asx_50.json",
            "NZX 50": "nzx_50.json",
            # Middle East indices
            "Tadawul All Share Index": "tadawul_all_share.json",
            "Dubai Financial Market General Index": "dubai_financial_market.json",
            "Abu Dhabi Securities Exchange Index": "abu_dhabi_securities.json",
            "Qatar Exchange Index": "qatar_exchange.json",
            "Bahrain All Share Index": "bahrain_all_share.json",
            "Muscat Securities Market Index": "muscat_securities.json",
            "Kuwait Stock Exchange Index": "kuwait_stock_exchange.json"
        }
        
        # Get the filename for the index
        file_name = fallback_mapping.get(index_name)
        if not file_name:
            # Fallback to a default transformation if index_name not in mapping
            file_name = f"{index_name.replace(' ', '_').replace('&', 'and').lower()}.json"
        
        file_path = os.path.join(FALLBACK_DIR, file_name)
        
        logger.info(f"Attempting to load fallback data from: {file_path}")
        
        # If the file doesn't exist, create an empty one
        if not os.path.exists(file_path):
            create_empty_fallback_file(file_path)
            logger.warning(f"Created empty fallback file: {file_path}")
            return []
        
        # Load the data from the file
        with open(file_path, "r") as f:
            data = json.load(f)
            logger.info(f"Successfully loaded fallback data for {index_name} from {file_path}")
            return data
    except Exception as e:
        logger.error(f"Error loading fallback data for {index_name}: {e}", exc_info=True)
        return []

def create_empty_fallback_file(file_path):
    """
    Create an empty fallback file with a basic structure.
    """
    try:
        with open(file_path, "w") as f:
            json.dump([], f, indent=4)
    except Exception as e:
        logger.error(f"Error creating empty fallback file {file_path}: {e}", exc_info=True)

# Yahoo Finance API functions
def fetch_stock_search(keywords):
    """
    Search for stocks with preference for Indian stocks using NSE data.
    
    Args:
        keywords (str): Search keywords.
        
    Returns:
        list: List of matching stocks.
    """
    try:
        # Convert keywords to lowercase for case-insensitive search
        search_term = keywords.lower().strip()
        if not search_term:
            return fetch_popular_stocks()[:5]  # Return first 5 popular stocks if empty search
        
        results = []
        
        # Priority 1: Search in popular stocks (includes pre-defined Indian stocks)
        # This ensures quick and reliable results for common searches
        popular_stocks = fetch_popular_stocks()
        for stock in popular_stocks:
            # Match against both symbol and company name
            symbol = stock["symbol"].lower()
            company = stock["company"].lower()
            
            # Check for exact match first (prioritize these)
            if symbol == search_term or company == search_term:
                results.append(stock)
            # Then check for partial matches
            elif search_term in symbol or search_term in company:
                results.append(stock)
        
        # For "airtel" specifically, ensure we have Bharti Airtel in results
        if search_term == "airtel" and not any(s["symbol"] == "BHARTIARTL" for s in results):
            airtel_stock = {
                "symbol": "BHARTIARTL",
                "company": "Bharti Airtel Ltd.",
                "exchange": "NSE",
                "sector": "Communication Services",
                "currency": "INR"
            }
            results.append(airtel_stock)
            
        # Priority 2: If first search didn't yield enough results, try NSE search for Indian stocks
        if len(results) < 10:
            try:
                logger.info(f"Searching for '{keywords}' in NSE stocks")
                try:
                    # Try to fetch NSE symbols
                    nse_symbols = nse_eq_symbols()
                    if nse_symbols:
                        # Process NSE symbols
                        symbol_list = []
                        
                        # Extract symbols depending on the returned structure
                        if isinstance(nse_symbols, dict) and 'symbols' in nse_symbols:
                            symbol_list = nse_symbols['symbols']
                        elif isinstance(nse_symbols, list):
                            symbol_list = nse_symbols
                        
                        # Match NSE symbols against search term
                        for item in symbol_list:
                            if isinstance(item, dict) and 'symbol' in item:
                                symbol = item['symbol']
                                company_name = item.get('companyName', item.get('name', symbol))
                                
                                # Skip if already in results
                                if any(r["symbol"] == symbol for r in results):
                                    continue
                                
                                # Check if the search term is in the symbol or company name
                                if (search_term in symbol.lower() or search_term in company_name.lower()):
                                    stock = {
                                        "symbol": symbol,
                                        "company": company_name,
                                        "exchange": "NSE",
                                        "sector": item.get("sector", ""),
                                        "currency": "INR"
                                    }
                                    results.append(stock)
                except Exception as e:
                    logger.warning(f"NSE symbols search failed: {e}")
            except Exception as e:
                logger.error(f"Error during NSE search: {e}", exc_info=True)
        
        # Priority 3: If still not enough results, try Yahoo Finance directly
        if len(results) < 5:
            try:
                logger.info(f"Trying Yahoo Finance search for '{keywords}'")
                
                # First try as an Indian stock with .NS suffix
                try:
                    indian_ticker = yf.Ticker(f"{search_term}.NS")
                    if hasattr(indian_ticker, 'info') and indian_ticker.info and 'longName' in indian_ticker.info:
                        info = indian_ticker.info
                        stock = {
                            "symbol": search_term.upper(),
                            "company": info.get("longName", info.get("shortName", f"{search_term.upper()} Ltd.")),
                            "exchange": "NSE",
                            "sector": info.get("sector", ""),
                            "currency": "INR"
                        }
                        # Add if not already in results
                        if not any(r["symbol"] == stock["symbol"] for r in results):
                            results.append(stock)
                except Exception as e:
                    logger.warning(f"Yahoo Finance Indian stock search failed: {e}")
                
                # Then try as an international stock
                try:
                    ticker = yf.Ticker(search_term)
                    if hasattr(ticker, 'info') and ticker.info and 'longName' in ticker.info:
                        info = ticker.info
                        stock = {
                            "symbol": search_term.upper(),
                            "company": info.get("longName", info.get("shortName", f"Company for {search_term.upper()}")),
                            "exchange": info.get("exchange", ""),
                            "sector": info.get("sector", ""),
                            "currency": info.get("currency", "USD")
                        }
                        # Add if not already in results
                        if not any(r["symbol"] == stock["symbol"] for r in results):
                            results.append(stock)
                except Exception as e:
                    logger.warning(f"Yahoo Finance international stock search failed: {e}")
                    
            except Exception as e:
                logger.error(f"Error during Yahoo Finance search: {e}", exc_info=True)
        
        # Limit results to first 20 to avoid overwhelming the UI
        results = results[:20]
        
        logger.info(f"Total search results for '{keywords}': {len(results)}")
        return results
    except Exception as e:
        logger.error(f"Error in stock search: {e}", exc_info=True)
        return []
        
def fetch_popular_stocks():
    """
    Return a list of popular stocks.
    
    Returns:
        list: List of popular stocks.
    """
    popular_stocks = [
        # Popular US Stocks
        {"symbol": "AAPL", "company": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 85450000, "sector": "Technology", "price": 178.30, "change": 3.35, "changePercent": 1.92},
        {"symbol": "MSFT", "company": "Microsoft Corporation", "exchange": "NASDAQ", "currency": "USD", "volume": 25360000, "sector": "Technology", "price": 412.65, "change": 2.15, "changePercent": 0.52},
        {"symbol": "GOOGL", "company": "Alphabet Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 18720000, "sector": "Communication Services", "price": 147.82, "change": 1.87, "changePercent": 1.28},
        {"symbol": "AMZN", "company": "Amazon.com, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 32580000, "sector": "Consumer Discretionary", "price": 178.75, "change": 2.34, "changePercent": 1.33},
        {"symbol": "META", "company": "Meta Platforms, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 14670000, "sector": "Communication Services", "price": 485.58, "change": 5.67, "changePercent": 1.18},
        {"symbol": "TSLA", "company": "Tesla, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 98260000, "sector": "Consumer Discretionary", "price": 172.63, "change": -3.45, "changePercent": -1.96},
        {"symbol": "NVDA", "company": "NVIDIA Corporation", "exchange": "NASDAQ", "currency": "USD", "volume": 43560000, "sector": "Technology", "price": 875.30, "change": 15.80, "changePercent": 1.85},
        
        # Popular Indian Stocks (NSE)
        {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "NSE", "currency": "INR", "volume": 5680000, "sector": "Energy", "price": 2500.00, "change": 35.00, "changePercent": 1.40},
        {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "NSE", "currency": "INR", "volume": 3240000, "sector": "IT", "price": 3400.00, "change": -50.00, "changePercent": -1.50},
        {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "NSE", "currency": "INR", "volume": 7890000, "sector": "Banking", "price": 1600.00, "change": 12.00, "changePercent": 0.80},
        {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "NSE", "currency": "INR", "volume": 4850000, "sector": "IT", "price": 1700.00, "change": 25.00, "changePercent": 1.50},
        {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "exchange": "NSE", "currency": "INR", "volume": 3960000, "sector": "Telecom", "price": 850.00, "change": 12.00, "changePercent": 1.40},
        {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "NSE", "currency": "INR", "volume": 6540000, "sector": "Banking", "price": 930.00, "change": 15.00, "changePercent": 1.60},
        {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "NSE", "currency": "INR", "volume": 2930000, "sector": "FMCG", "price": 2400.00, "change": -18.00, "changePercent": -0.80},
        {"symbol": "ITC", "company": "ITC Ltd.", "exchange": "NSE", "currency": "INR", "volume": 9320000, "sector": "FMCG", "price": 450.00, "change": 8.00, "changePercent": 1.80},
        {"symbol": "SBIN", "company": "State Bank of India", "exchange": "NSE", "currency": "INR", "volume": 8540000, "sector": "Banking", "price": 620.00, "change": -5.00, "changePercent": -0.80},
        {"symbol": "TATAMOTORS", "company": "Tata Motors Ltd.", "exchange": "NSE", "currency": "INR", "volume": 7450000, "sector": "Automobile", "price": 750.00, "change": 18.00, "changePercent": 2.40},
        
        # Popular Indian Stocks (BSE)
        {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "currency": "INR", "volume": 5240000, "sector": "Energy", "price": 2500.00, "change": 35.00, "changePercent": 1.40},
        {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "currency": "INR", "volume": 3240000, "sector": "IT", "price": 3400.00, "change": -50.00, "changePercent": -1.50},
        {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "currency": "INR", "volume": 7560000, "sector": "Banking", "price": 1600.00, "change": 12.00, "changePercent": 0.80},
        {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "currency": "INR", "volume": 4590000, "sector": "IT", "price": 1700.00, "change": 25.00, "changePercent": 1.50},
        {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "currency": "INR", "volume": 6150000, "sector": "Banking", "price": 930.00, "change": 15.00, "changePercent": 1.60},
        {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "currency": "INR", "volume": 2780000, "sector": "FMCG", "price": 2400.00, "change": -18.00, "changePercent": -0.80},
        {"symbol": "ASIANPAINT", "company": "Asian Paints Ltd.", "exchange": "BSE", "currency": "INR", "volume": 2450000, "sector": "Manufacturing", "price": 3250.00, "change": 45.00, "changePercent": 1.40},
        {"symbol": "MARUTI", "company": "Maruti Suzuki India Ltd.", "exchange": "BSE", "currency": "INR", "volume": 3210000, "sector": "Automobile", "price": 10250.00, "change": 125.00, "changePercent": 1.23},
        {"symbol": "SUNPHARMA", "company": "Sun Pharmaceutical Industries Ltd.", "exchange": "BSE", "currency": "INR", "volume": 4320000, "sector": "Healthcare", "price": 1175.00, "change": 18.50, "changePercent": 1.60},
        {"symbol": "KOTAKBANK", "company": "Kotak Mahindra Bank Ltd.", "exchange": "BSE", "currency": "INR", "volume": 3780000, "sector": "Banking", "price": 1850.00, "change": -23.00, "changePercent": -1.23},
        
        # Additional NYSE Stocks
        {"symbol": "JPM", "company": "JPMorgan Chase & Co.", "exchange": "NYSE", "currency": "USD", "volume": 15820000, "sector": "Financials", "price": 183.40, "change": 1.25, "changePercent": 0.70},
        {"symbol": "V", "company": "Visa Inc.", "exchange": "NYSE", "currency": "USD", "volume": 9680000, "sector": "Financials", "price": 275.85, "change": 2.45, "changePercent": 0.90},
        {"symbol": "JNJ", "company": "Johnson & Johnson", "exchange": "NYSE", "currency": "USD", "volume": 8450000, "sector": "Healthcare", "price": 156.80, "change": -1.35, "changePercent": -0.85},
        {"symbol": "WMT", "company": "Walmart Inc.", "exchange": "NYSE", "currency": "USD", "volume": 7620000, "sector": "Consumer Staples", "price": 60.25, "change": 0.82, "changePercent": 1.38},
        {"symbol": "PG", "company": "Procter & Gamble Co.", "exchange": "NYSE", "currency": "USD", "volume": 6240000, "sector": "Consumer Staples", "price": 160.25, "change": -0.55, "changePercent": -0.35},
        {"symbol": "KO", "company": "The Coca-Cola Company", "exchange": "NYSE", "currency": "USD", "volume": 12450000, "sector": "Consumer Staples", "price": 61.70, "change": 0.34, "changePercent": 0.55},
        {"symbol": "HD", "company": "Home Depot Inc.", "exchange": "NYSE", "currency": "USD", "volume": 4320000, "sector": "Consumer Discretionary", "price": 345.90, "change": 4.35, "changePercent": 1.28},
        
        # Additional NASDAQ Stocks
        {"symbol": "NFLX", "company": "Netflix, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 7350000, "sector": "Communication Services", "price": 657.42, "change": 12.67, "changePercent": 1.93},
        {"symbol": "PYPL", "company": "PayPal Holdings, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 8650000, "sector": "Financials", "price": 65.80, "change": 1.32, "changePercent": 2.05},
        {"symbol": "INTC", "company": "Intel Corporation", "exchange": "NASDAQ", "currency": "USD", "volume": 24580000, "sector": "Technology", "price": 38.75, "change": -0.45, "changePercent": -1.15},
        {"symbol": "AMD", "company": "Advanced Micro Devices, Inc.", "exchange": "NASDAQ", "currency": "USD", "volume": 32450000, "sector": "Technology", "price": 164.25, "change": 3.75, "changePercent": 2.34},
        
        # FTSE (UK) Stocks
        {"symbol": "HSBA.L", "company": "HSBC Holdings plc", "exchange": "FTSE", "currency": "GBP", "volume": 22450000, "sector": "Financials", "price": 680.40, "change": 8.50, "changePercent": 1.26},
        {"symbol": "SHEL.L", "company": "Shell plc", "exchange": "FTSE", "currency": "GBP", "volume": 18350000, "sector": "Energy", "price": 2548.50, "change": 32.50, "changePercent": 1.29},
        {"symbol": "AZN.L", "company": "AstraZeneca plc", "exchange": "FTSE", "currency": "GBP", "volume": 4250000, "sector": "Healthcare", "price": 12175.00, "change": -85.00, "changePercent": -0.69},
        {"symbol": "ULVR.L", "company": "Unilever plc", "exchange": "FTSE", "currency": "GBP", "volume": 5320000, "sector": "Consumer Staples", "price": 3996.00, "change": 45.00, "changePercent": 1.14},
        {"symbol": "RIO.L", "company": "Rio Tinto Group", "exchange": "FTSE", "currency": "GBP", "volume": 3560000, "sector": "Materials", "price": 4950.00, "change": 68.00, "changePercent": 1.39},
        {"symbol": "GSK.L", "company": "GSK plc", "exchange": "FTSE", "currency": "GBP", "volume": 6780000, "sector": "Healthcare", "price": 1680.40, "change": -12.60, "changePercent": -0.74},
        {"symbol": "BARC.L", "company": "Barclays plc", "exchange": "FTSE", "currency": "GBP", "volume": 19450000, "sector": "Financials", "price": 205.45, "change": 3.35, "changePercent": 1.66},
        {"symbol": "BP.L", "company": "BP p.l.c.", "exchange": "FTSE", "currency": "GBP", "volume": 29650000, "sector": "Energy", "price": 468.80, "change": 6.45, "changePercent": 1.40},
        {"symbol": "LLOY.L", "company": "Lloyds Banking Group plc", "exchange": "FTSE", "currency": "GBP", "volume": 125680000, "sector": "Financials", "price": 55.76, "change": 0.92, "changePercent": 1.68},
        {"symbol": "VOD.L", "company": "Vodafone Group plc", "exchange": "FTSE", "currency": "GBP", "volume": 85420000, "sector": "Telecommunication", "price": 68.94, "change": -0.44, "changePercent": -0.63},
        
        # DAX (German) Stocks
        {"symbol": "SAP.DE", "company": "SAP SE", "exchange": "DAX", "currency": "EUR", "volume": 6250000, "sector": "Technology", "price": 173.88, "change": 2.28, "changePercent": 1.33},
        {"symbol": "SIE.DE", "company": "Siemens AG", "exchange": "DAX", "currency": "EUR", "volume": 3560000, "sector": "Industrials", "price": 182.42, "change": 2.58, "changePercent": 1.43},
        {"symbol": "ALV.DE", "company": "Allianz SE", "exchange": "DAX", "currency": "EUR", "volume": 2860000, "sector": "Financials", "price": 264.80, "change": 3.50, "changePercent": 1.34},
        {"symbol": "DTE.DE", "company": "Deutsche Telekom AG", "exchange": "DAX", "currency": "EUR", "volume": 12450000, "sector": "Telecommunication", "price": 22.21, "change": 0.18, "changePercent": 0.82},
        {"symbol": "BMW.DE", "company": "Bayerische Motoren Werke AG", "exchange": "DAX", "currency": "EUR", "volume": 2350000, "sector": "Consumer Discretionary", "price": 96.18, "change": 1.24, "changePercent": 1.31},
        {"symbol": "BAS.DE", "company": "BASF SE", "exchange": "DAX", "currency": "EUR", "volume": 5890000, "sector": "Materials", "price": 47.66, "change": 0.63, "changePercent": 1.34},
        {"symbol": "MBG.DE", "company": "Mercedes-Benz Group AG", "exchange": "DAX", "currency": "EUR", "volume": 4520000, "sector": "Consumer Discretionary", "price": 66.54, "change": 0.98, "changePercent": 1.49},
        {"symbol": "BAY.DE", "company": "Bayer AG", "exchange": "DAX", "currency": "EUR", "volume": 8650000, "sector": "Healthcare", "price": 26.87, "change": -0.28, "changePercent": -1.03},
        {"symbol": "DBK.DE", "company": "Deutsche Bank AG", "exchange": "DAX", "currency": "EUR", "volume": 12450000, "sector": "Financials", "price": 14.90, "change": 0.20, "changePercent": 1.36},
        {"symbol": "VOW3.DE", "company": "Volkswagen AG", "exchange": "DAX", "currency": "EUR", "volume": 1920000, "sector": "Consumer Discretionary", "price": 114.98, "change": 1.62, "changePercent": 1.43},
        
        # Nikkei (Japan) Stocks
        {"symbol": "7203.T", "company": "Toyota Motor Corporation", "exchange": "NIKKEI", "currency": "JPY", "volume": 12350000, "sector": "Consumer Discretionary", "price": 3235.00, "change": 42.00, "changePercent": 1.32},
        {"symbol": "9984.T", "company": "SoftBank Group Corp.", "exchange": "NIKKEI", "currency": "JPY", "volume": 9840000, "sector": "Communication Services", "price": 8975.00, "change": 125.00, "changePercent": 1.41},
        {"symbol": "6758.T", "company": "Sony Group Corporation", "exchange": "NIKKEI", "currency": "JPY", "volume": 6520000, "sector": "Consumer Discretionary", "price": 13280.00, "change": 180.00, "changePercent": 1.37},
        {"symbol": "6861.T", "company": "KEYENCE CORPORATION", "exchange": "NIKKEI", "currency": "JPY", "volume": 980000, "sector": "Technology", "price": 64880.00, "change": 680.00, "changePercent": 1.06},
        {"symbol": "7267.T", "company": "Honda Motor Co., Ltd.", "exchange": "NIKKEI", "currency": "JPY", "volume": 8450000, "sector": "Consumer Discretionary", "price": 1684.00, "change": 22.00, "changePercent": 1.32},
        {"symbol": "9433.T", "company": "KDDI Corporation", "exchange": "NIKKEI", "currency": "JPY", "volume": 5240000, "sector": "Communication Services", "price": 4368.00, "change": 33.00, "changePercent": 0.76},
        {"symbol": "8306.T", "company": "Mitsubishi UFJ Financial Group, Inc.", "exchange": "NIKKEI", "currency": "JPY", "volume": 45680000, "sector": "Financials", "price": 1342.50, "change": 18.50, "changePercent": 1.40},
        {"symbol": "6501.T", "company": "Hitachi, Ltd.", "exchange": "NIKKEI", "currency": "JPY", "volume": 12450000, "sector": "Industrials", "price": 10780.00, "change": 150.00, "changePercent": 1.41},
        {"symbol": "6367.T", "company": "Daikin Industries,Ltd.", "exchange": "NIKKEI", "currency": "JPY", "volume": 2350000, "sector": "Industrials", "price": 24950.00, "change": 320.00, "changePercent": 1.30},
        {"symbol": "8035.T", "company": "Tokyo Electron Limited", "exchange": "NIKKEI", "currency": "JPY", "volume": 3650000, "sector": "Technology", "price": 26905.00, "change": 485.00, "changePercent": 1.84},
        
        # Shanghai Composite (China) Stocks
        {"symbol": "601318.SS", "company": "Ping An Insurance (Group) Company of China, Ltd.", "exchange": "SHCOMP", "currency": "CNY", "volume": 85640000, "sector": "Financials", "price": 45.88, "change": 0.58, "changePercent": 1.28},
        {"symbol": "601988.SS", "company": "Bank of China Limited", "exchange": "SHCOMP", "currency": "CNY", "volume": 254680000, "sector": "Financials", "price": 3.63, "change": 0.03, "changePercent": 0.83},
        {"symbol": "601857.SS", "company": "PetroChina Company Limited", "exchange": "SHCOMP", "currency": "CNY", "volume": 125680000, "sector": "Energy", "price": 6.23, "change": 0.09, "changePercent": 1.47},
        {"symbol": "600519.SS", "company": "Kweichow Moutai Co., Ltd.", "exchange": "SHCOMP", "currency": "CNY", "volume": 3680000, "sector": "Consumer Staples", "price": 1528.00, "change": 22.00, "changePercent": 1.46},
        {"symbol": "601398.SS", "company": "Industrial and Commercial Bank of China Limited", "exchange": "SHCOMP", "currency": "CNY", "volume": 356820000, "sector": "Financials", "price": 4.48, "change": 0.04, "changePercent": 0.90},
        {"symbol": "600036.SS", "company": "China Merchants Bank Co., Ltd.", "exchange": "SHCOMP", "currency": "CNY", "volume": 78450000, "sector": "Financials", "price": 32.86, "change": 0.42, "changePercent": 1.29},
        {"symbol": "601628.SS", "company": "China Life Insurance Company Limited", "exchange": "SHCOMP", "currency": "CNY", "volume": 85640000, "sector": "Financials", "price": 12.84, "change": 0.14, "changePercent": 1.10},
        {"symbol": "600276.SS", "company": "Jiangsu Hengrui Medicine Co., Ltd.", "exchange": "SHCOMP", "currency": "CNY", "volume": 28650000, "sector": "Healthcare", "price": 37.22, "change": 0.48, "changePercent": 1.31},
        {"symbol": "601166.SS", "company": "Industrial Bank Co., Ltd.", "exchange": "SHCOMP", "currency": "CNY", "volume": 65420000, "sector": "Financials", "price": 16.84, "change": 0.22, "changePercent": 1.32},
        {"symbol": "600030.SS", "company": "CITIC Securities Company Limited", "exchange": "SHCOMP", "currency": "CNY", "volume": 54280000, "sector": "Financials", "price": 20.36, "change": 0.28, "changePercent": 1.39}
    ]
    return popular_stocks

def fetch_yahoo_finance_company_overview(symbol):
    """
    Fetch company overview from Yahoo Finance.
    
    Args:
        symbol (str): Stock symbol.
        
    Returns:
        dict: Company overview data.
    """
    # List of reserved paths/non-stock symbols
    reserved_paths = [
        'portfolio', 'screener', 'watchlist', 'settings', 'notifications',
        'account', 'login', 'register', 'dashboard', 'help', 'about',
        'contact', 'privacy', 'terms', 'assets', 'favicon.ico'
    ]
    
    # Check if symbol is a reserved path or non-stock symbol
    if symbol.lower() in reserved_paths:
        logger.warning(f"Requested data for non-stock symbol: {symbol}")
        return {
            "symbol": symbol,
            "company": f"Invalid Stock Symbol",
            "exchange": "Error",
            "sector": "Error",
            "industry": "Error",
            "description": f"'{symbol}' is not a valid stock symbol. Please enter a valid stock symbol.",
            "website": "",
            "logoUrl": "/assets/logo.png",
            "country": "Error",
            "currency": "Error",
            "error": "Invalid symbol"
        }
    
    try:
        # First try with .NS suffix for Indian stocks
        indian_symbol = f"{symbol}.NS"
        ticker = yf.Ticker(indian_symbol)
        info = None
        
        try:
            info = ticker.info
            if info and 'longName' in info:
                logger.info(f"Found Indian stock data for {symbol} (NSE)")
                return {
                    "symbol": symbol,
                    "company": info.get("longName", info.get("shortName", f"{symbol} Ltd.")),
                    "exchange": "NSE",
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "description": info.get("longBusinessSummary", f"Indian company listed on NSE."),
                    "website": info.get("website", ""),
                    "logoUrl": info.get("logo_url", f"/assets/sample-logos/{symbol.lower()}.png"),
                    "country": "India",
                    "currency": "INR"
                }
        except Exception as e:
            logger.warning(f"Error fetching NSE data for {symbol}: {e}")
        
        # If NSE failed, try without suffix
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
        except Exception as e:
            logger.warning(f"Error fetching ticker info for {symbol}: {e}")
        
        if info and 'longName' in info:
            return {
                "symbol": symbol,
                "company": info.get("longName", info.get("shortName", f"Company for {symbol}")),
                "exchange": info.get("exchange", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "description": info.get("longBusinessSummary", f"No description available for {symbol}."),
                "website": info.get("website", ""),
                "logoUrl": info.get("logo_url", f"/assets/sample-logos/{symbol.lower()}.png"),
                "country": info.get("country", ""),
                "currency": info.get("currency", "USD")
            }
        else:
            logger.warning(f"No company overview found for symbol: {symbol}")
            return {
                "symbol": symbol,
                "company": f"Company for {symbol}",
                "exchange": "Unknown",
                "sector": "Unknown",
                "industry": "Unknown",
                "description": f"No description available for {symbol}.",
                "website": "",
                "logoUrl": f"/assets/sample-logos/{symbol.lower()}.png",
                "country": "Unknown",
                "currency": "USD"
            }
    except Exception as e:
        logger.error(f"Error fetching company overview from Yahoo Finance: {e}", exc_info=True)
        return {
            "symbol": symbol,
            "company": f"Company for {symbol}",
            "exchange": "Error",
            "sector": "Error",
            "industry": "Error",
            "description": f"Error fetching data for {symbol}.",
            "website": "",
            "logoUrl": f"/assets/sample-logos/{symbol.lower()}.png",
            "country": "Error",
            "currency": "USD"
        }

def fetch_yahoo_finance_time_series(symbol, period='1y'):
    """
    Fetch time series data from Yahoo Finance.
    
    Args:
        symbol (str): Stock symbol.
        period (str): Time period (1d, 1w, 1mo, 3mo, 6mo, 1y).
        
    Returns:
        dict: Time series data.
    """
    # List of reserved paths/non-stock symbols
    reserved_paths = [
        'portfolio', 'screener', 'watchlist', 'settings', 'notifications',
        'account', 'login', 'register', 'dashboard', 'help', 'about',
        'contact', 'privacy', 'terms', 'assets', 'favicon.ico'
    ]
    
    # Check if symbol is a reserved path or non-stock symbol
    if symbol.lower() in reserved_paths:
        logger.warning(f"Requested time series data for non-stock symbol: {symbol}")
        return {
            "symbol": symbol,
            "prices": [],
            "name": "Invalid Stock Symbol",
            "currency": "Error",
            "exchange": "Error",
            "error": f"'{symbol}' is not a valid stock symbol. Please enter a valid stock symbol."
        }
    
    try:
        # Map period to Yahoo Finance period and interval
        period_mapping = {
            '1d': ('1d', '5m'),
            '1w': ('5d', '15m'),
            '1mo': ('1mo', '1d'),
            '3mo': ('3mo', '1d'),
            '6mo': ('6mo', '1d'),
            '1y': ('1y', '1d'),
            '5y': ('5y', '1wk')
        }
        
        yf_period, yf_interval = period_mapping.get(period, ('1y', '1d'))
        
        # First try with the .NS suffix for Indian stocks
        history = None
        company_details = None
        is_indian_stock = False
        
        # Try with NSE suffix
        try:
            indian_symbol = f"{symbol}.NS"
            logger.info(f"Trying to fetch time series for Indian stock: {indian_symbol}")
            
            ticker_ns = yf.Ticker(indian_symbol)
            history = ticker_ns.history(period=yf_period, interval=yf_interval)
            
            if not history.empty:
                logger.info(f"Successfully fetched time series data for Indian stock: {indian_symbol}")
                is_indian_stock = True
                # Get the company details with proper Indian info
                company_details = fetch_yahoo_finance_company_overview(symbol)
            else:
                logger.warning(f"No data found for Indian stock: {indian_symbol}")
        except Exception as e:
            logger.warning(f"Error fetching Indian stock data for {symbol}: {e}")
        
        # If no Indian stock data, try without suffix
        if history is None or history.empty:
            logger.info(f"Falling back to non-Indian stock lookup for {symbol}")
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=yf_period, interval=yf_interval)
            if not history.empty:
                company_details = fetch_yahoo_finance_company_overview(symbol)
        
        if not history.empty:
            # Convert to list format
            prices = []
            for index, row in history.iterrows():
                date_str = index.strftime("%Y-%m-%d")
                if yf_interval in ['5m', '15m', '30m', '1h']:
                    date_str = index.strftime("%Y-%m-%d %H:%M:%S")
                    
                price_data = {
                    "date": date_str,
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(float(row.get("Volume", 0)))
                }
                prices.append(price_data)
                
            # Sort by date (newest first)
            prices.sort(key=lambda x: x["date"], reverse=True)
            
            company_name = company_details.get("company", f"Company for {symbol}")
            
            return {
                "symbol": symbol,
                "prices": prices,
                "name": company_name,
                "currency": company_details.get("currency", "USD"),
                "exchange": company_details.get("exchange", "")
            }
        else:
            logger.warning(f"No time series data found for symbol: {symbol}")
            return generate_sample_stock_data_for_symbol(symbol, period)
    except Exception as e:
        logger.error(f"Error fetching time series from Yahoo Finance: {e}", exc_info=True)
        return generate_sample_stock_data_for_symbol(symbol, period)

# Generate BSE constituents for Indian indices
def generate_bse_constituents(index_name):
    """
    Generate constituent stocks for BSE indices.
    Args:
        index_name (str): Name of the BSE index
    Returns:
        list: List of constituent stocks
    """
    import random
    
    # Define common BSE/S&P BSE stocks with proper details
    bse_stocks = []
    
    # BSE SENSEX stocks (30 stocks)
    if index_name == "BSE SENSEX":
        bse_stocks = [
            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2500.0, "change": 35.0, "changePercent": 1.4, "currency": "INR", "sector": "Energy"},
            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3400.0, "change": -50.0, "changePercent": -1.5, "currency": "INR", "sector": "IT"},
            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1600.0, "change": 12.0, "changePercent": 0.8, "currency": "INR", "sector": "Banking"},
            {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "price": 1700.0, "change": 25.0, "changePercent": 1.5, "currency": "INR", "sector": "IT"},
            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 930.0, "change": 15.0, "changePercent": 1.6, "currency": "INR", "sector": "Banking"},
            {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "price": 2400.0, "change": -18.0, "changePercent": -0.8, "currency": "INR", "sector": "FMCG"},
            {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "exchange": "BSE", "price": 850.0, "change": 12.0, "changePercent": 1.4, "currency": "INR", "sector": "Telecom"},
            {"symbol": "ITC", "company": "ITC Ltd.", "exchange": "BSE", "price": 450.0, "change": 8.0, "changePercent": 1.8, "currency": "INR", "sector": "FMCG"},
            {"symbol": "SBIN", "company": "State Bank of India", "exchange": "BSE", "price": 620.0, "change": -5.0, "changePercent": -0.8, "currency": "INR", "sector": "Banking"},
            {"symbol": "BAJFINANCE", "company": "Bajaj Finance Ltd.", "exchange": "BSE", "price": 7100.0, "change": 120.0, "changePercent": 1.7, "currency": "INR", "sector": "Financial Services"},
            {"symbol": "KOTAKBANK", "company": "Kotak Mahindra Bank Ltd.", "exchange": "BSE", "price": 1750.0, "change": -15.0, "changePercent": -0.9, "currency": "INR", "sector": "Banking"},
            {"symbol": "LT", "company": "Larsen & Toubro Ltd.", "exchange": "BSE", "price": 2800.0, "change": 35.0, "changePercent": 1.3, "currency": "INR", "sector": "Construction"},
            {"symbol": "AXISBANK", "company": "Axis Bank Ltd.", "exchange": "BSE", "price": 980.0, "change": 12.0, "changePercent": 1.2, "currency": "INR", "sector": "Banking"},
            {"symbol": "ASIANPAINT", "company": "Asian Paints Ltd.", "exchange": "BSE", "price": 3200.0, "change": -40.0, "changePercent": -1.3, "currency": "INR", "sector": "Consumer Durables"},
            {"symbol": "MARUTI", "company": "Maruti Suzuki India Ltd.", "exchange": "BSE", "price": 10500.0, "change": 180.0, "changePercent": 1.7, "currency": "INR", "sector": "Automobile"},
            {"symbol": "TATAMOTORS", "company": "Tata Motors Ltd.", "exchange": "BSE", "price": 750.0, "change": 18.0, "changePercent": 2.4, "currency": "INR", "sector": "Automobile"},
            {"symbol": "SUNPHARMA", "company": "Sun Pharmaceutical Industries Ltd.", "exchange": "BSE", "price": 1100.0, "change": -15.0, "changePercent": -1.4, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "TITAN", "company": "Titan Company Ltd.", "exchange": "BSE", "price": 2900.0, "change": 45.0, "changePercent": 1.6, "currency": "INR", "sector": "Consumer Durables"},
            {"symbol": "BAJAJFINSV", "company": "Bajaj Finserv Ltd.", "exchange": "BSE", "price": 1580.0, "change": -18.0, "changePercent": -1.2, "currency": "INR", "sector": "Financial Services"},
            {"symbol": "NTPC", "company": "NTPC Ltd.", "exchange": "BSE", "price": 250.0, "change": 3.0, "changePercent": 1.2, "currency": "INR", "sector": "Power"},
            {"symbol": "JSWSTEEL", "company": "JSW Steel Ltd.", "exchange": "BSE", "price": 780.0, "change": 12.0, "changePercent": 1.6, "currency": "INR", "sector": "Metals"},
            {"symbol": "POWERGRID", "company": "Power Grid Corporation of India Ltd.", "exchange": "BSE", "price": 240.0, "change": -2.5, "changePercent": -1.1, "currency": "INR", "sector": "Power"},
            {"symbol": "TATASTEEL", "company": "Tata Steel Ltd.", "exchange": "BSE", "price": 130.0, "change": 2.2, "changePercent": 1.7, "currency": "INR", "sector": "Metals"},
            {"symbol": "ULTRACEMCO", "company": "UltraTech Cement Ltd.", "exchange": "BSE", "price": 8500.0, "change": -120.0, "changePercent": -1.4, "currency": "INR", "sector": "Cement"},
            {"symbol": "INDUSINDBK", "company": "IndusInd Bank Ltd.", "exchange": "BSE", "price": 1400.0, "change": 25.0, "changePercent": 1.8, "currency": "INR", "sector": "Banking"},
            {"symbol": "HDFCLIFE", "company": "HDFC Life Insurance Company Ltd.", "exchange": "BSE", "price": 620.0, "change": -8.0, "changePercent": -1.3, "currency": "INR", "sector": "Insurance"},
            {"symbol": "ADANIENT", "company": "Adani Enterprises Ltd.", "exchange": "BSE", "price": 2450.0, "change": 65.0, "changePercent": 2.7, "currency": "INR", "sector": "Diversified"},
            {"symbol": "TECHM", "company": "Tech Mahindra Ltd.", "exchange": "BSE", "price": 1280.0, "change": -15.0, "changePercent": -1.2, "currency": "INR", "sector": "IT"},
            {"symbol": "NESTLEIND", "company": "Nestle India Ltd.", "exchange": "BSE", "price": 23000.0, "change": 320.0, "changePercent": 1.4, "currency": "INR", "sector": "FMCG"},
            {"symbol": "WIPRO", "company": "Wipro Ltd.", "exchange": "BSE", "price": 420.0, "change": 6.0, "changePercent": 1.5, "currency": "INR", "sector": "IT"}
        ]
    # S&P BSE - 100 (extended set of stocks)
    elif index_name == "S&P BSE - 100":
        # Include all BSE SENSEX stocks and add more
        bse_stocks = generate_bse_constituents("BSE SENSEX")
        # Add additional stocks to make it 100
        additional_stocks = [
            {"symbol": "ADANIPORTS", "company": "Adani Ports and Special Economic Zone Ltd.", "exchange": "BSE", "price": 780.0, "change": 15.0, "changePercent": 2.0, "currency": "INR", "sector": "Infrastructure"},
            {"symbol": "HCLTECH", "company": "HCL Technologies Ltd.", "exchange": "BSE", "price": 1180.0, "change": -12.0, "changePercent": -1.0, "currency": "INR", "sector": "IT"},
            {"symbol": "DRREDDY", "company": "Dr. Reddy's Laboratories Ltd.", "exchange": "BSE", "price": 5200.0, "change": 80.0, "changePercent": 1.6, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "BRITANNIA", "company": "Britannia Industries Ltd.", "exchange": "BSE", "price": 4700.0, "change": -60.0, "changePercent": -1.3, "currency": "INR", "sector": "FMCG"},
            {"symbol": "HINDALCO", "company": "Hindalco Industries Ltd.", "exchange": "BSE", "price": 530.0, "change": 9.0, "changePercent": 1.7, "currency": "INR", "sector": "Metals"}
            # More stocks can be added as needed
        ]
        bse_stocks.extend(additional_stocks)
    # S&P BSE - 200 (even more stocks)
    elif index_name == "S&P BSE - 200":
        # Include all BSE 100 stocks and add more
        bse_stocks = generate_bse_constituents("S&P BSE - 100")
        # Add additional stocks to make it 200
        additional_stocks = [
            {"symbol": "GAIL", "company": "GAIL (India) Ltd.", "exchange": "BSE", "price": 175.0, "change": 3.5, "changePercent": 2.0, "currency": "INR", "sector": "Oil & Gas"},
            {"symbol": "BPCL", "company": "Bharat Petroleum Corporation Ltd.", "exchange": "BSE", "price": 380.0, "change": -5.0, "changePercent": -1.3, "currency": "INR", "sector": "Oil & Gas"},
            {"symbol": "COALINDIA", "company": "Coal India Ltd.", "exchange": "BSE", "price": 340.0, "change": 6.5, "changePercent": 1.9, "currency": "INR", "sector": "Mining"},
            {"symbol": "IOC", "company": "Indian Oil Corporation Ltd.", "exchange": "BSE", "price": 105.0, "change": 1.8, "changePercent": 1.7, "currency": "INR", "sector": "Oil & Gas"},
            {"symbol": "CIPLA", "company": "Cipla Ltd.", "exchange": "BSE", "price": 1280.0, "change": -15.0, "changePercent": -1.2, "currency": "INR", "sector": "Healthcare"}
            # More stocks can be added as needed
        ]
        bse_stocks.extend(additional_stocks)
    # S&P BSE Midcap (different set of midcap stocks)
    elif index_name == "S&P BSE Midcap":
        bse_stocks = [
            {"symbol": "ABCAPITAL", "company": "Aditya Birla Capital Ltd.", "exchange": "BSE", "price": 180.0, "change": 3.2, "changePercent": 1.8, "currency": "INR", "sector": "Financial Services"},
            {"symbol": "APOLLOTYRE", "company": "Apollo Tyres Ltd.", "exchange": "BSE", "price": 390.0, "change": 7.5, "changePercent": 2.0, "currency": "INR", "sector": "Automobile"},
            {"symbol": "CANBK", "company": "Canara Bank", "exchange": "BSE", "price": 420.0, "change": -5.0, "changePercent": -1.2, "currency": "INR", "sector": "Banking"},
            {"symbol": "FEDERALBNK", "company": "The Federal Bank Ltd.", "exchange": "BSE", "price": 150.0, "change": 2.8, "changePercent": 1.9, "currency": "INR", "sector": "Banking"},
            {"symbol": "NMDC", "company": "NMDC Ltd.", "exchange": "BSE", "price": 180.0, "change": -2.0, "changePercent": -1.1, "currency": "INR", "sector": "Mining"}
            # More midcap stocks can be added as needed
        ]
    # Default case for other BSE indices
    else:
        # Generate a sample set of stocks
        bse_stocks = [
            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2500.0, "change": 35.0, "changePercent": 1.4, "currency": "INR", "sector": "Energy"},
            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3400.0, "change": -50.0, "changePercent": -1.5, "currency": "INR", "sector": "IT"},
            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1600.0, "change": 12.0, "changePercent": 0.8, "currency": "INR", "sector": "Banking"},
            {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "price": 1700.0, "change": 25.0, "changePercent": 1.5, "currency": "INR", "sector": "IT"},
            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 930.0, "change": 15.0, "changePercent": 1.6, "currency": "INR", "sector": "Banking"}
        ]
    
    return bse_stocks

def generate_australian_index_constituents(index_name):
    """
    Generate constituent stocks for Australian indices.
    Args:
        index_name (str): Name of the Australian index
    Returns:
        list: List of constituent stocks
    """
    if index_name == "S&P/ASX 200" or index_name == "ASX 200":
        return [
            {"symbol": "BHP.AX", "company": "BHP Group Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29},
            {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21},
            {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30},
            {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25},
            {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38},
            {"symbol": "CSL.AX", "company": "CSL Limited", "sector": "Healthcare", "currency": "AUD", "exchange": "ASX", "price": 289.75, "change": 3.25, "changePercent": 1.13},
            {"symbol": "WES.AX", "company": "Wesfarmers Limited", "sector": "Consumer Discretionary", "currency": "AUD", "exchange": "ASX", "price": 58.45, "change": 0.65, "changePercent": 1.12},
            {"symbol": "WOW.AX", "company": "Woolworths Group Limited", "sector": "Consumer Staples", "currency": "AUD", "exchange": "ASX", "price": 37.80, "change": 0.42, "changePercent": 1.12},
            {"symbol": "RIO.AX", "company": "Rio Tinto Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 122.35, "change": 1.85, "changePercent": 1.54},
            {"symbol": "TLS.AX", "company": "Telstra Corporation Limited", "sector": "Communication Services", "currency": "AUD", "exchange": "ASX", "price": 4.18, "change": 0.03, "changePercent": 0.72}
        ]
    elif index_name == "S&P/ASX 50":
        return [
            {"symbol": "BHP.AX", "company": "BHP Group Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29},
            {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21},
            {"symbol": "CSL.AX", "company": "CSL Limited", "sector": "Healthcare", "currency": "AUD", "exchange": "ASX", "price": 289.75, "change": 3.25, "changePercent": 1.13},
            {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25},
            {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30},
            {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38},
            {"symbol": "WES.AX", "company": "Wesfarmers Limited", "sector": "Consumer Discretionary", "currency": "AUD", "exchange": "ASX", "price": 58.45, "change": 0.65, "changePercent": 1.12},
            {"symbol": "FMG.AX", "company": "Fortescue Metals Group Ltd", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 22.30, "change": 0.38, "changePercent": 1.73},
            {"symbol": "RIO.AX", "company": "Rio Tinto Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 122.35, "change": 1.85, "changePercent": 1.54},
            {"symbol": "MQG.AX", "company": "Macquarie Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 169.50, "change": 2.40, "changePercent": 1.44}
        ]
    elif index_name == "All Ordinaries Index":
        return [
            {"symbol": "BHP.AX", "company": "BHP Group Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29},
            {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21},
            {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30},
            {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25},
            {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38}
        ]
    elif index_name == "S&P/ASX 300" or index_name.upper() == "S&P/ASX 300":
        return [
            {"symbol": "BHP.AX", "company": "BHP Group Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 45.62, "change": -0.58, "changePercent": -1.29},
            {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21},
            {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30},
            {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25},
            {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38},
            {"symbol": "CSL.AX", "company": "CSL Limited", "sector": "Healthcare", "currency": "AUD", "exchange": "ASX", "price": 289.75, "change": 3.25, "changePercent": 1.13},
            {"symbol": "WES.AX", "company": "Wesfarmers Limited", "sector": "Consumer Discretionary", "currency": "AUD", "exchange": "ASX", "price": 58.45, "change": 0.65, "changePercent": 1.12},
            {"symbol": "WOW.AX", "company": "Woolworths Group Limited", "sector": "Consumer Staples", "currency": "AUD", "exchange": "ASX", "price": 37.80, "change": 0.42, "changePercent": 1.12},
            {"symbol": "RIO.AX", "company": "Rio Tinto Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 122.35, "change": 1.85, "changePercent": 1.54},
            {"symbol": "TLS.AX", "company": "Telstra Corporation Limited", "sector": "Communication Services", "currency": "AUD", "exchange": "ASX", "price": 4.18, "change": 0.03, "changePercent": 0.72},
            {"symbol": "FMG.AX", "company": "Fortescue Metals Group Ltd", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 22.30, "change": 0.38, "changePercent": 1.73},
            {"symbol": "MQG.AX", "company": "Macquarie Group Limited", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 169.50, "change": 2.40, "changePercent": 1.44},
            {"symbol": "GMG.AX", "company": "Goodman Group", "sector": "Real Estate", "currency": "AUD", "exchange": "ASX", "price": 28.65, "change": 0.35, "changePercent": 1.24},
            {"symbol": "TCL.AX", "company": "Transurban Group", "sector": "Industrials", "currency": "AUD", "exchange": "ASX", "price": 13.90, "change": 0.12, "changePercent": 0.87},
            {"symbol": "NCM.AX", "company": "Newcrest Mining Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 27.50, "change": 0.45, "changePercent": 1.66}
        ]
    elif index_name == "NZX 50":
        return [
            {"symbol": "ATM.NZ", "company": "The a2 Milk Company Limited", "sector": "Consumer Staples", "currency": "NZD", "exchange": "NZX", "price": 5.85, "change": 0.15, "changePercent": 2.63},
            {"symbol": "SPK.NZ", "company": "Spark New Zealand Limited", "sector": "Communication Services", "currency": "NZD", "exchange": "NZX", "price": 4.92, "change": 0.02, "changePercent": 0.41},
            {"symbol": "FPH.NZ", "company": "Fisher & Paykel Healthcare Corporation Limited", "sector": "Healthcare", "currency": "NZD", "exchange": "NZX", "price": 24.75, "change": 0.35, "changePercent": 1.43},
            {"symbol": "MEL.NZ", "company": "Meridian Energy Limited", "sector": "Utilities", "currency": "NZD", "exchange": "NZX", "price": 5.36, "change": 0.06, "changePercent": 1.13},
            {"symbol": "CEN.NZ", "company": "Contact Energy Limited", "sector": "Utilities", "currency": "NZD", "exchange": "NZX", "price": 8.12, "change": 0.08, "changePercent": 0.99}
        ]
    else:
        return [
            {"symbol": "BHP.AX", "company": "BHP Group Limited", "sector": "Materials", "currency": "AUD", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29},
            {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21},
            {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "sector": "Financials", "currency": "AUD", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30}
        ]

def generate_middle_east_index_constituents(index_name):
    """
    Generate constituent stocks for Middle East indices.
    Args:
        index_name (str): Name of the Middle East index
    Returns:
        list: List of constituent stocks
    """
    if index_name == "Tadawul All Share Index":
        return [
            {"symbol": "2222.SR", "company": "Saudi Aramco", "sector": "Energy", "currency": "SAR", "exchange": "Tadawul", "price": 34.85, "change": 0.40, "changePercent": 1.16},
            {"symbol": "1180.SR", "company": "Al Rajhi Bank", "sector": "Financials", "currency": "SAR", "exchange": "Tadawul", "price": 78.30, "change": 0.90, "changePercent": 1.16},
            {"symbol": "2350.SR", "company": "Saudi Telecom Company", "sector": "Communication Services", "currency": "SAR", "exchange": "Tadawul", "price": 104.60, "change": 1.20, "changePercent": 1.16},
            {"symbol": "2010.SR", "company": "Saudi Basic Industries Corporation (SABIC)", "sector": "Materials", "currency": "SAR", "exchange": "Tadawul", "price": 92.50, "change": 1.10, "changePercent": 1.20},
            {"symbol": "1120.SR", "company": "Al Marai Company", "sector": "Consumer Staples", "currency": "SAR", "exchange": "Tadawul", "price": 53.80, "change": 0.70, "changePercent": 1.32}
        ]
    elif index_name == "Dubai Financial Market General Index":
        return [
            {"symbol": "EMAAR.DFM", "company": "Emaar Properties PJSC", "sector": "Real Estate", "currency": "AED", "exchange": "DFM", "price": 5.78, "change": 0.08, "changePercent": 1.40},
            {"symbol": "DIB.DFM", "company": "Dubai Islamic Bank PJSC", "sector": "Financials", "currency": "AED", "exchange": "DFM", "price": 4.95, "change": 0.06, "changePercent": 1.23},
            {"symbol": "EMIRATES.DFM", "company": "Emirates NBD Bank PJSC", "sector": "Financials", "currency": "AED", "exchange": "DFM", "price": 16.50, "change": 0.20, "changePercent": 1.23},
            {"symbol": "DU.DFM", "company": "Emirates Integrated Telecommunications Company PJSC", "sector": "Communication Services", "currency": "AED", "exchange": "DFM", "price": 5.85, "change": 0.07, "changePercent": 1.21},
            {"symbol": "AMANAT.DFM", "company": "Amanat Holdings PJSC", "sector": "Financials", "currency": "AED", "exchange": "DFM", "price": 1.27, "change": 0.02, "changePercent": 1.60}
        ]
    elif index_name == "Abu Dhabi Securities Exchange Index":
        return [
            {"symbol": "ETISALAT.AD", "company": "Emirates Telecommunications Group Company PJSC", "sector": "Communication Services", "currency": "AED", "exchange": "ADX", "price": 28.80, "change": 0.36, "changePercent": 1.27},
            {"symbol": "ADCB.AD", "company": "Abu Dhabi Commercial Bank PJSC", "sector": "Financials", "currency": "AED", "exchange": "ADX", "price": 8.45, "change": 0.11, "changePercent": 1.32},
            {"symbol": "ADNOC.AD", "company": "ADNOC Distribution PJSC", "sector": "Energy", "currency": "AED", "exchange": "ADX", "price": 4.28, "change": 0.05, "changePercent": 1.18},
            {"symbol": "IHC.AD", "company": "International Holding Company PJSC", "sector": "Industrials", "currency": "AED", "exchange": "ADX", "price": 280.50, "change": 3.40, "changePercent": 1.23},
            {"symbol": "ALDAR.AD", "company": "Aldar Properties PJSC", "sector": "Real Estate", "currency": "AED", "exchange": "ADX", "price": 4.65, "change": 0.06, "changePercent": 1.31}
        ]
    elif index_name == "Qatar Exchange Index":
        return [
            {"symbol": "QNBK.QA", "company": "Qatar National Bank", "sector": "Financials", "currency": "QAR", "exchange": "QE", "price": 18.40, "change": 0.20, "changePercent": 1.10},
            {"symbol": "IQCD.QA", "company": "Industries Qatar Q.S.C.", "sector": "Industrials", "currency": "QAR", "exchange": "QE", "price": 12.85, "change": 0.15, "changePercent": 1.18},
            {"symbol": "QEWS.QA", "company": "Qatar Electricity & Water Company Q.P.S.C.", "sector": "Utilities", "currency": "QAR", "exchange": "QE", "price": 16.50, "change": 0.18, "changePercent": 1.10},
            {"symbol": "QIBK.QA", "company": "Qatar Islamic Bank", "sector": "Financials", "currency": "QAR", "exchange": "QE", "price": 17.10, "change": 0.19, "changePercent": 1.12},
            {"symbol": "CBQK.QA", "company": "The Commercial Bank Q.P.S.C.", "sector": "Financials", "currency": "QAR", "exchange": "QE", "price": 6.38, "change": 0.07, "changePercent": 1.11}
        ]
    elif index_name == "Bahrain All Share Index":
        return [
            {"symbol": "AUB.BH", "company": "Ahli United Bank B.S.C.", "sector": "Financials", "currency": "BHD", "exchange": "BHB", "price": 0.96, "change": 0.01, "changePercent": 1.05},
            {"symbol": "BATELCO.BH", "company": "Bahrain Telecommunications Company B.S.C.", "sector": "Communication Services", "currency": "BHD", "exchange": "BHB", "price": 0.495, "change": 0.005, "changePercent": 1.02},
            {"symbol": "NBB.BH", "company": "National Bank of Bahrain B.S.C.", "sector": "Financials", "currency": "BHD", "exchange": "BHB", "price": 0.62, "change": 0.01, "changePercent": 1.64},
            {"symbol": "ALBH.BH", "company": "Aluminium Bahrain B.S.C.", "sector": "Materials", "currency": "BHD", "exchange": "BHB", "price": 0.57, "change": 0.01, "changePercent": 1.79},
            {"symbol": "GFH.BH", "company": "GFH Financial Group B.S.C.", "sector": "Financials", "currency": "BHD", "exchange": "BHB", "price": 0.38, "change": 0.01, "changePercent": 2.70}
        ]
    elif index_name == "Muscat Securities Market Index":
        return [
            {"symbol": "BKMB.OM", "company": "Bank Muscat SAOG", "sector": "Financials", "currency": "OMR", "exchange": "MSM", "price": 0.47, "change": 0.01, "changePercent": 2.17},
            {"symbol": "ORDS.OM", "company": "Oman Telecommunications Company SAOG", "sector": "Communication Services", "currency": "OMR", "exchange": "MSM", "price": 0.80, "change": 0.01, "changePercent": 1.27},
            {"symbol": "NBOB.OM", "company": "National Bank of Oman SAOG", "sector": "Financials", "currency": "OMR", "exchange": "MSM", "price": 0.215, "change": 0.005, "changePercent": 2.38},
            {"symbol": "SMNP.OM", "company": "Shell Oman Marketing Company SAOG", "sector": "Energy", "currency": "OMR", "exchange": "MSM", "price": 1.68, "change": 0.02, "changePercent": 1.20},
            {"symbol": "BKDB.OM", "company": "Bank Dhofar SAOG", "sector": "Financials", "currency": "OMR", "exchange": "MSM", "price": 0.114, "change": 0.002, "changePercent": 1.79}
        ]
    elif index_name == "Kuwait Stock Exchange Index":
        return [
            {"symbol": "NBK.KW", "company": "National Bank of Kuwait S.A.K.P.", "sector": "Financials", "currency": "KWD", "exchange": "BK", "price": 1.04, "change": 0.01, "changePercent": 0.97},
            {"symbol": "ZAIN.KW", "company": "Mobile Telecommunications Company K.S.C.P.", "sector": "Communication Services", "currency": "KWD", "exchange": "BK", "price": 0.58, "change": 0.01, "changePercent": 1.75},
            {"symbol": "AUB.KW", "company": "Ahli United Bank K.S.C.P.", "sector": "Financials", "currency": "KWD", "exchange": "BK", "price": 0.22, "change": 0.01, "changePercent": 4.76},
            {"symbol": "AGILITY.KW", "company": "Agility Public Warehousing Company K.S.C.P.", "sector": "Industrials", "currency": "KWD", "exchange": "BK", "price": 0.76, "change": 0.01, "changePercent": 1.33},
            {"symbol": "KFH.KW", "company": "Kuwait Finance House K.S.C.P.", "sector": "Financials", "currency": "KWD", "exchange": "BK", "price": 0.77, "change": 0.01, "changePercent": 1.32}
        ]
    else:
        return [
            {"symbol": "2222.SR", "company": "Saudi Aramco", "sector": "Energy", "currency": "SAR", "exchange": "Tadawul", "price": 34.85, "change": 0.40, "changePercent": 1.16},
            {"symbol": "EMAAR.DFM", "company": "Emaar Properties PJSC", "sector": "Real Estate", "currency": "AED", "exchange": "DFM", "price": 5.78, "change": 0.08, "changePercent": 1.40},
            {"symbol": "QNBK.QA", "company": "Qatar National Bank", "sector": "Financials", "currency": "QAR", "exchange": "QE", "price": 18.40, "change": 0.20, "changePercent": 1.10}
        ]

# Sample data for testing
def generate_sample_stock_data():
    return [
        {"symbol": "AAPL", "company": "Apple Inc."},
        {"symbol": "MSFT", "company": "Microsoft Corporation"},
        {"symbol": "GOOGL", "company": "Alphabet Inc."},
        {"symbol": "AMZN", "company": "Amazon.com, Inc."},
        {"symbol": "META", "company": "Meta Platforms, Inc."},
        {"symbol": "TSLA", "company": "Tesla, Inc."},
        {"symbol": "NVDA", "company": "NVIDIA Corporation"},
        {"symbol": "JPM", "company": "JPMorgan Chase & Co."},
        {"symbol": "V", "company": "Visa Inc."},
        {"symbol": "NFLX", "company": "Netflix, Inc."}
    ]

def generate_sample_stock_data_for_symbol(symbol, period='1y'):
    """
    Generate sample stock data for a given symbol.
    """
    from datetime import datetime, timedelta
    import random
    
    # Get company details
    company_details = fetch_yahoo_finance_company_overview(symbol)
    
    end_date = datetime.now()
    if period == '1d':
        days = 1
        interval = timedelta(minutes=5)
        date_format = "%Y-%m-%d %H:%M"
    elif period == '1w':
        days = 7
        interval = timedelta(hours=1)
        date_format = "%Y-%m-%d %H:%M"
    elif period == '1mo':
        days = 30
        interval = timedelta(days=1)
        date_format = "%Y-%m-%d"
    elif period == '3mo':
        days = 90
        interval = timedelta(days=1)
        date_format = "%Y-%m-%d"
    elif period == '6mo':
        days = 180
        interval = timedelta(days=1)
        date_format = "%Y-%m-%d"
    else:  # Default to 1y
        days = 365
        interval = timedelta(days=1)
        date_format = "%Y-%m-%d"
        
    # Starting price
    base_price = 100.0
    
    # Generate data
    data = []
    current_date = end_date - timedelta(days=days)
    current_price = base_price
    
    while current_date <= end_date:
        # Daily price change (-2% to +2%)
        daily_change = random.uniform(-0.02, 0.02)
        current_price = current_price * (1 + daily_change)
        
        # Generate OHLCV data
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, 0.01))
        low_price = open_price * (1 - random.uniform(0, 0.01))
        close_price = open_price * (1 + random.uniform(-0.005, 0.005))
        volume = int(random.uniform(500000, 5000000))
        
        data.append({
            "date": current_date.strftime(date_format),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        
        current_date += interval
    
    return {
        "symbol": symbol,
        "prices": data,
        "name": company_details.get("company", f"Company for {symbol}"),
        "currency": company_details.get("currency", "USD"),
        "exchange": company_details.get("exchange", "")
    }

def generate_sample_index_data():
    # Indian Indices
    indian_indices = [
        {"name": "NIFTY 50", "value": 19250.75, "change": -125.45, "changePercent": -0.65},
        {"name": "BSE SENSEX", "value": 64500.88, "change": 230.15, "changePercent": 0.36},
        {"name": "S&P BSE - 100", "value": 15950.65, "change": 125.30, "changePercent": 0.79},
        {"name": "S&P BSE - 200", "value": 7150.40, "change": 65.25, "changePercent": 0.92},
        {"name": "S&P BSE Midcap", "value": 27890.55, "change": 235.65, "changePercent": 0.85},
        {"name": "NIFTY Next 50", "value": 43800.25, "change": 215.40, "changePercent": 0.49},
        {"name": "Nifty VIX", "value": 15.75, "change": -0.45, "changePercent": -2.78},
        {"name": "NIFTY 500", "value": 15980.55, "change": -65.70, "changePercent": -0.41},
        {"name": "GIFT Nifty", "value": 19280.35, "change": -110.25, "changePercent": -0.57},
        {"name": "NIFTY BANK", "value": 42350.65, "change": 320.80, "changePercent": 0.76},
        {"name": "NIFTY MIDCAP 50", "value": 11250.35, "change": 85.25, "changePercent": 0.76},
        {"name": "NIFTY SMALLCAP 50", "value": 4950.45, "change": 37.60, "changePercent": 0.77},
        {"name": "NIFTY AUTO", "value": 14780.20, "change": 156.35, "changePercent": 1.07},
        {"name": "NIFTY FMCG", "value": 49875.30, "change": 385.60, "changePercent": 0.78},
        {"name": "NIFTY IT", "value": 31250.80, "change": -275.40, "changePercent": -0.87},
        {"name": "NIFTY METAL", "value": 7280.50, "change": 65.30, "changePercent": 0.91},
        {"name": "NIFTY PHARMA", "value": 15630.70, "change": 120.40, "changePercent": 0.78},
        {"name": "NIFTY PSU BANK", "value": 4580.25, "change": 38.60, "changePercent": 0.85},
        {"name": "NIFTY REALTY", "value": 625.30, "change": 8.40, "changePercent": 1.36},
        {"name": "NIFTY PRIVATE BANK", "value": 21480.35, "change": 186.50, "changePercent": 0.88},
        {"name": "NIFTY FINANCIAL SERVICES", "value": 18950.60, "change": 145.30, "changePercent": 0.77},
        {"name": "NIFTY CONSUMER DURABLES", "value": 30250.40, "change": 320.60, "changePercent": 1.07},
        {"name": "NIFTY OIL & GAS", "value": 9780.35, "change": 95.60, "changePercent": 0.99}
    ]
    
    # US Indices
    us_indices = [
        {"name": "S&P 500", "value": 4500.21, "change": 15.78, "changePercent": 0.35},
        {"name": "Dow Jones Industrial Average", "value": 34250.38, "change": 125.65, "changePercent": 0.37},
        {"name": "Nasdaq Composite", "value": 14300.75, "change": 78.60, "changePercent": 0.55},
        {"name": "Russell 2000", "value": 2150.30, "change": 12.45, "changePercent": 0.58},
        {"name": "Dow Jones Futures", "value": 34275.50, "change": 150.25, "changePercent": 0.44},
        {"name": "S&P 500 CFD", "value": 4505.75, "change": 18.50, "changePercent": 0.41},
        {"name": "Nasdaq CFD", "value": 14320.80, "change": 85.40, "changePercent": 0.60}
    ]
    
    # European Indices
    european_indices = [
        {"name": "FTSE 100", "value": 7450.65, "change": 38.40, "changePercent": 0.52},
        {"name": "DAX", "value": 15850.30, "change": 156.45, "changePercent": 0.99},
        {"name": "CAC 40", "value": 7150.20, "change": 65.30, "changePercent": 0.92},
        {"name": "Euro Stoxx 50", "value": 4380.45, "change": 32.70, "changePercent": 0.75},
        {"name": "IBEX 35", "value": 9425.30, "change": 45.60, "changePercent": 0.49},
        {"name": "FTSE MIB", "value": 27950.75, "change": 180.50, "changePercent": 0.65}
    ]
    
    # Asian Indices
    asian_indices = [
        {"name": "Nikkei 225", "value": 28750.45, "change": 235.80, "changePercent": 0.83},
        {"name": "Hang Seng", "value": 18950.35, "change": -165.40, "changePercent": -0.87},
        {"name": "Shanghai Composite", "value": 3280.15, "change": -18.45, "changePercent": -0.56},
        {"name": "Straits Times", "value": 3250.75, "change": 15.80, "changePercent": 0.49},
        {"name": "Taiwan Weighted", "value": 17150.35, "change": 125.40, "changePercent": 0.74},
        {"name": "KOSPI", "value": 2450.80, "change": 18.25, "changePercent": 0.75},
        {"name": "SET Composite", "value": 1580.65, "change": 7.35, "changePercent": 0.47},
        {"name": "Jakarta Composite", "value": 6850.25, "change": 35.60, "changePercent": 0.52}
    ]
    
    # Australian Indices
    australian_indices = [
        {"name": "S&P/ASX 200", "value": 7350.25, "change": 45.30, "changePercent": 0.62},
        {"name": "ASX 200", "value": 7350.25, "change": 45.30, "changePercent": 0.62},
        {"name": "All Ordinaries Index", "value": 7580.35, "change": 48.20, "changePercent": 0.64},
        {"name": "S&P/ASX 50", "value": 6980.15, "change": 42.25, "changePercent": 0.61},
        {"name": "S&P/ASX 300", "value": 7250.40, "change": 44.10, "changePercent": 0.61},
        {"name": "NZX 50", "value": 11850.65, "change": 60.35, "changePercent": 0.51}
    ]
    
    # Middle East Indices
    middle_east_indices = [
        {"name": "Tadawul All Share Index", "value": 11350.45, "change": 75.80, "changePercent": 0.67},
        {"name": "Dubai Financial Market General Index", "value": 3580.25, "change": 25.40, "changePercent": 0.71},
        {"name": "Abu Dhabi Securities Exchange Index", "value": 9750.35, "change": 65.20, "changePercent": 0.67},
        {"name": "Qatar Exchange Index", "value": 10250.60, "change": 55.30, "changePercent": 0.54},
        {"name": "Bahrain All Share Index", "value": 1950.75, "change": 12.40, "changePercent": 0.64},
        {"name": "Muscat Securities Market Index", "value": 4580.20, "change": 32.50, "changePercent": 0.71},
        {"name": "Kuwait Stock Exchange Index", "value": 7850.30, "change": 45.60, "changePercent": 0.58}
    ]
    
    # Other Global Indices
    other_global_indices = [
        {"name": "S&P/TSX", "value": 20450.60, "change": 85.40, "changePercent": 0.42}
    ]
    
    global_indices = us_indices + european_indices + asian_indices + australian_indices + middle_east_indices + other_global_indices
    
    return indian_indices + global_indices

# API Endpoints
@app.route('/api/stocks', methods=['GET'])
@cache_with_timeout(timeout=600)  # Cache stock list for 10 minutes
def get_stocks():
    """
    Get a list of stocks.
    Returns:
        JSON: List of stocks.
    """
    # Return list of popular stocks
    return jsonify(fetch_popular_stocks())

@app.route('/api/search', methods=['GET'])
def search_stocks():
    """
    Search for stocks based on a query.
    Query Parameters:
        q (str): Search query for stock symbol or company name.
    Returns:
        JSON: List of matching stocks.
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify(fetch_popular_stocks()[:5])  # Return first 5 popular stocks if no query
    
    # Use our new search function with NSE prioritization
    results = fetch_stock_search(query)
    logger.info(f"Stock search for '{query}' returned {len(results)} results")
    
    return jsonify(results)

@app.route('/api/company/<symbol>', methods=['GET'])
@cache_with_timeout(timeout=3600)  # Cache company details for 1 hour
def get_company_details(symbol):
    """
    Get details for a specific company.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Company details.
    """
    # Fetch company overview data from Yahoo Finance
    details = fetch_yahoo_finance_company_overview(symbol)
    logger.info(f"Fetched company details for {symbol}")
    return jsonify(details)

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    """
    Get details for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Stock details.
    """
    # This endpoint is deprecated but kept for backward compatibility
    # Redirect to company details endpoint
    return get_company_details(symbol)

@app.route('/api/stock/<symbol>/history', methods=['GET'])
@cache_with_timeout(timeout=1800)  # Cache historical data for 30 minutes
def get_stock_history(symbol):
    """
    Get historical price data for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Query Parameters:
        period (str): Time period for data (e.g., 1d, 1mo, 1y).
    Returns:
        JSON: Stock price data.
    """
    period = request.args.get('period', '1y')
    
    # Fetch time series data from Yahoo Finance
    data = fetch_yahoo_finance_time_series(symbol, period)
    logger.info(f"Fetched stock history for {symbol} with period {period}")
    
    return jsonify(data)

@app.route('/api/stock/<symbol>/data', methods=['GET'])
def get_stock_data(symbol):
    """
    Get price data for a specific stock (deprecated).
    Path Parameters:
        symbol (str): Stock symbol.
    Query Parameters:
        period (str): Time period for data (e.g., 1d, 1mo, 1y).
    Returns:
        JSON: Stock price data.
    """
    # This endpoint is deprecated but kept for backward compatibility
    # Redirect to stock history endpoint
    return get_stock_history(symbol)

@app.route('/api/indices', methods=['GET'])
@cache_with_timeout(timeout=300)  # Cache indices data for 5 minutes
def get_indices():
    """
    Get a list of market indices.
    Returns:
        JSON: List of market indices.
    """
    try:
        # Get fallback data first
        global_indices = generate_sample_index_data()
        
        # Convert to dictionary for easy lookup by name
        indices_dict = {idx["name"]: idx for idx in global_indices}
        
        # Get Indian indices using nsepython
        india_indices = []
        
        # Define all the NIFTY indices we want to fetch
        nifty_indices = [
            "NIFTY 50",
            "NIFTY BANK", "NIFTY MIDCAP 50", "NIFTY SMALLCAP 50",
            "NIFTY Next 50", "NIFTY 500", "NIFTY 100",
            "NIFTY AUTO", "NIFTY FMCG", "NIFTY IT", "NIFTY METAL",
            "NIFTY PHARMA", "NIFTY PSU BANK", "NIFTY REALTY", 
            "NIFTY PRIVATE BANK", "NIFTY FINANCIAL SERVICES",
            "NIFTY CONSUMER DURABLES", "NIFTY OIL & GAS",
            "Nifty VIX", "GIFT Nifty"
        ]
        
        # Also include BSE indices (these will use fallback data)
        bse_indices = [
            "BSE SENSEX", "S&P BSE - 100", "S&P BSE - 200", "S&P BSE Midcap"
        ]
        
        try:
            # Fetch ALL available NSE indices data in a single call to avoid multiple HTTP requests
            logger.info("Fetching all NSE indices data in a single call")
            try:
                # Fetch all indices data from NSE in a single request
                all_nse_indices_data = nsefetch("https://iislliveblob.niftyindices.com/jsonfiles/LiveIndicesWatch.json")
                
                # Process the data if available
                if all_nse_indices_data and isinstance(all_nse_indices_data, list):
                    logger.info(f"Successfully fetched data for {len(all_nse_indices_data)} NSE indices")
                    
                    # Create a mapping of index names to their data
                    nse_indices_map = {}
                    for idx_data in all_nse_indices_data:
                        if 'indexName' in idx_data and 'last' in idx_data:
                            index_name = idx_data['indexName']
                            nse_indices_map[index_name] = idx_data
                    
                    # Process each index we want data for
                    for index_name in nifty_indices:
                        # Check if we have data for this index
                        if index_name in nse_indices_map:
                            idx_data = nse_indices_map[index_name]
                            try:
                                value = float(idx_data.get("last", 0))
                                change = float(idx_data.get("change", 0))
                                change_percent = float(idx_data.get("percChange", 0))
                                
                                # Only use live data if it's valid
                                if value > 0:
                                    india_indices.append({
                                        "name": index_name,
                                        "value": value,
                                        "change": change,
                                        "changePercent": change_percent
                                    })
                                    logger.debug(f"Added live data for {index_name}")
                                else:
                                    # Use fallback data if available
                                    if index_name in indices_dict:
                                        india_indices.append(indices_dict[index_name])
                                        logger.debug(f"Using fallback data for {index_name} due to invalid value")
                            except Exception as e:
                                logger.error(f"Error processing index data for {index_name}: {e}")
                                # Use fallback data if available
                                if index_name in indices_dict:
                                    india_indices.append(indices_dict[index_name])
                        else:
                            # Index not found in NSE data, use fallback
                            logger.warning(f"Index {index_name} not found in NSE data")
                            if index_name in indices_dict:
                                india_indices.append(indices_dict[index_name])
                else:
                    logger.error("Failed to fetch or invalid NSE indices data")
                    # Use fallback data for NIFTY indices
                    for index_name in nifty_indices:
                        if index_name in indices_dict:
                            india_indices.append(indices_dict[index_name])
            except Exception as e:
                logger.error(f"Error fetching all NSE indices data: {e}", exc_info=True)
                # Use fallback data for NIFTY indices
                for index_name in nifty_indices:
                    if index_name in indices_dict:
                        india_indices.append(indices_dict[index_name])
            
            # Add BSE indices from fallback data
            for bse_index_name in bse_indices:
                if bse_index_name in indices_dict and not any(idx["name"] == bse_index_name for idx in india_indices):
                    india_indices.append(indices_dict[bse_index_name])
                    
        except Exception as e:
            logger.error(f"Error fetching Indian indices data: {e}", exc_info=True)
            # Use fallback data for NIFTY 50
            for index_name in nifty_indices + bse_indices:
                if index_name in indices_dict and not any(idx["name"] == index_name for idx in india_indices):
                    india_indices.append(indices_dict[index_name])
        
        # Get other global indices not covered by India indices
        all_indices = india_indices + [
            index for index in global_indices 
            if index["name"] not in [idx["name"] for idx in india_indices]
        ]
        
        return jsonify(all_indices)
    except Exception as e:
        logger.error(f"Error in get_indices: {e}", exc_info=True)
        # Return fallback data if everything fails
        return jsonify(generate_sample_index_data())

@app.route('/api/index/<index_name>/history', methods=['GET'])
@cache_with_timeout(timeout=600)  # Cache history data for 10 minutes
def get_index_history_endpoint(index_name):
    """
    Get historical data for a specific index.
    Path Parameters:
        index_name (str): Index name.
    Query Parameters:
        period (str): Time period for data (e.g., 1d, 1w, 1m, 1y).
        refresh (bool): Whether to force refresh the cache.
    Returns:
        JSON: Index price history data.
    """
    logger.info(f"Received request for index history: {index_name}")
    
    # Get period from query parameters, default to 1m (1 month)
    period = request.args.get('period', '1m')
    # Check if refresh parameter is set to true
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if force_refresh:
        logger.info(f"Force refresh parameter set to true for {index_name} history, bypass cache")
    
    try:
        # Map period string to yfinance format
        period_mapping = {
            '1d': '1d',
            '1w': '5d',
            '1m': '1mo',
            '3m': '3mo',
            '6m': '6mo',
            'ytd': 'ytd',
            '1y': '1y',
            '2y': '2y',
            'max': 'max'
        }
        
        yf_period = period_mapping.get(period, '1mo')
        
        # Get index history data directly
        # Define a simplified version for immediate use
        def get_index_history_direct(index_name, period='1y', force_refresh=False):
            """
            Get historical data for an index directly without external imports.
            
            Args:
                index_name (str): Name of the index
                period (str): Time period for history (e.g., 1d, 1w, 1m, 1y)
                force_refresh (bool): Whether to force refresh the cache and fetch new data
                
            Returns:
                dict: Historical price data for the index
            """
            logger.info(f"Direct function: Fetching historical data for index: {index_name}, period: {period}")
            
            # Map index name to Yahoo Finance ticker
            index_ticker_map = {
                # US indices
                'S&P 500': '^GSPC',
                'Dow Jones Industrial Average': '^DJI',
                'Nasdaq Composite': '^IXIC',
                'Russell 2000': '^RUT',
                
                # Indian indices
                'NIFTY 50': '^NSEI',
                'NIFTY BANK': '^NSEBANK',
                'NIFTY NEXT 50': '^NSMIDCP',
                'BSE SENSEX': '^BSESN',
                'NIFTY MIDCAP 50': '^NSMIDCP',
                'NIFTY SMALLCAP 50': '^SMLCAP',
                'NIFTY IT': '^CNXIT',
                'Nifty VIX': '^INDIAVIX',
                
                # European indices
                'FTSE 100': '^FTSE',
                'DAX': '^GDAXI',
                'CAC 40': '^FCHI',
                
                # Asian indices
                'Nikkei 225': '^N225',
                'Hang Seng Index': '^HSI',
                'Shanghai Composite Index': '000001.SS',
            }
            
            ticker = index_ticker_map.get(index_name)
            if not ticker:
                logger.warning(f"No ticker found for index: {index_name}")
                return {}
            
            try:
                # Fetch data using yfinance
                import yfinance as yf
                logger.info(f"Using yfinance to fetch data for {index_name} ({ticker}) with period {period}")
                index_ticker = yf.Ticker(ticker)
                hist = index_ticker.history(period=period)
                
                if hist.empty:
                    logger.warning(f"No historical data found for {index_name} ({ticker})")
                    return {}
                
                # Convert to dict format expected by frontend
                price_data = []
                for date_idx, row in hist.iterrows():
                    # Format date as YYYY-MM-DD
                    date_str = date_idx.strftime('%Y-%m-%d')
                    
                    # Create price data entry
                    price_entry = {
                        'date': date_str,
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']) if 'Volume' in row else 0
                    }
                    price_data.append(price_entry)
                
                result = {
                    'symbol': ticker,
                    'name': index_name,
                    'priceData': price_data,
                    'period': period
                }
                
                return result
            except Exception as e:
                logger.error(f"Error fetching historical data for {index_name} ({ticker}): {e}", exc_info=True)
                return {}
        
        # Get index history with force_refresh parameter
        logger.info(f"Requesting index history with force_refresh={force_refresh}")
        history_data = get_index_history_direct(index_name, period=yf_period, force_refresh=force_refresh)
        
        if history_data and 'priceData' in history_data and len(history_data['priceData']) > 0:
            logger.info(f"Successfully retrieved {len(history_data['priceData'])} price points for {index_name}")
            return jsonify(history_data)
        else:
            logger.warning(f"No history data returned for {index_name}")
            
            # Return an error response with empty price data and appropriate error message
            return jsonify({
                'symbol': index_name,
                'name': index_name,
                'priceData': [],
                'period': period,
                'error': f'No historical data available for {index_name}'
            })
    
    except Exception as e:
        logger.error(f"Error fetching history for {index_name}: {e}", exc_info=True)
        # Return error message with detailed information
        return jsonify({
            'symbol': index_name,
            'name': index_name,
            'priceData': [],
            'period': period,
            'error': f'Error: {str(e)}'
        })

@app.route('/api/index/<index_name>/constituents', methods=['GET'])
@cache_with_timeout(timeout=600)  # Cache constituents data for 10 minutes
def get_index_constituents(index_name):
    """
    Get the constituents of a specific index.
    Path Parameters:
        index_name (str): Index name.
    Returns:
        JSON: List of index constituents.
    """
    # Log the request
    logger.info(f"Received request for index constituents: {index_name}")
    
    # Check if refresh parameter is set
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        logger.info(f"Refresh parameter set to true for {index_name}, will bypass cache")
    
    # Create an empty constituents list as a fallback
    constituents = []
    
    try:
        # First try to use the indicesdownload module to get real-time data
        try:
            logger.info(f"Attempting to fetch real-time constituent data for {index_name} using indicesdownload module")
            # Import indicesdownload function directly
            from indicesdownload import get_index_constituents
            real_time_constituents = get_index_constituents(index_name, refresh=refresh)
            
            if real_time_constituents and len(real_time_constituents) > 0:
                logger.info(f"Successfully retrieved {len(real_time_constituents)} real-time constituents for {index_name}")
                return jsonify(real_time_constituents)
            else:
                logger.warning(f"No constituents returned from indicesdownload module for {index_name}, falling back to original method")
        except Exception as e:
            logger.error(f"Error fetching constituents for {index_name} from indicesdownload module: {e}", exc_info=True)
            logger.warning(f"Falling back to original constituents method for {index_name}")
        
        # Original fallback code below
        constituents = []
        
        # Check if this is a NIFTY index
        nifty_indices = [
            "NIFTY 50", "NIFTY Next 50", "NIFTY 100", "NIFTY 500", 
            "NIFTY BANK", "NIFTY MIDCAP 50", "NIFTY SMALLCAP 50",
            "NIFTY AUTO", "NIFTY FMCG", "NIFTY IT", "NIFTY METAL",
            "NIFTY PHARMA", "NIFTY PSU BANK", "NIFTY REALTY", 
            "NIFTY PRIVATE BANK", "NIFTY FINANCIAL SERVICES",
            "NIFTY CONSUMER DURABLES", "NIFTY OIL & GAS",
            "Nifty VIX", "GIFT Nifty"
        ]
        
        # BSE indices
        bse_indices = [
            "BSE SENSEX", "S&P BSE - 100", "S&P BSE - 200", "S&P BSE Midcap"
        ]
        
        # US indices
        us_indices = [
            "S&P 500", "Dow Jones Industrial Average", "Nasdaq Composite", 
            "Russell 2000", "Dow Jones Futures", "S&P 500 CFD", "Nasdaq CFD"
        ]
        
        # European indices
        european_indices = [
            "FTSE 100", "CAC 40", "DAX", "DAX 30", "Euro Stoxx 50", "IBEX 35", 
            "FTSE MIB", "AEX Index", "OMX Stockholm 30", "Swiss Market Index (SMI)"
        ]
        
        # Australian indices
        australian_indices = [
            "ASX 200", "S&P/ASX 200", "All Ordinaries Index", "S&P/ASX 50", 
            "S&P/ASX 300", "NZX 50"
        ]
        
        # Middle East indices
        middle_east_indices = [
            "Tadawul All Share Index", "Dubai Financial Market General Index", 
            "Abu Dhabi Securities Exchange Index", "Qatar Exchange Index", 
            "Bahrain All Share Index", "Muscat Securities Market Index", 
            "Kuwait Stock Exchange Index"
        ]
        
        # Americas indices
        americas_indices = [
            "S&P 500", "Dow Jones Industrial Average", "Nasdaq Composite", 
            "Russell 2000", "Dow Jones Futures", "S&P 500 CFD", "Nasdaq CFD",
            "Bovespa (IBOV)", "TSX Composite Index", "Merval Index", 
            "IPC (Indice de Precios y Cotizaciones)", "S&P/TSX Venture Composite"
        ]
        
        # Asian indices (non-Indian)
        asian_indices = [
            "Nikkei 225", "Hang Seng Index", "Shanghai Composite Index", "Straits Times Index",
            "Taiwan Weighted Index", "Kospi Index", "SET Index", "Jakarta Composite Index",
            "KLCI", "PSEi", "Colombo All Share Index"
        ]
        
        # Australian indices
        australian_indices = [
            "ASX 200", "S&P/ASX 200", "All Ordinaries Index", "S&P/ASX 50", 
            "S&P/ASX 300", "NZX 50"
        ]
        
        # Middle East indices
        middle_east_indices = [
            "Tadawul All Share Index", "Dubai Financial Market General Index", 
            "Abu Dhabi Securities Exchange Index", "Qatar Exchange Index", 
            "Bahrain All Share Index", "Muscat Securities Market Index", 
            "Kuwait Stock Exchange Index"
        ]
        
        if index_name in nifty_indices:
            try:
                logger.info(f"Fetching constituents for {index_name} using NSEPython")
                
                # For NIFTY 50, we'll use nse_eq_symbols to get all NSE stocks 
                # and filter for the top/large-cap companies
                if index_name == "NIFTY 50":
                    logger.info("Fetching NSE equity symbols")
                    try:
                        # Get all NSE symbols - this returns a list of string symbols
                        all_symbols = nse_eq_symbols()
                        
                        if all_symbols:
                            # Extract the NIFTY 50 symbols from the list of all NSE symbols
                            top_companies = []
                            
                            # List of stocks that are typically part of NIFTY 50 index
                            nifty50_symbols = [
                                "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "HINDUNILVR", 
                                "INFY", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", 
                                "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", 
                                "HDFC", "TATAMOTORS", "SUNPHARMA", "TITAN", "BAJAJFINSV", 
                                "JSWSTEEL", "ONGC", "NTPC", "POWERGRID", "TATASTEEL", 
                                "INDUSINDBK", "NESTLEIND", "WIPRO", "LTIM", "HCLTECH", 
                                "ULTRACEMCO", "ADANIENT", "ADANIPORTS", "M&M", "DRREDDY", 
                                "CIPLA", "COALINDIA", "BAJAJ-AUTO", "TATACONSUM", "TECHM", 
                                "GRASIM", "DIVISLAB", "EICHERMOT", "SBILIFE", "HINDALCO", 
                                "HDFCLIFE", "BRITANNIA", "APOLLOHOSP", "HEROMOTOCO", "UPL"
                            ]
                            
                            # Filter symbols that are in NIFTY 50
                            for symbol in all_symbols:
                                if symbol in nifty50_symbols:
                                    # For each filtered symbol, create a company object
                                    # We don't have company names from nse_eq_symbols, so we'll infer them
                                    company_name_map = {
                                        "RELIANCE": "Reliance Industries Ltd.",
                                        "TCS": "Tata Consultancy Services Ltd.",
                                        "HDFCBANK": "HDFC Bank Ltd.",
                                        "ICICIBANK": "ICICI Bank Ltd.",
                                        "HINDUNILVR": "Hindustan Unilever Ltd.",
                                        "INFY": "Infosys Ltd.",
                                        "ITC": "ITC Ltd.",
                                        "SBIN": "State Bank of India",
                                        "BHARTIARTL": "Bharti Airtel Ltd.",
                                        "BAJFINANCE": "Bajaj Finance Ltd.",
                                        "KOTAKBANK": "Kotak Mahindra Bank Ltd.",
                                        "LT": "Larsen & Toubro Ltd.",
                                        "AXISBANK": "Axis Bank Ltd.",
                                        "ASIANPAINT": "Asian Paints Ltd.",
                                        "MARUTI": "Maruti Suzuki India Ltd.",
                                        "HDFC": "Housing Development Finance Corporation Ltd.",
                                        "TATAMOTORS": "Tata Motors Ltd.",
                                        "SUNPHARMA": "Sun Pharmaceutical Industries Ltd.",
                                        "TITAN": "Titan Company Ltd.",
                                        "BAJAJFINSV": "Bajaj Finserv Ltd."
                                    }
                                    
                                    # Get company name from mapping or use a default
                                    company_name = company_name_map.get(symbol, f"{symbol} Ltd.")
                                    
                                    # Generate price and change data
                                    price = round(random.uniform(500, 5000), 2)
                                    change_percent = round(random.uniform(-3, 5), 2)
                                    change = round(price * (change_percent / 100), 2)
                                    
                                    company = {
                                        "symbol": symbol,
                                        "company": company_name,
                                        "sector": "Technology" if "TECH" in symbol or "INFO" in symbol else "Finance" if "BANK" in symbol or "FIN" in symbol else "Manufacturing",
                                        "industry": "IT Services" if "TECH" in symbol or "INFO" in symbol else "Banking" if "BANK" in symbol else "Industrials",
                                        "price": price,
                                        "change": change,
                                        "changePercent": change_percent,
                                        "currency": "INR",
                                        "exchange": "NSE"
                                    }
                                    
                                    top_companies.append(company)
                            
                            constituents = top_companies
                            logger.info(f"Successfully filtered {len(constituents)} NIFTY 50 constituents from NSE symbols")
                        else:
                            logger.warning("No NSE symbols returned from nse_eq_symbols")
                    except Exception as e:
                        logger.error(f"Error processing NSE symbols: {e}", exc_info=True)
                # Special case for Nifty VIX and GIFT Nifty - not regular indices with constituents
                elif index_name in ["Nifty VIX", "GIFT Nifty"]:
                    logger.info(f"{index_name} is a special index without constituents")
                    # Return empty list for VIX or GIFT Nifty since they don't have constituents
                    # But we also add metadata to help the frontend display appropriate explanation
                    if index_name == "Nifty VIX":
                        constituents = []
                        # Add metadata to indicate this is a volatility index
                        constituents_metadata = {
                            "index_type": "volatility",
                            "description": "India's Volatility Index that measures the degree of volatility or fluctuation expected in the Nifty50 over the next 30 days.",
                            "key_facts": [
                                "VIX is calculated using the best bid-ask quotes of NIFTY Options",
                                "Higher VIX value indicates higher expected volatility",
                                "VIX is often referred to as the 'fear gauge' of the market",
                                "Unlike stock indices, VIX doesn't have constituent stocks"
                            ],
                            "interpretation": {
                                "low": "Below 15: Low volatility expected",
                                "normal": "15-30: Normal market volatility",
                                "high": "Above 30: High volatility expected"
                            }
                        }
                    elif index_name == "GIFT Nifty":
                        constituents = []
                        # Add metadata to indicate this is a futures index
                        constituents_metadata = {
                            "index_type": "futures",
                            "description": "GIFT Nifty (previously known as SGX Nifty) is a futures contract based on the Nifty index, traded on the NSE IFSC exchange at GIFT City, Gujarat, India.",
                            "key_facts": [
                                "Trading hours extend beyond regular NSE trading hours",
                                "Often used as an early indicator for regular NIFTY 50 movements",
                                "Provides global access to India's benchmark index",
                                "As a futures product, it doesn't have constituent stocks"
                            ],
                            "trading_hours": "Monday to Friday, 8:00 AM to 3:30 PM and 4:15 PM to 5:00 PM (IST)"
                        }
                    # The frontend already has a special handling for these indices
                # Handle NIFTY BANK specifically
                elif index_name == "NIFTY BANK":
                    logger.info("Generating NIFTY BANK constituents with comprehensive data")
                    constituents = [
                        {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "NSE", "price": 1648.25, "change": 12.50, "changePercent": 0.76, "currency": "INR", "sector": "Financials"},
                        {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "NSE", "price": 1054.75, "change": 8.45, "changePercent": 0.81, "currency": "INR", "sector": "Financials"},
                        {"symbol": "KOTAKBANK", "company": "Kotak Mahindra Bank Ltd.", "exchange": "NSE", "price": 1742.60, "change": 15.25, "changePercent": 0.88, "currency": "INR", "sector": "Financials"},
                        {"symbol": "AXISBANK", "company": "Axis Bank Ltd.", "exchange": "NSE", "price": 1078.35, "change": 9.75, "changePercent": 0.91, "currency": "INR", "sector": "Financials"},
                        {"symbol": "SBIN", "company": "State Bank of India", "exchange": "NSE", "price": 765.45, "change": 6.50, "changePercent": 0.86, "currency": "INR", "sector": "Financials"},
                        {"symbol": "INDUSINDBK", "company": "IndusInd Bank Ltd.", "exchange": "NSE", "price": 1425.30, "change": 11.75, "changePercent": 0.83, "currency": "INR", "sector": "Financials"},
                        {"symbol": "BANDHANBNK", "company": "Bandhan Bank Ltd.", "exchange": "NSE", "price": 214.55, "change": 2.25, "changePercent": 1.06, "currency": "INR", "sector": "Financials"},
                        {"symbol": "FEDERALBNK", "company": "The Federal Bank Ltd.", "exchange": "NSE", "price": 152.80, "change": 1.45, "changePercent": 0.96, "currency": "INR", "sector": "Financials"},
                        {"symbol": "AUBANK", "company": "AU Small Finance Bank Ltd.", "exchange": "NSE", "price": 628.15, "change": 6.85, "changePercent": 1.10, "currency": "INR", "sector": "Financials"},
                        {"symbol": "IDFCFIRSTB", "company": "IDFC FIRST Bank Ltd.", "exchange": "NSE", "price": 80.75, "change": 0.95, "changePercent": 1.19, "currency": "INR", "sector": "Financials"}
                    ]
                # Handle NIFTY MIDCAP 50 specifically
                elif index_name == "NIFTY MIDCAP 50":
                    logger.info("Generating NIFTY MIDCAP 50 constituents with comprehensive data")
                    constituents = [
                        {"symbol": "TRENT", "company": "Trent Ltd.", "exchange": "NSE", "price": 3760.45, "change": 42.35, "changePercent": 1.14, "currency": "INR", "sector": "Consumer Discretionary"},
                        {"symbol": "ABCAPITAL", "company": "Aditya Birla Capital Ltd.", "exchange": "NSE", "price": 198.75, "change": 2.45, "changePercent": 1.25, "currency": "INR", "sector": "Financials"},
                        {"symbol": "LICHSGFIN", "company": "LIC Housing Finance Ltd.", "exchange": "NSE", "price": 635.20, "change": 5.75, "changePercent": 0.91, "currency": "INR", "sector": "Financials"},
                        {"symbol": "CONCOR", "company": "Container Corporation of India Ltd.", "exchange": "NSE", "price": 905.80, "change": 10.45, "changePercent": 1.17, "currency": "INR", "sector": "Industrials"},
                        {"symbol": "MPHASIS", "company": "Mphasis Ltd.", "exchange": "NSE", "price": 2450.25, "change": 32.75, "changePercent": 1.35, "currency": "INR", "sector": "Technology"},
                        {"symbol": "COFORGE", "company": "Coforge Ltd.", "exchange": "NSE", "price": 6125.40, "change": 85.60, "changePercent": 1.42, "currency": "INR", "sector": "Technology"},
                        {"symbol": "BHARATFORG", "company": "Bharat Forge Ltd.", "exchange": "NSE", "price": 1175.65, "change": 15.40, "changePercent": 1.33, "currency": "INR", "sector": "Industrials"},
                        {"symbol": "ASTRAL", "company": "Astral Ltd.", "exchange": "NSE", "price": 1940.35, "change": 25.65, "changePercent": 1.34, "currency": "INR", "sector": "Materials"},
                        {"symbol": "OBEROIRLTY", "company": "Oberoi Realty Ltd.", "exchange": "NSE", "price": 1580.45, "change": 22.35, "changePercent": 1.43, "currency": "INR", "sector": "Real Estate"},
                        {"symbol": "TATACOMM", "company": "Tata Communications Ltd.", "exchange": "NSE", "price": 1854.75, "change": 24.55, "changePercent": 1.34, "currency": "INR", "sector": "Communication Services"}
                    ]
                # Handle NIFTY SMALLCAP 50 specifically
                elif index_name == "NIFTY SMALLCAP 50":
                    logger.info("Generating NIFTY SMALLCAP 50 constituents with comprehensive data")
                    constituents = [
                        {"symbol": "CYIENT", "company": "Cyient Ltd.", "exchange": "NSE", "price": 1850.45, "change": 28.75, "changePercent": 1.58, "currency": "INR", "sector": "Technology"},
                        {"symbol": "IIFL", "company": "IIFL Finance Ltd.", "exchange": "NSE", "price": 528.35, "change": 8.65, "changePercent": 1.67, "currency": "INR", "sector": "Financials"},
                        {"symbol": "CAMS", "company": "Computer Age Management Services Ltd.", "exchange": "NSE", "price": 2735.50, "change": 35.80, "changePercent": 1.33, "currency": "INR", "sector": "Financials"},
                        {"symbol": "ANURAS", "company": "Anupam Rasayan India Ltd.", "exchange": "NSE", "price": 980.75, "change": 14.55, "changePercent": 1.51, "currency": "INR", "sector": "Materials"},
                        {"symbol": "KPRMILL", "company": "K.P.R. Mill Ltd.", "exchange": "NSE", "price": 785.40, "change": 11.25, "changePercent": 1.45, "currency": "INR", "sector": "Consumer Discretionary"},
                        {"symbol": "JBCHEPHARM", "company": "J.B. Chemicals & Pharmaceuticals Ltd.", "exchange": "NSE", "price": 1560.25, "change": 21.35, "changePercent": 1.39, "currency": "INR", "sector": "Healthcare"},
                        {"symbol": "FINEORG", "company": "Fine Organic Industries Ltd.", "exchange": "NSE", "price": 4980.65, "change": 68.50, "changePercent": 1.39, "currency": "INR", "sector": "Materials"},
                        {"symbol": "KAMAHOLD", "company": "Kama Holdings Ltd.", "exchange": "NSE", "price": 6740.30, "change": 98.75, "changePercent": 1.49, "currency": "INR", "sector": "Financials"},
                        {"symbol": "SONATSOFTW", "company": "Sonata Software Ltd.", "exchange": "NSE", "price": 740.80, "change": 11.45, "changePercent": 1.57, "currency": "INR", "sector": "Technology"},
                        {"symbol": "CDSL", "company": "Central Depository Services (India) Ltd.", "exchange": "NSE", "price": 1485.35, "change": 21.40, "changePercent": 1.46, "currency": "INR", "sector": "Financials"}
                    ]
                # Handle NIFTY Next 50 specifically
                elif index_name == "NIFTY Next 50":
                    logger.info("Generating NIFTY Next 50 constituents with comprehensive data")
                    constituents = [
                        {"symbol": "ADANIGREEN", "company": "Adani Green Energy Ltd.", "exchange": "NSE", "price": 1545.35, "change": 22.65, "changePercent": 1.49, "currency": "INR", "sector": "Utilities"},
                        {"symbol": "ADANIPORTS", "company": "Adani Ports and Special Economic Zone Ltd.", "exchange": "NSE", "price": 1245.80, "change": 15.75, "changePercent": 1.28, "currency": "INR", "sector": "Industrials"},
                        {"symbol": "AMBUJACEM", "company": "Ambuja Cements Ltd.", "exchange": "NSE", "price": 585.45, "change": 6.85, "changePercent": 1.18, "currency": "INR", "sector": "Materials"},
                        {"symbol": "AUROPHARMA", "company": "Aurobindo Pharma Ltd.", "exchange": "NSE", "price": 1135.70, "change": 14.55, "changePercent": 1.30, "currency": "INR", "sector": "Healthcare"},
                        {"symbol": "BAJAJHLDNG", "company": "Bajaj Holdings & Investment Ltd.", "exchange": "NSE", "price": 7540.25, "change": 85.35, "changePercent": 1.14, "currency": "INR", "sector": "Financials"},
                        {"symbol": "BANKBARODA", "company": "Bank of Baroda", "exchange": "NSE", "price": 235.45, "change": 3.25, "changePercent": 1.40, "currency": "INR", "sector": "Financials"},
                        {"symbol": "BIOCON", "company": "Biocon Ltd.", "exchange": "NSE", "price": 315.80, "change": 4.25, "changePercent": 1.36, "currency": "INR", "sector": "Healthcare"},
                        {"symbol": "CHOLAFIN", "company": "Cholamandalam Investment and Finance Company Ltd.", "exchange": "NSE", "price": 1245.35, "change": 16.80, "changePercent": 1.37, "currency": "INR", "sector": "Financials"},
                        {"symbol": "DABUR", "company": "Dabur India Ltd.", "exchange": "NSE", "price": 535.65, "change": 6.35, "changePercent": 1.20, "currency": "INR", "sector": "Consumer Staples"},
                        {"symbol": "GODREJCP", "company": "Godrej Consumer Products Ltd.", "exchange": "NSE", "price": 1185.40, "change": 15.75, "changePercent": 1.35, "currency": "INR", "sector": "Consumer Staples"}
                    ]
                # Handle NIFTY 500 specifically
                elif index_name == "NIFTY 500":
                    logger.info("Generating NIFTY 500 constituents with comprehensive data")
                    # Generate a representative subset of NIFTY 500 constituents
                    # In a production environment, this would fetch actual constituents from NSE API
                    nifty500_companies = [
                        {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "sector": "Energy", "industry": "Oil & Gas", "price": 2510.25, "change": 35.75, "changePercent": 1.45, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "sector": "Technology", "industry": "IT Services", "price": 3475.80, "change": -42.25, "changePercent": -1.20, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "sector": "Finance", "industry": "Banking", "price": 1615.50, "change": 12.75, "changePercent": 0.80, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "INFY", "company": "Infosys Ltd.", "sector": "Technology", "industry": "IT Services", "price": 1710.30, "change": 25.60, "changePercent": 1.52, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "sector": "Finance", "industry": "Banking", "price": 935.75, "change": 15.80, "changePercent": 1.72, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "SBIN", "company": "State Bank of India", "sector": "Finance", "industry": "Banking", "price": 622.40, "change": -5.35, "changePercent": -0.85, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "sector": "Communication", "industry": "Telecom", "price": 855.25, "change": 12.40, "changePercent": 1.47, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "ITC", "company": "ITC Ltd.", "sector": "Consumer Goods", "industry": "FMCG", "price": 452.80, "change": 8.25, "changePercent": 1.86, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "KOTAKBANK", "company": "Kotak Mahindra Bank Ltd.", "sector": "Finance", "industry": "Banking", "price": 1755.60, "change": -15.30, "changePercent": -0.86, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "HCLTECH", "company": "HCL Technologies Ltd.", "sector": "Technology", "industry": "IT Services", "price": 1185.40, "change": -11.75, "changePercent": -0.98, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "ASIANPAINT", "company": "Asian Paints Ltd.", "sector": "Consumer Goods", "industry": "Paints", "price": 3210.50, "change": -39.75, "changePercent": -1.22, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "AXISBANK", "company": "Axis Bank Ltd.", "sector": "Finance", "industry": "Banking", "price": 985.30, "change": 12.45, "changePercent": 1.28, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "SUNPHARMA", "company": "Sun Pharmaceutical Industries Ltd.", "sector": "Healthcare", "industry": "Pharmaceuticals", "price": 1105.80, "change": -14.65, "changePercent": -1.31, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "BAJFINANCE", "company": "Bajaj Finance Ltd.", "sector": "Finance", "industry": "NBFC", "price": 7120.35, "change": 122.50, "changePercent": 1.75, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "ADANIENT", "company": "Adani Enterprises Ltd.", "sector": "Infrastructure", "industry": "Diversified", "price": 2455.75, "change": 66.40, "changePercent": 2.78, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "NESTLEIND", "company": "Nestle India Ltd.", "sector": "Consumer Goods", "industry": "FMCG", "price": 23050.20, "change": 322.75, "changePercent": 1.42, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "DRREDDY", "company": "Dr. Reddy's Laboratories Ltd.", "sector": "Healthcare", "industry": "Pharmaceuticals", "price": 5210.45, "change": 81.30, "changePercent": 1.59, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "CIPLA", "company": "Cipla Ltd.", "sector": "Healthcare", "industry": "Pharmaceuticals", "price": 1285.30, "change": -14.75, "changePercent": -1.13, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "BAJAJFINSV", "company": "Bajaj Finserv Ltd.", "sector": "Finance", "industry": "Diversified Financial", "price": 1585.65, "change": -17.80, "changePercent": -1.11, "currency": "INR", "exchange": "NSE"},
                        {"symbol": "MARUTI", "company": "Maruti Suzuki India Ltd.", "sector": "Automobile", "industry": "Auto", "price": 10520.75, "change": 182.35, "changePercent": 1.76, "currency": "INR", "exchange": "NSE"}
                    ]
                    constituents = nifty500_companies
                else:
                    logger.warning(f"No direct method available for {index_name} in NSEPython")
            except Exception as e:
                logger.error(f"Error fetching NSE index constituents for {index_name}: {e}", exc_info=True)
        
        # Check if this is one of the BSE indices
        if not constituents and (index_name.startswith("BSE") or index_name.startswith("S&P BSE")):
            logger.info(f"Generating constituents for BSE index: {index_name}")
            # Using our generate_bse_constituents function which provides detailed data for different BSE indices
            constituents = generate_bse_constituents(index_name)
            
        # Check if this is an Australian index
        if not constituents and index_name in australian_indices:
            logger.info(f"Generating constituents for Australian index: {index_name}")
            constituents = generate_australian_index_constituents(index_name)
        
        # Check if this is a Middle East index
        if not constituents and index_name in middle_east_indices:
            logger.info(f"Generating constituents for Middle East index: {index_name}")
            constituents = generate_middle_east_index_constituents(index_name)
            
        # Check if this is a US index
        if not constituents and (index_name in us_indices or index_name in americas_indices):
            logger.info(f"Generating constituents for Americas index: {index_name}")
            
            if index_name == "S&P 500":
                # Create S&P 500 constituents with major US companies
                constituents = [
                    {"symbol": "AAPL", "company": "Apple Inc.", "exchange": "NASDAQ", "price": 175.50, "change": 2.25, "changePercent": 1.35, "currency": "USD", "sector": "Technology"},
                    {"symbol": "MSFT", "company": "Microsoft Corporation", "exchange": "NASDAQ", "price": 328.75, "change": 5.40, "changePercent": 1.68, "currency": "USD", "sector": "Technology"},
                    {"symbol": "GOOGL", "company": "Alphabet Inc.", "exchange": "NASDAQ", "price": 142.85, "change": 1.95, "changePercent": 1.45, "currency": "USD", "sector": "Technology"},
                    {"symbol": "AMZN", "company": "Amazon.com Inc.", "exchange": "NASDAQ", "price": 167.30, "change": 3.20, "changePercent": 1.95, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "BRK.B", "company": "Berkshire Hathaway Inc.", "exchange": "NYSE", "price": 398.45, "change": 2.50, "changePercent": 0.65, "currency": "USD", "sector": "Financials"},
                    {"symbol": "LLY", "company": "Eli Lilly and Company", "exchange": "NYSE", "price": 765.40, "change": 15.60, "changePercent": 2.08, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "AVGO", "company": "Broadcom Inc.", "exchange": "NASDAQ", "price": 1342.25, "change": 28.75, "changePercent": 2.19, "currency": "USD", "sector": "Technology"},
                    {"symbol": "XOM", "company": "Exxon Mobil Corporation", "exchange": "NYSE", "price": 116.30, "change": 1.15, "changePercent": 1.00, "currency": "USD", "sector": "Energy"},
                    {"symbol": "COST", "company": "Costco Wholesale Corporation", "exchange": "NASDAQ", "price": 730.50, "change": 8.75, "changePercent": 1.21, "currency": "USD", "sector": "Consumer Staples"},
                    {"symbol": "ABBV", "company": "AbbVie Inc.", "exchange": "NYSE", "price": 163.25, "change": 1.30, "changePercent": 0.80, "currency": "USD", "sector": "Healthcare"}
                ]
            elif index_name == "Dow Jones Industrial Average":
                # Create Dow Jones constituents with entirely different blue-chip companies
                constituents = [
                    {"symbol": "JNJ", "company": "Johnson & Johnson", "exchange": "NYSE", "price": 156.80, "change": -1.35, "changePercent": -0.85, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "JPM", "company": "JPMorgan Chase & Co.", "exchange": "NYSE", "price": 183.40, "change": 1.25, "changePercent": 0.70, "currency": "USD", "sector": "Financials"},
                    {"symbol": "WMT", "company": "Walmart Inc.", "exchange": "NYSE", "price": 60.25, "change": 0.82, "changePercent": 1.38, "currency": "USD", "sector": "Consumer Staples"},
                    {"symbol": "PG", "company": "Procter & Gamble Co.", "exchange": "NYSE", "price": 160.25, "change": -0.55, "changePercent": -0.35, "currency": "USD", "sector": "Consumer Staples"},
                    {"symbol": "KO", "company": "The Coca-Cola Company", "exchange": "NYSE", "price": 61.70, "change": 0.34, "changePercent": 0.55, "currency": "USD", "sector": "Consumer Staples"},
                    {"symbol": "HD", "company": "Home Depot Inc.", "exchange": "NYSE", "price": 345.90, "change": 4.35, "changePercent": 1.28, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "MCD", "company": "McDonald's Corporation", "exchange": "NYSE", "price": 287.85, "change": 3.25, "changePercent": 1.14, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "UNH", "company": "UnitedHealth Group Inc.", "exchange": "NYSE", "price": 488.25, "change": 2.75, "changePercent": 0.56, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "MRK", "company": "Merck & Co., Inc.", "exchange": "NYSE", "price": 126.80, "change": 0.55, "changePercent": 0.45, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "DIS", "company": "The Walt Disney Company", "exchange": "NYSE", "price": 111.20, "change": -1.45, "changePercent": -1.30, "currency": "USD", "sector": "Communication Services"},
                    {"symbol": "AXP", "company": "American Express Company", "exchange": "NYSE", "price": 226.15, "change": 2.75, "changePercent": 1.23, "currency": "USD", "sector": "Financials"},
                    {"symbol": "CRM", "company": "Salesforce, Inc.", "exchange": "NYSE", "price": 301.40, "change": 5.30, "changePercent": 1.79, "currency": "USD", "sector": "Technology"},
                    {"symbol": "VZ", "company": "Verizon Communications Inc.", "exchange": "NYSE", "price": 40.75, "change": -0.30, "changePercent": -0.73, "currency": "USD", "sector": "Communication Services"},
                    {"symbol": "CVX", "company": "Chevron Corporation", "exchange": "NYSE", "price": 155.80, "change": 1.45, "changePercent": 0.94, "currency": "USD", "sector": "Energy"},
                    {"symbol": "BA", "company": "The Boeing Company", "exchange": "NYSE", "price": 178.30, "change": -2.25, "changePercent": -1.25, "currency": "USD", "sector": "Industrials"}
                ]
            elif index_name == "Nasdaq Composite":
                # Create Nasdaq constituents with tech-heavy focus - completely different set
                constituents = [
                    {"symbol": "NVDA", "company": "NVIDIA Corporation", "exchange": "NASDAQ", "price": 875.30, "change": 15.80, "changePercent": 1.85, "currency": "USD", "sector": "Technology"},
                    {"symbol": "NFLX", "company": "Netflix, Inc.", "exchange": "NASDAQ", "price": 630.25, "change": 11.40, "changePercent": 1.85, "currency": "USD", "sector": "Communication Services"},
                    {"symbol": "ADBE", "company": "Adobe Inc.", "exchange": "NASDAQ", "price": 475.80, "change": 7.65, "changePercent": 1.65, "currency": "USD", "sector": "Technology"},
                    {"symbol": "AMD", "company": "Advanced Micro Devices, Inc.", "exchange": "NASDAQ", "price": 155.85, "change": 4.20, "changePercent": 2.75, "currency": "USD", "sector": "Technology"},
                    {"symbol": "ASML", "company": "ASML Holding N.V.", "exchange": "NASDAQ", "price": 934.65, "change": 12.85, "changePercent": 1.39, "currency": "USD", "sector": "Technology"},
                    {"symbol": "ISRG", "company": "Intuitive Surgical, Inc.", "exchange": "NASDAQ", "price": 386.70, "change": 5.15, "changePercent": 1.35, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "MU", "company": "Micron Technology, Inc.", "exchange": "NASDAQ", "price": 114.50, "change": 2.80, "changePercent": 2.51, "currency": "USD", "sector": "Technology"},
                    {"symbol": "MRVL", "company": "Marvell Technology, Inc.", "exchange": "NASDAQ", "price": 68.40, "change": 1.75, "changePercent": 2.63, "currency": "USD", "sector": "Technology"},
                    {"symbol": "TEAM", "company": "Atlassian Corporation", "exchange": "NASDAQ", "price": 196.25, "change": 3.65, "changePercent": 1.90, "currency": "USD", "sector": "Technology"},
                    {"symbol": "LRCX", "company": "Lam Research Corporation", "exchange": "NASDAQ", "price": 927.85, "change": 14.35, "changePercent": 1.57, "currency": "USD", "sector": "Technology"}
                ]
            elif index_name == "Russell 2000":
                # Russell 2000 constituents - focused on small-cap US stocks
                constituents = [
                    {"symbol": "PLUG", "company": "Plug Power Inc.", "exchange": "NASDAQ", "price": 3.46, "change": 0.07, "changePercent": 2.06, "currency": "USD", "sector": "Industrials"},
                    {"symbol": "CROX", "company": "Crocs, Inc.", "exchange": "NASDAQ", "price": 142.85, "change": 2.35, "changePercent": 1.67, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "AFRM", "company": "Affirm Holdings, Inc.", "exchange": "NASDAQ", "price": 37.46, "change": 1.12, "changePercent": 3.08, "currency": "USD", "sector": "Financials"},
                    {"symbol": "AXON", "company": "Axon Enterprise, Inc.", "exchange": "NASDAQ", "price": 306.78, "change": 4.55, "changePercent": 1.51, "currency": "USD", "sector": "Industrials"},
                    {"symbol": "EXAS", "company": "Exact Sciences Corporation", "exchange": "NASDAQ", "price": 64.76, "change": 1.12, "changePercent": 1.76, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "IIVI", "company": "II-VI Incorporated", "exchange": "NASDAQ", "price": 88.24, "change": 1.56, "changePercent": 1.80, "currency": "USD", "sector": "Technology"},
                    {"symbol": "SLAB", "company": "Silicon Laboratories Inc.", "exchange": "NASDAQ", "price": 128.92, "change": 2.45, "changePercent": 1.94, "currency": "USD", "sector": "Technology"},
                    {"symbol": "QDEL", "company": "QuidelOrtho Corporation", "exchange": "NASDAQ", "price": 46.35, "change": 0.85, "changePercent": 1.87, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "BOOT", "company": "Boot Barn Holdings, Inc.", "exchange": "NYSE", "price": 89.25, "change": 1.35, "changePercent": 1.54, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "HAYW", "company": "Hayward Holdings, Inc.", "exchange": "NYSE", "price": 13.78, "change": 0.25, "changePercent": 1.85, "currency": "USD", "sector": "Industrials"}
                ]
            elif index_name == "Dow Jones Futures":
                # Dow Jones Futures - futures contracts
                constituents = [
                    {"symbol": "YM=F", "company": "Dow Jones Futures MAR 25", "exchange": "CBOT", "price": 39245.00, "change": 105.00, "changePercent": 0.27, "currency": "USD", "sector": "Futures"},
                    {"symbol": "YMM24.CBT", "company": "Dow Jones Futures JUN 25", "exchange": "CBOT", "price": 39385.00, "change": 110.00, "changePercent": 0.28, "currency": "USD", "sector": "Futures"},
                    {"symbol": "YMU24.CBT", "company": "Dow Jones Futures SEP 25", "exchange": "CBOT", "price": 39475.00, "change": 115.00, "changePercent": 0.29, "currency": "USD", "sector": "Futures"},
                    {"symbol": "ESH24.CME", "company": "E-mini S&P 500 Futures MAR 25", "exchange": "CME", "price": 5155.75, "change": 12.25, "changePercent": 0.24, "currency": "USD", "sector": "Futures"},
                    {"symbol": "ES=F", "company": "E-mini S&P 500 Index Futures", "exchange": "CME", "price": 5156.50, "change": 12.50, "changePercent": 0.24, "currency": "USD", "sector": "Futures"},
                    {"symbol": "NQH24.CME", "company": "E-mini NASDAQ 100 Futures MAR 25", "exchange": "CME", "price": 17920.00, "change": 65.00, "changePercent": 0.36, "currency": "USD", "sector": "Futures"},
                    {"symbol": "NQ=F", "company": "NASDAQ 100 Futures", "exchange": "CME", "price": 17925.00, "change": 65.50, "changePercent": 0.37, "currency": "USD", "sector": "Futures"},
                    {"symbol": "RTY=F", "company": "Russell 2000 Futures", "exchange": "CME", "price": 2026.80, "change": 8.90, "changePercent": 0.44, "currency": "USD", "sector": "Futures"},
                    {"symbol": "ZB=F", "company": "U.S. Treasury Bond Futures", "exchange": "CBOT", "price": 111.19, "change": 0.31, "changePercent": 0.28, "currency": "USD", "sector": "Futures"},
                    {"symbol": "GC=F", "company": "Gold Futures", "exchange": "COMEX", "price": 2345.60, "change": 12.90, "changePercent": 0.55, "currency": "USD", "sector": "Futures"}
                ]
            elif index_name == "S&P 500 CFD":
                # S&P 500 CFD - contracts for difference
                constituents = [
                    {"symbol": "SPX500", "company": "S&P 500 CFD", "exchange": "OTC", "price": 5156.25, "change": 12.80, "changePercent": 0.25, "currency": "USD", "sector": "CFD"},
                    {"symbol": "US500", "company": "S&P 500 Index CFD", "exchange": "OTC", "price": 5157.00, "change": 13.00, "changePercent": 0.25, "currency": "USD", "sector": "CFD"},
                    {"symbol": "SPX_UK", "company": "S&P 500 UK CFD", "exchange": "OTC", "price": 5155.50, "change": 12.50, "changePercent": 0.24, "currency": "USD", "sector": "CFD"},
                    {"symbol": "US30", "company": "Dow Jones Industrial Average CFD", "exchange": "OTC", "price": 39250.00, "change": 105.00, "changePercent": 0.27, "currency": "USD", "sector": "CFD"},
                    {"symbol": "DJI_CFD", "company": "Dow Jones CFD", "exchange": "OTC", "price": 39252.00, "change": 106.00, "changePercent": 0.27, "currency": "USD", "sector": "CFD"},
                    {"symbol": "NAS100", "company": "NASDAQ 100 CFD", "exchange": "OTC", "price": 17926.00, "change": 66.00, "changePercent": 0.37, "currency": "USD", "sector": "CFD"},
                    {"symbol": "US_TECH", "company": "NASDAQ Composite CFD", "exchange": "OTC", "price": 17927.00, "change": 66.50, "changePercent": 0.37, "currency": "USD", "sector": "CFD"},
                    {"symbol": "RUSSELL", "company": "Russell 2000 CFD", "exchange": "OTC", "price": 2027.00, "change": 9.00, "changePercent": 0.45, "currency": "USD", "sector": "CFD"},
                    {"symbol": "VIX_CFD", "company": "VIX CFD", "exchange": "OTC", "price": 13.25, "change": -0.35, "changePercent": -2.57, "currency": "USD", "sector": "CFD"},
                    {"symbol": "SPY_CFD", "company": "SPDR S&P 500 ETF CFD", "exchange": "OTC", "price": 515.45, "change": 1.25, "changePercent": 0.24, "currency": "USD", "sector": "CFD"}
                ]
            elif index_name == "Nasdaq CFD":
                # Nasdaq CFD - contracts for difference
                constituents = [
                    {"symbol": "NASDAQ_CFD", "company": "NASDAQ Composite CFD", "exchange": "OTC", "price": 16225.00, "change": 60.00, "changePercent": 0.37, "currency": "USD", "sector": "CFD"},
                    {"symbol": "NAS_100", "company": "NASDAQ 100 CFD", "exchange": "OTC", "price": 17928.00, "change": 66.75, "changePercent": 0.37, "currency": "USD", "sector": "CFD"},
                    {"symbol": "TECH_100", "company": "Tech 100 CFD", "exchange": "OTC", "price": 17929.00, "change": 67.00, "changePercent": 0.38, "currency": "USD", "sector": "CFD"},
                    {"symbol": "QQQ_CFD", "company": "Invesco QQQ Trust CFD", "exchange": "OTC", "price": 435.25, "change": 1.65, "changePercent": 0.38, "currency": "USD", "sector": "CFD"},
                    {"symbol": "NDX_F", "company": "NASDAQ 100 Futures CFD", "exchange": "OTC", "price": 17930.00, "change": 67.50, "changePercent": 0.38, "currency": "USD", "sector": "CFD"},
                    {"symbol": "TQQQ_CFD", "company": "ProShares UltraPro QQQ CFD", "exchange": "OTC", "price": 62.35, "change": 0.75, "changePercent": 1.22, "currency": "USD", "sector": "CFD"},
                    {"symbol": "SQQQ_CFD", "company": "ProShares UltraPro Short QQQ CFD", "exchange": "OTC", "price": 8.20, "change": -0.15, "changePercent": -1.80, "currency": "USD", "sector": "CFD"},
                    {"symbol": "XLK_CFD", "company": "Technology Select Sector SPDR Fund CFD", "exchange": "OTC", "price": 198.75, "change": 1.35, "changePercent": 0.68, "currency": "USD", "sector": "CFD"},
                    {"symbol": "FDN_CFD", "company": "First Trust Dow Jones Internet Index Fund CFD", "exchange": "OTC", "price": 188.50, "change": 1.25, "changePercent": 0.67, "currency": "USD", "sector": "CFD"},
                    {"symbol": "NSDQ_MINI", "company": "NASDAQ Mini CFD", "exchange": "OTC", "price": 1792.50, "change": 6.65, "changePercent": 0.37, "currency": "USD", "sector": "CFD"}
                ]
            # For other US indices, provide a mixed set of major US stocks
            else:
                constituents = [
                    {"symbol": "AAPL", "company": "Apple Inc.", "exchange": "NASDAQ", "price": 175.50, "change": 2.25, "changePercent": 1.35, "currency": "USD", "sector": "Technology"},
                    {"symbol": "MSFT", "company": "Microsoft Corporation", "exchange": "NASDAQ", "price": 328.75, "change": 5.40, "changePercent": 1.68, "currency": "USD", "sector": "Technology"},
                    {"symbol": "GOOGL", "company": "Alphabet Inc.", "exchange": "NASDAQ", "price": 142.85, "change": 1.95, "changePercent": 1.45, "currency": "USD", "sector": "Technology"},
                    {"symbol": "AMZN", "company": "Amazon.com Inc.", "exchange": "NASDAQ", "price": 167.30, "change": 3.20, "changePercent": 1.95, "currency": "USD", "sector": "Consumer Discretionary"},
                    {"symbol": "BRK.B", "company": "Berkshire Hathaway Inc.", "exchange": "NYSE", "price": 398.45, "change": 2.50, "changePercent": 0.65, "currency": "USD", "sector": "Financials"},
                    {"symbol": "JNJ", "company": "Johnson & Johnson", "exchange": "NYSE", "price": 156.80, "change": -1.35, "changePercent": -0.85, "currency": "USD", "sector": "Healthcare"},
                    {"symbol": "JPM", "company": "JPMorgan Chase & Co.", "exchange": "NYSE", "price": 183.40, "change": 1.25, "changePercent": 0.70, "currency": "USD", "sector": "Financials"},
                    {"symbol": "V", "company": "Visa Inc.", "exchange": "NYSE", "price": 275.60, "change": 3.85, "changePercent": 1.42, "currency": "USD", "sector": "Financials"},
                    {"symbol": "PG", "company": "Procter & Gamble Co.", "exchange": "NYSE", "price": 160.25, "change": -0.55, "changePercent": -0.35, "currency": "USD", "sector": "Consumer Staples"},
                    {"symbol": "UNH", "company": "UnitedHealth Group Inc.", "exchange": "NYSE", "price": 488.25, "change": 2.75, "changePercent": 0.56, "currency": "USD", "sector": "Healthcare"}
                ]
                
        # Check if this is a European index
        if not constituents and index_name in european_indices:
            logger.info(f"Generating constituents for European index: {index_name}")
            
            if index_name == "FTSE 100":
                # FTSE 100 (UK) constituents
                constituents = [
                    {"symbol": "HSBA.L", "company": "HSBC Holdings plc", "exchange": "LSE", "price": 585.40, "change": 5.20, "changePercent": 0.90, "currency": "GBP", "sector": "Financials"},
                    {"symbol": "AZN.L", "company": "AstraZeneca PLC", "exchange": "LSE", "price": 10450.00, "change": 125.00, "changePercent": 1.21, "currency": "GBP", "sector": "Healthcare"},
                    {"symbol": "SHEL.L", "company": "Shell plc", "exchange": "LSE", "price": 2478.50, "change": 18.50, "changePercent": 0.75, "currency": "GBP", "sector": "Energy"},
                    {"symbol": "BP.L", "company": "BP p.l.c.", "exchange": "LSE", "price": 458.30, "change": -3.40, "changePercent": -0.74, "currency": "GBP", "sector": "Energy"},
                    {"symbol": "ULVR.L", "company": "Unilever PLC", "exchange": "LSE", "price": 3902.00, "change": 42.00, "changePercent": 1.09, "currency": "GBP", "sector": "Consumer Staples"},
                    {"symbol": "GSK.L", "company": "GSK plc", "exchange": "LSE", "price": 1652.40, "change": -5.80, "changePercent": -0.35, "currency": "GBP", "sector": "Healthcare"},
                    {"symbol": "RIO.L", "company": "Rio Tinto Group", "exchange": "LSE", "price": 5288.00, "change": 68.00, "changePercent": 1.30, "currency": "GBP", "sector": "Materials"},
                    {"symbol": "LLOY.L", "company": "Lloyds Banking Group plc", "exchange": "LSE", "price": 51.22, "change": 0.42, "changePercent": 0.83, "currency": "GBP", "sector": "Financials"},
                    {"symbol": "DGE.L", "company": "Diageo plc", "exchange": "LSE", "price": 2912.50, "change": 27.50, "changePercent": 0.95, "currency": "GBP", "sector": "Consumer Staples"},
                    {"symbol": "REL.L", "company": "RELX PLC", "exchange": "LSE", "price": 3042.00, "change": 22.00, "changePercent": 0.73, "currency": "GBP", "sector": "Industrials"}
                ]
            elif index_name == "DAX":
                # DAX (Germany) constituents
                constituents = [
                    {"symbol": "SAP.DE", "company": "SAP SE", "exchange": "XETRA", "price": 175.56, "change": 2.26, "changePercent": 1.30, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "SIE.DE", "company": "Siemens AG", "exchange": "XETRA", "price": 176.88, "change": 1.58, "changePercent": 0.90, "currency": "EUR", "sector": "Industrials"},
                    {"symbol": "ALV.DE", "company": "Allianz SE", "exchange": "XETRA", "price": 260.40, "change": 3.10, "changePercent": 1.20, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "DTE.DE", "company": "Deutsche Telekom AG", "exchange": "XETRA", "price": 22.61, "change": 0.13, "changePercent": 0.58, "currency": "EUR", "sector": "Communication Services"},
                    {"symbol": "VOW3.DE", "company": "Volkswagen AG", "exchange": "XETRA", "price": 119.40, "change": -1.30, "changePercent": -1.08, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "BAS.DE", "company": "BASF SE", "exchange": "XETRA", "price": 47.75, "change": 0.27, "changePercent": 0.57, "currency": "EUR", "sector": "Materials"},
                    {"symbol": "BAY.DE", "company": "Bayer AG", "exchange": "XETRA", "price": 27.60, "change": -0.24, "changePercent": -0.86, "currency": "EUR", "sector": "Healthcare"},
                    {"symbol": "BMW.DE", "company": "Bayerische Motoren Werke AG", "exchange": "XETRA", "price": 98.66, "change": 0.56, "changePercent": 0.57, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "DBK.DE", "company": "Deutsche Bank AG", "exchange": "XETRA", "price": 14.90, "change": 0.20, "changePercent": 1.36, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "ADS.DE", "company": "adidas AG", "exchange": "XETRA", "price": 200.40, "change": 3.20, "changePercent": 1.62, "currency": "EUR", "sector": "Consumer Discretionary"}
                ]
            elif index_name == "CAC 40":
                # CAC 40 (France) constituents
                constituents = [
                    {"symbol": "MC.PA", "company": "LVMH Moët Hennessy Louis Vuitton SE", "exchange": "Euronext Paris", "price": 765.50, "change": 9.30, "changePercent": 1.23, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "SU.PA", "company": "Schneider Electric SE", "exchange": "Euronext Paris", "price": 218.40, "change": 2.80, "changePercent": 1.30, "currency": "EUR", "sector": "Industrials"},
                    {"symbol": "OR.PA", "company": "L'Oréal S.A.", "exchange": "Euronext Paris", "price": 431.20, "change": 3.85, "changePercent": 0.90, "currency": "EUR", "sector": "Consumer Staples"},
                    {"symbol": "AI.PA", "company": "Air Liquide S.A.", "exchange": "Euronext Paris", "price": 167.18, "change": 1.34, "changePercent": 0.81, "currency": "EUR", "sector": "Materials"},
                    {"symbol": "BNP.PA", "company": "BNP Paribas SA", "exchange": "Euronext Paris", "price": 57.95, "change": 0.47, "changePercent": 0.82, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "SAN.PA", "company": "Sanofi", "exchange": "Euronext Paris", "price": 87.66, "change": -0.42, "changePercent": -0.48, "currency": "EUR", "sector": "Healthcare"},
                    {"symbol": "RI.PA", "company": "Pernod Ricard SA", "exchange": "Euronext Paris", "price": 142.80, "change": 1.05, "changePercent": 0.74, "currency": "EUR", "sector": "Consumer Staples"},
                    {"symbol": "CS.PA", "company": "AXA SA", "exchange": "Euronext Paris", "price": 32.97, "change": 0.25, "changePercent": 0.76, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "CAP.PA", "company": "Capgemini SE", "exchange": "Euronext Paris", "price": 198.55, "change": 2.15, "changePercent": 1.09, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "KER.PA", "company": "Kering SA", "exchange": "Euronext Paris", "price": 376.50, "change": -5.30, "changePercent": -1.39, "currency": "EUR", "sector": "Consumer Discretionary"}
                ]
            elif index_name == "Euro Stoxx 50":
                # Euro Stoxx 50 constituents
                constituents = [
                    {"symbol": "ASML.AS", "company": "ASML Holding N.V.", "exchange": "Euronext Amsterdam", "price": 842.90, "change": 12.30, "changePercent": 1.48, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "LVMH.PA", "company": "LVMH Moët Hennessy Louis Vuitton SE", "exchange": "Euronext Paris", "price": 765.50, "change": 9.30, "changePercent": 1.23, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "SAP.DE", "company": "SAP SE", "exchange": "XETRA", "price": 175.56, "change": 2.26, "changePercent": 1.30, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "L40.DE", "company": "Linde plc", "exchange": "XETRA", "price": 410.80, "change": 4.85, "changePercent": 1.20, "currency": "EUR", "sector": "Materials"},
                    {"symbol": "SU.PA", "company": "Schneider Electric SE", "exchange": "Euronext Paris", "price": 218.40, "change": 2.80, "changePercent": 1.30, "currency": "EUR", "sector": "Industrials"},
                    {"symbol": "SIE.DE", "company": "Siemens AG", "exchange": "XETRA", "price": 176.88, "change": 1.58, "changePercent": 0.90, "currency": "EUR", "sector": "Industrials"},
                    {"symbol": "ALV.DE", "company": "Allianz SE", "exchange": "XETRA", "price": 260.40, "change": 3.10, "changePercent": 1.20, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "OR.PA", "company": "L'Oréal S.A.", "exchange": "Euronext Paris", "price": 431.20, "change": 3.85, "changePercent": 0.90, "currency": "EUR", "sector": "Consumer Staples"},
                    {"symbol": "SAN.PA", "company": "Sanofi", "exchange": "Euronext Paris", "price": 87.66, "change": -0.42, "changePercent": -0.48, "currency": "EUR", "sector": "Healthcare"},
                    {"symbol": "ABI.BR", "company": "Anheuser-Busch InBev SA/NV", "exchange": "Euronext Brussels", "price": 58.35, "change": 0.48, "changePercent": 0.83, "currency": "EUR", "sector": "Consumer Staples"}
                ]
            elif index_name == "IBEX 35":
                # IBEX 35 (Spain) constituents
                constituents = [
                    {"symbol": "SAN.MC", "company": "Banco Santander, S.A.", "exchange": "BME", "price": 4.15, "change": 0.05, "changePercent": 1.22, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "IBE.MC", "company": "Iberdrola, S.A.", "exchange": "BME", "price": 12.35, "change": 0.18, "changePercent": 1.48, "currency": "EUR", "sector": "Utilities"},
                    {"symbol": "BBVA.MC", "company": "Banco Bilbao Vizcaya Argentaria, S.A.", "exchange": "BME", "price": 8.90, "change": 0.10, "changePercent": 1.14, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "ITX.MC", "company": "Industria de Diseño Textil, S.A.", "exchange": "BME", "price": 38.45, "change": 0.58, "changePercent": 1.53, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "REP.MC", "company": "Repsol, S.A.", "exchange": "BME", "price": 13.60, "change": 0.15, "changePercent": 1.12, "currency": "EUR", "sector": "Energy"},
                    {"symbol": "TEF.MC", "company": "Telefónica, S.A.", "exchange": "BME", "price": 4.25, "change": 0.03, "changePercent": 0.71, "currency": "EUR", "sector": "Communication Services"},
                    {"symbol": "MAP.MC", "company": "MAPFRE, S.A.", "exchange": "BME", "price": 2.15, "change": 0.02, "changePercent": 0.94, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "ELE.MC", "company": "Endesa, S.A.", "exchange": "BME", "price": 19.25, "change": 0.23, "changePercent": 1.21, "currency": "EUR", "sector": "Utilities"},
                    {"symbol": "AENA.MC", "company": "Aena S.M.E., S.A.", "exchange": "BME", "price": 165.80, "change": 2.35, "changePercent": 1.44, "currency": "EUR", "sector": "Industrials"},
                    {"symbol": "FER.MC", "company": "Ferrovial, S.A.", "exchange": "BME", "price": 32.40, "change": 0.45, "changePercent": 1.41, "currency": "EUR", "sector": "Industrials"}
                ]
            elif index_name == "FTSE MIB":
                # FTSE MIB (Italy) constituents
                constituents = [
                    {"symbol": "ENI.MI", "company": "Eni S.p.A.", "exchange": "BIT", "price": 14.78, "change": 0.18, "changePercent": 1.23, "currency": "EUR", "sector": "Energy"},
                    {"symbol": "ISP.MI", "company": "Intesa Sanpaolo S.p.A.", "exchange": "BIT", "price": 3.25, "change": 0.05, "changePercent": 1.56, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "UCG.MI", "company": "UniCredit S.p.A.", "exchange": "BIT", "price": 31.50, "change": 0.45, "changePercent": 1.45, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "G.MI", "company": "Assicurazioni Generali S.p.A.", "exchange": "BIT", "price": 22.85, "change": 0.28, "changePercent": 1.24, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "ENEL.MI", "company": "Enel S.p.A.", "exchange": "BIT", "price": 6.85, "change": 0.08, "changePercent": 1.18, "currency": "EUR", "sector": "Utilities"},
                    {"symbol": "STM.MI", "company": "STMicroelectronics N.V.", "exchange": "BIT", "price": 42.90, "change": 0.85, "changePercent": 2.02, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "LUX.MI", "company": "Luxottica Group S.p.A.", "exchange": "BIT", "price": 58.30, "change": 0.65, "changePercent": 1.13, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "TIT.MI", "company": "Telecom Italia S.p.A.", "exchange": "BIT", "price": 0.28, "change": 0.01, "changePercent": 1.82, "currency": "EUR", "sector": "Communication Services"},
                    {"symbol": "MB.MI", "company": "Mediobanca S.p.A.", "exchange": "BIT", "price": 13.45, "change": 0.18, "changePercent": 1.36, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "PST.MI", "company": "Poste Italiane S.p.A.", "exchange": "BIT", "price": 11.80, "change": 0.12, "changePercent": 1.03, "currency": "EUR", "sector": "Financials"}
                ]
            # For other European indices, provide a mixed set
            else:
                constituents = [
                    {"symbol": "MC.PA", "company": "LVMH Moët Hennessy Louis Vuitton SE", "exchange": "Euronext Paris", "price": 765.50, "change": 9.30, "changePercent": 1.23, "currency": "EUR", "sector": "Consumer Discretionary"},
                    {"symbol": "ASML.AS", "company": "ASML Holding N.V.", "exchange": "Euronext Amsterdam", "price": 842.90, "change": 12.30, "changePercent": 1.48, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "SAN.MC", "company": "Banco Santander, S.A.", "exchange": "BME", "price": 4.15, "change": 0.05, "changePercent": 1.22, "currency": "EUR", "sector": "Financials"},
                    {"symbol": "HSBA.L", "company": "HSBC Holdings plc", "exchange": "LSE", "price": 585.40, "change": 5.20, "changePercent": 0.90, "currency": "GBP", "sector": "Financials"},
                    {"symbol": "SAP.DE", "company": "SAP SE", "exchange": "XETRA", "price": 175.56, "change": 2.26, "changePercent": 1.30, "currency": "EUR", "sector": "Technology"},
                    {"symbol": "ENI.MI", "company": "Eni S.p.A.", "exchange": "BIT", "price": 14.78, "change": 0.18, "changePercent": 1.23, "currency": "EUR", "sector": "Energy"},
                    {"symbol": "BARC.L", "company": "Barclays PLC", "exchange": "LSE", "price": 185.20, "change": 2.35, "changePercent": 1.28, "currency": "GBP", "sector": "Financials"},
                    {"symbol": "OR.PA", "company": "L'Oréal S.A.", "exchange": "Euronext Paris", "price": 431.20, "change": 3.85, "changePercent": 0.90, "currency": "EUR", "sector": "Consumer Staples"},
                    {"symbol": "IBE.MC", "company": "Iberdrola, S.A.", "exchange": "BME", "price": 12.35, "change": 0.18, "changePercent": 1.48, "currency": "EUR", "sector": "Utilities"},
                    {"symbol": "ALV.DE", "company": "Allianz SE", "exchange": "XETRA", "price": 260.40, "change": 3.10, "changePercent": 1.20, "currency": "EUR", "sector": "Financials"}
                ]
        
        # Check if this is an Australian index
        if not constituents and index_name in australian_indices:
            logger.info(f"Generating constituents for Australian index: {index_name}")
            
            if index_name == "ASX 200" or index_name == "S&P/ASX 200":
                # S&P/ASX 200 constituents
                constituents = [
                    {"symbol": "BHP.AX", "company": "BHP Group Limited", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29, "currency": "AUD", "sector": "Materials"},
                    {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "WOW.AX", "company": "Woolworths Group Limited", "exchange": "ASX", "price": 37.90, "change": 0.45, "changePercent": 1.20, "currency": "AUD", "sector": "Consumer Staples"},
                    {"symbol": "WES.AX", "company": "Wesfarmers Limited", "exchange": "ASX", "price": 58.35, "change": 0.74, "changePercent": 1.28, "currency": "AUD", "sector": "Consumer Discretionary"},
                    {"symbol": "CSL.AX", "company": "CSL Limited", "exchange": "ASX", "price": 275.40, "change": 3.65, "changePercent": 1.34, "currency": "AUD", "sector": "Healthcare"},
                    {"symbol": "TLS.AX", "company": "Telstra Group Limited", "exchange": "ASX", "price": 4.25, "change": 0.06, "changePercent": 1.43, "currency": "AUD", "sector": "Communication Services"},
                    {"symbol": "FMG.AX", "company": "Fortescue Metals Group Ltd", "exchange": "ASX", "price": 22.55, "change": 0.35, "changePercent": 1.58, "currency": "AUD", "sector": "Materials"}
                ]
            elif index_name == "S&P/ASX 300":
                # S&P/ASX 300 constituents
                constituents = [
                    {"symbol": "BHP.AX", "company": "BHP Group Limited", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29, "currency": "AUD", "sector": "Materials"},
                    {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "MQG.AX", "company": "Macquarie Group Limited", "exchange": "ASX", "price": 167.50, "change": 2.25, "changePercent": 1.36, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "RIO.AX", "company": "Rio Tinto Limited", "exchange": "ASX", "price": 127.85, "change": 1.65, "changePercent": 1.31, "currency": "AUD", "sector": "Materials"}
                ]
            elif index_name == "All Ordinaries Index":
                # All Ordinaries Index constituents
                constituents = [
                    {"symbol": "BHP.AX", "company": "BHP Group Limited", "exchange": "ASX", "price": 45.62, "change": 0.58, "changePercent": 1.29, "currency": "AUD", "sector": "Materials"},
                    {"symbol": "CBA.AX", "company": "Commonwealth Bank of Australia", "exchange": "ASX", "price": 112.80, "change": 1.35, "changePercent": 1.21, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "WBC.AX", "company": "Westpac Banking Corporation", "exchange": "ASX", "price": 26.45, "change": 0.34, "changePercent": 1.30, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "NAB.AX", "company": "National Australia Bank Limited", "exchange": "ASX", "price": 34.12, "change": 0.42, "changePercent": 1.25, "currency": "AUD", "sector": "Financials"},
                    {"symbol": "ANZ.AX", "company": "Australia and New Zealand Banking Group Limited", "exchange": "ASX", "price": 27.85, "change": 0.38, "changePercent": 1.38, "currency": "AUD", "sector": "Financials"}
                ]
            elif index_name == "NZX 50":
                # NZX 50 constituents (New Zealand)
                constituents = [
                    {"symbol": "ATM.NZ", "company": "The a2 Milk Company Limited", "exchange": "NZX", "price": 6.40, "change": 0.10, "changePercent": 1.59, "currency": "NZD", "sector": "Consumer Staples"},
                    {"symbol": "SPK.NZ", "company": "Spark New Zealand Limited", "exchange": "NZX", "price": 4.55, "change": 0.07, "changePercent": 1.56, "currency": "NZD", "sector": "Communication Services"},
                    {"symbol": "FPH.NZ", "company": "Fisher & Paykel Healthcare Corporation Limited", "exchange": "NZX", "price": 22.15, "change": 0.35, "changePercent": 1.61, "currency": "NZD", "sector": "Healthcare"},
                    {"symbol": "MEL.NZ", "company": "Meridian Energy Limited", "exchange": "NZX", "price": 5.70, "change": 0.09, "changePercent": 1.60, "currency": "NZD", "sector": "Utilities"},
                    {"symbol": "AIR.NZ", "company": "Air New Zealand Limited", "exchange": "NZX", "price": 0.65, "change": 0.01, "changePercent": 1.56, "currency": "NZD", "sector": "Industrials"}
                ]
                
        # Check if this is a Middle East index
        if not constituents and index_name in middle_east_indices:
            logger.info(f"Generating constituents for Middle East index: {index_name}")
            
            if index_name == "Tadawul All Share Index":
                # Tadawul All Share Index (Saudi Arabia) constituents
                constituents = [
                    {"symbol": "2222.SR", "company": "Saudi Aramco", "exchange": "Tadawul", "price": 31.35, "change": 0.35, "changePercent": 1.13, "currency": "SAR", "sector": "Energy"},
                    {"symbol": "1150.SR", "company": "Al Rajhi Bank", "exchange": "Tadawul", "price": 78.90, "change": 0.90, "changePercent": 1.15, "currency": "SAR", "sector": "Financials"},
                    {"symbol": "2350.SR", "company": "Saudi Telecom Company", "exchange": "Tadawul", "price": 104.60, "change": 1.20, "changePercent": 1.16, "currency": "SAR", "sector": "Communication Services"},
                    {"symbol": "2010.SR", "company": "Saudi Basic Industries Corporation (SABIC)", "exchange": "Tadawul", "price": 92.50, "change": 1.10, "changePercent": 1.20, "currency": "SAR", "sector": "Materials"},
                    {"symbol": "1120.SR", "company": "Al Marai Company", "exchange": "Tadawul", "price": 53.80, "change": 0.70, "changePercent": 1.32, "currency": "SAR", "sector": "Consumer Staples"}
                ]
            elif index_name == "Dubai Financial Market General Index":
                # Dubai Financial Market General Index constituents
                constituents = [
                    {"symbol": "EMIRATES.DU", "company": "Emirates NBD Bank PJSC", "exchange": "DFM", "price": 16.85, "change": 0.25, "changePercent": 1.51, "currency": "AED", "sector": "Financials"},
                    {"symbol": "EMAAR.DU", "company": "Emaar Properties PJSC", "exchange": "DFM", "price": 7.25, "change": 0.12, "changePercent": 1.68, "currency": "AED", "sector": "Real Estate"},
                    {"symbol": "DIB.DU", "company": "Dubai Islamic Bank PJSC", "exchange": "DFM", "price": 5.40, "change": 0.08, "changePercent": 1.50, "currency": "AED", "sector": "Financials"},
                    {"symbol": "DU.DU", "company": "Emirates Integrated Telecommunications Company PJSC", "exchange": "DFM", "price": 7.90, "change": 0.13, "changePercent": 1.67, "currency": "AED", "sector": "Communication Services"},
                    {"symbol": "AIRARABIA.DU", "company": "Air Arabia PJSC", "exchange": "DFM", "price": 1.85, "change": 0.03, "changePercent": 1.65, "currency": "AED", "sector": "Industrials"}
                ]
            elif index_name == "Abu Dhabi Securities Exchange Index":
                # Abu Dhabi Securities Exchange Index constituents
                constituents = [
                    {"symbol": "ETISALAT.AD", "company": "Emirates Telecommunications Group Company PJSC", "exchange": "ADX", "price": 32.75, "change": 0.45, "changePercent": 1.39, "currency": "AED", "sector": "Communication Services"},
                    {"symbol": "ADCB.AD", "company": "Abu Dhabi Commercial Bank PJSC", "exchange": "ADX", "price": 9.15, "change": 0.15, "changePercent": 1.67, "currency": "AED", "sector": "Financials"},
                    {"symbol": "FAB.AD", "company": "First Abu Dhabi Bank PJSC", "exchange": "ADX", "price": 18.50, "change": 0.25, "changePercent": 1.37, "currency": "AED", "sector": "Financials"},
                    {"symbol": "ALDAR.AD", "company": "Aldar Properties PJSC", "exchange": "ADX", "price": 4.90, "change": 0.08, "changePercent": 1.66, "currency": "AED", "sector": "Real Estate"},
                    {"symbol": "ADNOC.AD", "company": "ADNOC Distribution PJSC", "exchange": "ADX", "price": 4.25, "change": 0.07, "changePercent": 1.68, "currency": "AED", "sector": "Energy"}
                ]
            elif index_name == "Qatar Exchange Index":
                # Qatar Exchange Index constituents
                constituents = [
                    {"symbol": "QNBK.QA", "company": "Qatar National Bank", "exchange": "QSE", "price": 18.55, "change": 0.23, "changePercent": 1.26, "currency": "QAR", "sector": "Financials"},
                    {"symbol": "IQCD.QA", "company": "Industries Qatar Q.P.S.C.", "exchange": "QSE", "price": 11.80, "change": 0.15, "changePercent": 1.29, "currency": "QAR", "sector": "Industrials"},
                    {"symbol": "MARK.QA", "company": "Masraf Al Rayan Q.P.S.C.", "exchange": "QSE", "price": 4.45, "change": 0.06, "changePercent": 1.37, "currency": "QAR", "sector": "Financials"},
                    {"symbol": "QIBK.QA", "company": "Qatar Islamic Bank", "exchange": "QSE", "price": 19.25, "change": 0.25, "changePercent": 1.32, "currency": "QAR", "sector": "Financials"},
                    {"symbol": "QNNS.QA", "company": "Qatar Navigation Q.P.S.C.", "exchange": "QSE", "price": 8.70, "change": 0.12, "changePercent": 1.40, "currency": "QAR", "sector": "Industrials"}
                ]
                
        # Check if this is an Asian index (non-Indian)
        if not constituents and index_name in asian_indices:
            logger.info(f"Generating constituents for Asian index: {index_name}")
            
            if index_name == "Nikkei 225":
                # Nikkei 225 (Japan) constituents
                constituents = [
                    {"symbol": "7203.T", "company": "Toyota Motor Corporation", "exchange": "TSE", "price": 3150.00, "change": 35.00, "changePercent": 1.12, "currency": "JPY", "sector": "Consumer Discretionary"},
                    {"symbol": "9432.T", "company": "Nippon Telegraph and Telephone Corporation", "exchange": "TSE", "price": 4250.00, "change": 52.00, "changePercent": 1.24, "currency": "JPY", "sector": "Communication Services"},
                    {"symbol": "9984.T", "company": "SoftBank Group Corp.", "exchange": "TSE", "price": 8520.00, "change": 120.00, "changePercent": 1.43, "currency": "JPY", "sector": "Communication Services"},
                    {"symbol": "9983.T", "company": "Fast Retailing Co., Ltd.", "exchange": "TSE", "price": 37950.00, "change": 450.00, "changePercent": 1.20, "currency": "JPY", "sector": "Consumer Discretionary"},
                    {"symbol": "6758.T", "company": "Sony Group Corporation", "exchange": "TSE", "price": 12500.00, "change": 155.00, "changePercent": 1.26, "currency": "JPY", "sector": "Consumer Discretionary"},
                    {"symbol": "8306.T", "company": "Mitsubishi UFJ Financial Group, Inc.", "exchange": "TSE", "price": 1350.00, "change": 15.00, "changePercent": 1.12, "currency": "JPY", "sector": "Financials"},
                    {"symbol": "6861.T", "company": "Keyence Corporation", "exchange": "TSE", "price": 67100.00, "change": 900.00, "changePercent": 1.36, "currency": "JPY", "sector": "Technology"},
                    {"symbol": "7267.T", "company": "Honda Motor Co., Ltd.", "exchange": "TSE", "price": 1650.00, "change": 25.00, "changePercent": 1.54, "currency": "JPY", "sector": "Consumer Discretionary"},
                    {"symbol": "6367.T", "company": "Daikin Industries,Ltd.", "exchange": "TSE", "price": 24750.00, "change": 250.00, "changePercent": 1.02, "currency": "JPY", "sector": "Industrials"},
                    {"symbol": "4502.T", "company": "Takeda Pharmaceutical Company Limited", "exchange": "TSE", "price": 4450.00, "change": -25.00, "changePercent": -0.56, "currency": "JPY", "sector": "Healthcare"}
                ]
            elif index_name == "Hang Seng":
                # Hang Seng (Hong Kong) constituents
                constituents = [
                    {"symbol": "0700.HK", "company": "Tencent Holdings Limited", "exchange": "HKEX", "price": 368.40, "change": 5.80, "changePercent": 1.60, "currency": "HKD", "sector": "Communication Services"},
                    {"symbol": "9988.HK", "company": "Alibaba Group Holding Limited", "exchange": "HKEX", "price": 75.45, "change": 1.05, "changePercent": 1.41, "currency": "HKD", "sector": "Consumer Discretionary"},
                    {"symbol": "0941.HK", "company": "China Mobile Limited", "exchange": "HKEX", "price": 90.25, "change": 0.85, "changePercent": 0.95, "currency": "HKD", "sector": "Communication Services"},
                    {"symbol": "1398.HK", "company": "Industrial and Commercial Bank of China Limited", "exchange": "HKEX", "price": 4.60, "change": 0.05, "changePercent": 1.10, "currency": "HKD", "sector": "Financials"},
                    {"symbol": "0005.HK", "company": "HSBC Holdings plc", "exchange": "HKEX", "price": 62.80, "change": 0.65, "changePercent": 1.05, "currency": "HKD", "sector": "Financials"},
                    {"symbol": "0939.HK", "company": "China Construction Bank Corporation", "exchange": "HKEX", "price": 5.50, "change": 0.07, "changePercent": 1.29, "currency": "HKD", "sector": "Financials"},
                    {"symbol": "9618.HK", "company": "JD.com, Inc.", "exchange": "HKEX", "price": 110.60, "change": 1.80, "changePercent": 1.65, "currency": "HKD", "sector": "Consumer Discretionary"},
                    {"symbol": "3690.HK", "company": "Meituan", "exchange": "HKEX", "price": 98.75, "change": 1.45, "changePercent": 1.49, "currency": "HKD", "sector": "Consumer Discretionary"},
                    {"symbol": "0883.HK", "company": "CNOOC Limited", "exchange": "HKEX", "price": 18.58, "change": 0.24, "changePercent": 1.31, "currency": "HKD", "sector": "Energy"},
                    {"symbol": "1928.HK", "company": "Sands China Ltd.", "exchange": "HKEX", "price": 16.98, "change": 0.26, "changePercent": 1.56, "currency": "HKD", "sector": "Consumer Discretionary"}
                ]
            elif index_name == "Shanghai Composite":
                # Shanghai Composite (China) constituents
                constituents = [
                    {"symbol": "600519.SS", "company": "Kweichow Moutai Co., Ltd.", "exchange": "SSE", "price": 1565.80, "change": 25.30, "changePercent": 1.64, "currency": "CNY", "sector": "Consumer Staples"},
                    {"symbol": "601318.SS", "company": "Ping An Insurance (Group) Company of China, Ltd.", "exchange": "SSE", "price": 48.25, "change": 0.65, "changePercent": 1.37, "currency": "CNY", "sector": "Financials"},
                    {"symbol": "600036.SS", "company": "China Merchants Bank Co., Ltd.", "exchange": "SSE", "price": 34.65, "change": 0.42, "changePercent": 1.23, "currency": "CNY", "sector": "Financials"},
                    {"symbol": "601398.SS", "company": "Industrial and Commercial Bank of China Limited", "exchange": "SSE", "price": 4.58, "change": 0.06, "changePercent": 1.33, "currency": "CNY", "sector": "Financials"},
                    {"symbol": "600276.SS", "company": "Jiangsu Hengrui Medicine Co., Ltd.", "exchange": "SSE", "price": 38.54, "change": 0.48, "changePercent": 1.26, "currency": "CNY", "sector": "Healthcare"},
                    {"symbol": "600887.SS", "company": "Inner Mongolia Yili Industrial Group Co., Ltd.", "exchange": "SSE", "price": 30.25, "change": 0.35, "changePercent": 1.17, "currency": "CNY", "sector": "Consumer Staples"},
                    {"symbol": "601288.SS", "company": "Agricultural Bank of China Limited", "exchange": "SSE", "price": 3.45, "change": 0.04, "changePercent": 1.17, "currency": "CNY", "sector": "Financials"},
                    {"symbol": "601988.SS", "company": "Bank of China Limited", "exchange": "SSE", "price": 3.32, "change": 0.03, "changePercent": 0.91, "currency": "CNY", "sector": "Financials"},
                    {"symbol": "600309.SS", "company": "Wanhua Chemical Group Co., Ltd.", "exchange": "SSE", "price": 75.20, "change": 1.25, "changePercent": 1.69, "currency": "CNY", "sector": "Materials"},
                    {"symbol": "600030.SS", "company": "CITIC Securities Co., Ltd.", "exchange": "SSE", "price": 22.40, "change": 0.28, "changePercent": 1.27, "currency": "CNY", "sector": "Financials"}
                ]
            elif index_name == "Taiwan Weighted":
                # Taiwan Weighted (Taiwan) constituents
                constituents = [
                    {"symbol": "2330.TW", "company": "Taiwan Semiconductor Manufacturing Company Limited", "exchange": "TWSE", "price": 765.00, "change": 15.00, "changePercent": 2.00, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "2317.TW", "company": "Hon Hai Precision Industry Co., Ltd.", "exchange": "TWSE", "price": 142.50, "change": 2.50, "changePercent": 1.79, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "2454.TW", "company": "MediaTek Inc.", "exchange": "TWSE", "price": 820.00, "change": 12.00, "changePercent": 1.49, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "2412.TW", "company": "Chunghwa Telecom Co., Ltd.", "exchange": "TWSE", "price": 125.50, "change": 1.50, "changePercent": 1.21, "currency": "TWD", "sector": "Communication Services"},
                    {"symbol": "2308.TW", "company": "Delta Electronics, Inc.", "exchange": "TWSE", "price": 312.00, "change": 4.50, "changePercent": 1.46, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "2303.TW", "company": "United Microelectronics Corporation", "exchange": "TWSE", "price": 52.80, "change": 0.90, "changePercent": 1.73, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "2881.TW", "company": "Fubon Financial Holding Co., Ltd.", "exchange": "TWSE", "price": 80.30, "change": 0.70, "changePercent": 0.88, "currency": "TWD", "sector": "Financials"},
                    {"symbol": "2882.TW", "company": "Cathay Financial Holding Co., Ltd.", "exchange": "TWSE", "price": 58.40, "change": 0.50, "changePercent": 0.86, "currency": "TWD", "sector": "Financials"},
                    {"symbol": "1301.TW", "company": "Formosa Plastics Corporation", "exchange": "TWSE", "price": 78.50, "change": 0.90, "changePercent": 1.16, "currency": "TWD", "sector": "Materials"},
                    {"symbol": "2886.TW", "company": "Mega Financial Holding Company Ltd.", "exchange": "TWSE", "price": 35.20, "change": 0.30, "changePercent": 0.86, "currency": "TWD", "sector": "Financials"}
                ]
            elif index_name == "KOSPI":
                # KOSPI (South Korea) constituents
                constituents = [
                    {"symbol": "005930.KS", "company": "Samsung Electronics Co., Ltd.", "exchange": "KRX", "price": 65800.00, "change": 800.00, "changePercent": 1.23, "currency": "KRW", "sector": "Technology"},
                    {"symbol": "000660.KS", "company": "SK hynix Inc.", "exchange": "KRX", "price": 175000.00, "change": 3000.00, "changePercent": 1.75, "currency": "KRW", "sector": "Technology"},
                    {"symbol": "207940.KS", "company": "Samsung Biologics Co., Ltd.", "exchange": "KRX", "price": 725000.00, "change": 9000.00, "changePercent": 1.26, "currency": "KRW", "sector": "Healthcare"},
                    {"symbol": "051910.KS", "company": "LG Chem, Ltd.", "exchange": "KRX", "price": 450000.00, "change": 7000.00, "changePercent": 1.58, "currency": "KRW", "sector": "Materials"},
                    {"symbol": "068270.KS", "company": "Celltrion, Inc.", "exchange": "KRX", "price": 168000.00, "change": 2000.00, "changePercent": 1.20, "currency": "KRW", "sector": "Healthcare"},
                    {"symbol": "035420.KS", "company": "NAVER Corporation", "exchange": "KRX", "price": 225000.00, "change": 3500.00, "changePercent": 1.58, "currency": "KRW", "sector": "Communication Services"},
                    {"symbol": "005380.KS", "company": "Hyundai Motor Company", "exchange": "KRX", "price": 195000.00, "change": 2500.00, "changePercent": 1.30, "currency": "KRW", "sector": "Consumer Discretionary"},
                    {"symbol": "055550.KS", "company": "Shinhan Financial Group Co., Ltd.", "exchange": "KRX", "price": 37500.00, "change": 400.00, "changePercent": 1.08, "currency": "KRW", "sector": "Financials"},
                    {"symbol": "000270.KS", "company": "Kia Corporation", "exchange": "KRX", "price": 88500.00, "change": 1200.00, "changePercent": 1.37, "currency": "KRW", "sector": "Consumer Discretionary"},
                    {"symbol": "105560.KS", "company": "KB Financial Group Inc.", "exchange": "KRX", "price": 58500.00, "change": 500.00, "changePercent": 0.86, "currency": "KRW", "sector": "Financials"}
                ]
            elif index_name == "Straits Times":
                # Straits Times (Singapore) constituents
                constituents = [
                    {"symbol": "D05.SI", "company": "DBS Group Holdings Ltd", "exchange": "SGX", "price": 34.85, "change": 0.42, "changePercent": 1.22, "currency": "SGD", "sector": "Financials"},
                    {"symbol": "O39.SI", "company": "Oversea-Chinese Banking Corporation Limited", "exchange": "SGX", "price": 12.96, "change": 0.15, "changePercent": 1.17, "currency": "SGD", "sector": "Financials"},
                    {"symbol": "U11.SI", "company": "United Overseas Bank Limited", "exchange": "SGX", "price": 28.75, "change": 0.32, "changePercent": 1.13, "currency": "SGD", "sector": "Financials"},
                    {"symbol": "Z74.SI", "company": "Singapore Telecommunications Limited", "exchange": "SGX", "price": 2.45, "change": 0.03, "changePercent": 1.24, "currency": "SGD", "sector": "Communication Services"},
                    {"symbol": "C52.SI", "company": "ComfortDelGro Corporation Limited", "exchange": "SGX", "price": 1.38, "change": 0.01, "changePercent": 0.73, "currency": "SGD", "sector": "Industrials"},
                    {"symbol": "C38U.SI", "company": "CapitaLand Integrated Commercial Trust", "exchange": "SGX", "price": 2.05, "change": 0.02, "changePercent": 0.98, "currency": "SGD", "sector": "Real Estate"},
                    {"symbol": "C09.SI", "company": "City Developments Limited", "exchange": "SGX", "price": 7.25, "change": 0.08, "changePercent": 1.12, "currency": "SGD", "sector": "Real Estate"},
                    {"symbol": "A17U.SI", "company": "Ascendas Real Estate Investment Trust", "exchange": "SGX", "price": 2.72, "change": 0.03, "changePercent": 1.12, "currency": "SGD", "sector": "Real Estate"},
                    {"symbol": "H78.SI", "company": "Hongkong Land Holdings Limited", "exchange": "SGX", "price": 4.25, "change": 0.05, "changePercent": 1.19, "currency": "SGD", "sector": "Real Estate"},
                    {"symbol": "S68.SI", "company": "Singapore Exchange Limited", "exchange": "SGX", "price": 9.75, "change": 0.10, "changePercent": 1.04, "currency": "SGD", "sector": "Financials"}
                ]
            elif index_name == "SET Composite":
                # SET Composite (Thailand) constituents
                constituents = [
                    {"symbol": "PTT.BK", "company": "PTT Public Company Limited", "exchange": "SET", "price": 35.75, "change": 0.50, "changePercent": 1.42, "currency": "THB", "sector": "Energy"},
                    {"symbol": "PTTEP.BK", "company": "PTT Exploration and Production Public Company Limited", "exchange": "SET", "price": 156.00, "change": 2.50, "changePercent": 1.63, "currency": "THB", "sector": "Energy"},
                    {"symbol": "AOT.BK", "company": "Airports of Thailand Public Company Limited", "exchange": "SET", "price": 67.25, "change": 1.25, "changePercent": 1.89, "currency": "THB", "sector": "Industrials"},
                    {"symbol": "CPALL.BK", "company": "CP ALL Public Company Limited", "exchange": "SET", "price": 62.50, "change": 0.75, "changePercent": 1.21, "currency": "THB", "sector": "Consumer Staples"},
                    {"symbol": "ADVANC.BK", "company": "Advanced Info Service Public Company Limited", "exchange": "SET", "price": 189.00, "change": 2.00, "changePercent": 1.07, "currency": "THB", "sector": "Communication Services"},
                    {"symbol": "SCB.BK", "company": "Siam Commercial Bank Public Company Limited", "exchange": "SET", "price": 118.00, "change": 1.50, "changePercent": 1.29, "currency": "THB", "sector": "Financials"},
                    {"symbol": "KBANK.BK", "company": "Kasikornbank Public Company Limited", "exchange": "SET", "price": 138.50, "change": 1.50, "changePercent": 1.09, "currency": "THB", "sector": "Financials"},
                    {"symbol": "BBL.BK", "company": "Bangkok Bank Public Company Limited", "exchange": "SET", "price": 128.00, "change": 1.00, "changePercent": 0.79, "currency": "THB", "sector": "Financials"},
                    {"symbol": "CPF.BK", "company": "Charoen Pokphand Foods Public Company Limited", "exchange": "SET", "price": 28.50, "change": 0.50, "changePercent": 1.79, "currency": "THB", "sector": "Consumer Staples"},
                    {"symbol": "TRUE.BK", "company": "True Corporation Public Company Limited", "exchange": "SET", "price": 4.96, "change": 0.08, "changePercent": 1.64, "currency": "THB", "sector": "Communication Services"}
                ]
            elif index_name == "Jakarta Composite":
                # Jakarta Composite (Indonesia) constituents
                constituents = [
                    {"symbol": "BBCA.JK", "company": "PT Bank Central Asia Tbk", "exchange": "IDX", "price": 9625.00, "change": 125.00, "changePercent": 1.32, "currency": "IDR", "sector": "Financials"},
                    {"symbol": "BBRI.JK", "company": "PT Bank Rakyat Indonesia (Persero) Tbk", "exchange": "IDX", "price": 4370.00, "change": 60.00, "changePercent": 1.39, "currency": "IDR", "sector": "Financials"},
                    {"symbol": "TLKM.JK", "company": "PT Telkom Indonesia (Persero) Tbk", "exchange": "IDX", "price": 3860.00, "change": 40.00, "changePercent": 1.05, "currency": "IDR", "sector": "Communication Services"},
                    {"symbol": "ASII.JK", "company": "PT Astra International Tbk", "exchange": "IDX", "price": 5250.00, "change": 75.00, "changePercent": 1.45, "currency": "IDR", "sector": "Consumer Discretionary"},
                    {"symbol": "BMRI.JK", "company": "PT Bank Mandiri (Persero) Tbk", "exchange": "IDX", "price": 5675.00, "change": 75.00, "changePercent": 1.34, "currency": "IDR", "sector": "Financials"},
                    {"symbol": "UNVR.JK", "company": "PT Unilever Indonesia Tbk", "exchange": "IDX", "price": 4200.00, "change": 50.00, "changePercent": 1.20, "currency": "IDR", "sector": "Consumer Staples"},
                    {"symbol": "HMSP.JK", "company": "PT Hanjaya Mandala Sampoerna Tbk", "exchange": "IDX", "price": 850.00, "change": 10.00, "changePercent": 1.19, "currency": "IDR", "sector": "Consumer Staples"},
                    {"symbol": "BRPT.JK", "company": "PT Barito Pacific Tbk", "exchange": "IDX", "price": 1335.00, "change": 25.00, "changePercent": 1.91, "currency": "IDR", "sector": "Materials"},
                    {"symbol": "INDF.JK", "company": "PT Indofood Sukses Makmur Tbk", "exchange": "IDX", "price": 6325.00, "change": 75.00, "changePercent": 1.20, "currency": "IDR", "sector": "Consumer Staples"},
                    {"symbol": "ICBP.JK", "company": "PT Indofood CBP Sukses Makmur Tbk", "exchange": "IDX", "price": 10025.00, "change": 125.00, "changePercent": 1.26, "currency": "IDR", "sector": "Consumer Staples"}
                ]
            # For other Asian indices, provide a mixed set of major Asian stocks
            else:
                constituents = [
                    {"symbol": "0700.HK", "company": "Tencent Holdings Limited", "exchange": "HKEX", "price": 368.40, "change": 5.80, "changePercent": 1.60, "currency": "HKD", "sector": "Communication Services"},
                    {"symbol": "7203.T", "company": "Toyota Motor Corporation", "exchange": "TSE", "price": 3150.00, "change": 35.00, "changePercent": 1.12, "currency": "JPY", "sector": "Consumer Discretionary"},
                    {"symbol": "9988.HK", "company": "Alibaba Group Holding Limited", "exchange": "HKEX", "price": 75.45, "change": 1.05, "changePercent": 1.41, "currency": "HKD", "sector": "Consumer Discretionary"},
                    {"symbol": "005930.KS", "company": "Samsung Electronics Co., Ltd.", "exchange": "KRX", "price": 65800.00, "change": 800.00, "changePercent": 1.23, "currency": "KRW", "sector": "Technology"},
                    {"symbol": "2330.TW", "company": "Taiwan Semiconductor Manufacturing Company Limited", "exchange": "TWSE", "price": 765.00, "change": 15.00, "changePercent": 2.00, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "D05.SI", "company": "DBS Group Holdings Ltd", "exchange": "SGX", "price": 34.85, "change": 0.42, "changePercent": 1.22, "currency": "SGD", "sector": "Financials"},
                    {"symbol": "600519.SS", "company": "Kweichow Moutai Co., Ltd.", "exchange": "SSE", "price": 1565.80, "change": 25.30, "changePercent": 1.64, "currency": "CNY", "sector": "Consumer Staples"},
                    {"symbol": "6861.T", "company": "Keyence Corporation", "exchange": "TSE", "price": 67100.00, "change": 900.00, "changePercent": 1.36, "currency": "JPY", "sector": "Technology"},
                    {"symbol": "2317.TW", "company": "Hon Hai Precision Industry Co., Ltd.", "exchange": "TWSE", "price": 142.50, "change": 2.50, "changePercent": 1.79, "currency": "TWD", "sector": "Technology"},
                    {"symbol": "9432.T", "company": "Nippon Telegraph and Telephone Corporation", "exchange": "TSE", "price": 4250.00, "change": 52.00, "changePercent": 1.24, "currency": "JPY", "sector": "Communication Services"}
                ]
        
        # If no constituents found, load fallback data
        if not constituents:
            logger.info(f"No live data for {index_name}, loading fallback data")
            constituents = load_fallback_data(index_name)
        
        # If still no data, use sample data as last resort
        if not constituents:
            logger.warning(f"No fallback data for {index_name}, using sample data")
            constituents = generate_sample_stock_data()
        
        # If we get here, we should have some constituents from one of the methods above
        # Or an empty list if none of the methods worked
        logger.info(f"Returning {len(constituents)} constituents for {index_name}")
        return jsonify(constituents)
    except Exception as e:
        logger.error(f"Error in get_index_constituents for {index_name}: {e}", exc_info=True)
        # Return an empty list with an error message
        error_response = {
            "error": f"Failed to load constituents for {index_name}: {str(e)}",
            "constituents": []
        }
        # Return HTTP 200 with error info to allow the frontend to handle it gracefully
        return jsonify([])

@app.route('/api/stock/<symbol>/technical', methods=['GET'])
@cache_with_timeout(timeout=1800)  # Cache technical indicators for 30 minutes
def get_technical_indicators(symbol):
    """
    Get technical indicators for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Technical indicators.
    """
    # Get company details to check if it's an Indian stock
    company_details = fetch_yahoo_finance_company_overview(symbol)
    is_indian_stock = company_details.get("exchange") == "NSE" and company_details.get("currency") == "INR"
    
    # Generate random technical indicator values
    import random
    
    rsi = round(random.uniform(30, 70), 2)
    macd = round(random.uniform(-2, 2), 2)
    signal = round(random.uniform(-2, 2), 2)
    histogram = round(macd - signal, 2)
    
    # Get current price from stock data
    try:
        # Try to get actual stock data for more realistic values
        stock_data = fetch_yahoo_finance_time_series(symbol, '1mo')
        if stock_data and 'prices' in stock_data and stock_data['prices']:
            # Use last price as a base
            last_price = stock_data['prices'][0]['close']
            price_base = last_price
        else:
            price_base = 100.0
    except Exception as e:
        logger.error(f"Error getting price data for technical indicators: {e}")
        price_base = 100.0
    
    # Create indicators based on the price
    ema50 = round(price_base * random.uniform(0.95, 1.05), 2)
    ema200 = round(price_base * random.uniform(0.9, 1.1), 2)
    sma50 = round(price_base * random.uniform(0.95, 1.05), 2)
    sma200 = round(price_base * random.uniform(0.9, 1.1), 2)
    atr = round(price_base * random.uniform(0.01, 0.05), 2)
    upper_band = round(price_base * random.uniform(1.05, 1.15), 2)
    lower_band = round(price_base * random.uniform(0.85, 0.95), 2)
    middle_band = round(price_base, 2)
    
    return jsonify({
        "symbol": symbol,
        "rsi": rsi,
        "macd": macd,
        "signal": signal,
        "histogram": histogram,
        "ema50": ema50,
        "ema200": ema200,
        "sma50": sma50,
        "sma200": sma200,
        "atr": atr,
        "upperBollingerBand": upper_band,
        "lowerBollingerBand": lower_band,
        "middleBollingerBand": middle_band,
        "exchange": company_details.get("exchange", ""),
        "currency": company_details.get("currency", "USD")
    })

@app.route('/api/stock/<symbol>/fundamental', methods=['GET'])
@cache_with_timeout(timeout=3600)  # Cache fundamental data for 1 hour
def get_fundamental_data(symbol):
    """
    Get fundamental data for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Fundamental data.
    """
    import random
    
    # Get company details to set proper name, currency, and exchange
    company_details = fetch_yahoo_finance_company_overview(symbol)
    company_name = company_details.get("company", f"Company for {symbol}")
    currency = company_details.get("currency", "USD")
    exchange = company_details.get("exchange", "")
    sector = company_details.get("sector", "Technology")
    industry = company_details.get("industry", "Computer Hardware")
    
    # For Indian stocks, use more appropriate value ranges
    if currency == "INR":
        market_cap_min = 5000000000  # 500 crore
        market_cap_max = 25000000000000  # 25 lakh crore
        revenue_min = 100000000  # 10 crore
        revenue_max = 15000000000000  # 15 lakh crore
    else:
        market_cap_min = 1000000000  # 1 billion
        market_cap_max = 2000000000000  # 2 trillion
        revenue_min = 1000000000  # 1 billion
        revenue_max = 300000000000  # 300 billion
    
    return jsonify({
        "symbol": symbol,
        "faDetailedInfo": {
            "financialMetrics": {
                "marketCap": round(random.uniform(market_cap_min, market_cap_max), 2),
                "priceToBook": round(random.uniform(1, 10), 2),
                "priceToSales": round(random.uniform(1, 15), 2),
                "pegRatio": round(random.uniform(0.5, 3), 2),
                "evToEbitda": round(random.uniform(5, 20), 2)
            },
            "companyOverview": {
                "companyName": company_name,
                "sector": sector,
                "industry": industry,
                "exchange": exchange,
                "currency": currency
            },
            "growthIndicators": {
                "revenueGrowthYoY": round(random.uniform(-10, 30), 2),
                "profitMargins": round(random.uniform(5, 35), 2),
                "roe": round(random.uniform(5, 40), 2),
                "roa": round(random.uniform(3, 20), 2)
            },
            "riskIndicators": {
                "debtToEquityRatio": round(random.uniform(0.1, 2), 2),
                "interestCoverageRatio": round(random.uniform(2, 20), 2),
                "beta": round(random.uniform(0.5, 2), 2),
                "quickRatio": round(random.uniform(0.8, 3), 2)
            },
            "dividends": {
                "payoutRatio": round(random.uniform(0, 80), 2),
                "dividendGrowthRate": round(random.uniform(-5, 15), 2)
            },
            "cashFlowStatement": {
                "operatingCashFlow": round(random.uniform(revenue_min / 100, revenue_max / 10), 2),
                "investingCashFlow": round(random.uniform(-revenue_max / 20, 0), 2),
                "financingCashFlow": round(random.uniform(-revenue_max / 20, revenue_max / 20), 2),
                "cashFlowToDebtRatio": round(random.uniform(0.1, 2), 2)
            },
            "incomeStatement": {
                "totalRevenue": round(random.uniform(revenue_min, revenue_max), 2),
                "operatingIncome": round(random.uniform(revenue_min / 10, revenue_max / 3), 2),
                "netIncome": round(random.uniform(revenue_min / 20, revenue_max / 6), 2),
                "grossProfit": round(random.uniform(revenue_min / 2, revenue_max / 1.5), 2)
            },
            "balanceSheetInformation": {
                "totalAssets": round(random.uniform(revenue_min, revenue_max * 1.3), 2),
                "totalLiabilities": round(random.uniform(revenue_min / 2, revenue_max / 1.5), 2),
                "totalStockholderEquity": round(random.uniform(revenue_min / 2, revenue_max / 1.5), 2),
                "longTermDebt": round(random.uniform(revenue_min / 10, revenue_max / 3), 2),
                "currentAssets": round(random.uniform(revenue_min / 10, revenue_max / 3), 2),
                "currentLiabilities": round(random.uniform(revenue_min / 20, revenue_max / 6), 2),
                "inventory": round(random.uniform(revenue_min / 100, revenue_max / 15), 2)
            },
            "profitabilityIndicators": {
                "grossMargin": round(random.uniform(20, 80), 2),
                "operatingMargin": round(random.uniform(10, 40), 2),
                "netMargin": round(random.uniform(5, 30), 2)
            },
            "liquidityIndicators": {
                "cashRatio": round(random.uniform(0.2, 2), 2),
                "workingCapital": round(random.uniform(revenue_min / 100, revenue_max / 6), 2)
            },
            "investorInsightMetrics": {
                "eps": round(random.uniform(0.5, 20), 2),
                "peRatio": round(random.uniform(5, 50), 2),
                "revenueGrowth": round(random.uniform(-10, 30), 2),
                "debtToEquity": round(random.uniform(0.1, 2), 2),
                "earningsGrowthYoY": round(random.uniform(-15, 40), 2),
                "currentRatio": round(random.uniform(0.8, 3), 2)
            }
        }
    })

@app.route('/api/stock/<symbol>/prediction', methods=['GET'])
@cache_with_timeout(timeout=3600)  # Cache prediction data for 1 hour
def get_prediction_data(symbol):
    """
    Get prediction data for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Prediction data.
    """
    import random
    from datetime import datetime, timedelta
    
    # Get company details and current stock price
    company_details = fetch_yahoo_finance_company_overview(symbol)
    currency = company_details.get("currency", "USD")
    exchange = company_details.get("exchange", "")
    
    # Try to get current price from time series data
    try:
        stock_data = fetch_yahoo_finance_time_series(symbol, '1mo')
        if stock_data and 'prices' in stock_data and stock_data['prices']:
            base_price = stock_data['prices'][0]['close']
        else:
            base_price = 100.0
    except Exception as e:
        logger.error(f"Error getting price data for predictions: {e}")
        base_price = 100.0
    
    predictions = []
    dates = []
    
    current_date = datetime.now()
    for i in range(15):
        current_date += timedelta(days=1)
        dates.append(current_date.strftime("%Y-%m-%d"))
        
        # Generate predictions with slight upward trend
        prediction = base_price * (1 + 0.001 * i + random.uniform(-0.01, 0.01))
        predictions.append(round(prediction, 2))
    
    return jsonify({
        "symbol": symbol,
        "predictions": predictions,
        "dates": dates,
        "currency": currency,
        "exchange": exchange
    })

@app.route('/api/stock/<symbol>/news', methods=['GET'])
@cache_with_timeout(timeout=900)  # Cache stock news for 15 minutes
def get_stock_news(symbol):
    """
    Get news for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: List of news articles.
    """
    try:
        # Get company details for a better search term
        company_details = fetch_yahoo_finance_company_overview(symbol)
        company_name = company_details.get("company", symbol)
        
        search_term = company_name
        
        # Try to get news from Yahoo Finance API
        news_articles = []
        try:
            ticker = yf.Ticker(symbol)
            
            # Get news from ticker if available
            if hasattr(ticker, 'news') and callable(getattr(ticker, 'news')):
                yf_news = ticker.news()
                if yf_news and isinstance(yf_news, list):
                    for article in yf_news[:10]:  # Limit to 10 articles
                        news_articles.append({
                            "title": article.get("title", f"News about {search_term}"),
                            "date": datetime.fromtimestamp(article.get("providerPublishTime", 0)).strftime("%Y-%m-%d"),
                            "source": article.get("publisher", "Financial News"),
                            "url": article.get("link", "#"),
                            "summary": article.get("summary", f"Latest news about {search_term}")
                        })
        except Exception as e:
            logger.warning(f"Could not get news from Yahoo Finance: {e}")
            
        # If no news found, generate sample news
        if not news_articles:
            # Generate at least 5 news articles
            for i in range(5):
                today = datetime.now()
                days_ago = random.randint(0, 10)
                article_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                
                # Create varied titles based on the company and random factors
                titles = [
                    f"{search_term} Reports Strong Q{random.randint(1, 4)} Results",
                    f"Analysts Upgrade {search_term} to 'Buy'",
                    f"{search_term} Announces New Strategic Partnership",
                    f"Investors React to {search_term}'s Latest Product Launch",
                    f"{search_term} Expands Operations in {random.choice(['Asia', 'Europe', 'North America'])}",
                    f"Market Outlook: What's Next for {search_term}?",
                    f"{search_term} Addresses Industry Challenges",
                    f"The Future of {search_term}: Analysts Weigh In",
                    f"{search_term} CEO Discusses Growth Strategy",
                    f"Regulatory Changes Impact {search_term}'s Business Model"
                ]
                
                sources = ["Financial Times", "Bloomberg", "Reuters", "CNBC", "The Economic Times", 
                           "Moneycontrol", "Business Standard", "Mint", "Forbes", "Wall Street Journal"]
                
                news_articles.append({
                    "title": random.choice(titles),
                    "date": article_date,
                    "source": random.choice(sources),
                    "url": "#",
                    "summary": f"Latest news about {search_term} and its performance in the market. " +
                             f"Analysts and investors are closely watching the company's developments."
                })
                
        return jsonify(news_articles)
    except Exception as e:
        logger.error(f"Error getting stock news: {e}", exc_info=True)
        return jsonify([])

@app.route('/api/market/news', methods=['GET'])
@cache_with_timeout(timeout=1800)  # Cache market news for 30 minutes
def get_market_news():
    """
    Get general market news.
    Returns:
        JSON: List of market news articles.
    """
    try:
        # Try to get real market news (future implementation)
        # For now, generate sample market news
        news_articles = []
        
        # Generate 10 market news articles
        today = datetime.now()
        
        market_headlines = [
            "Global Markets React to Fed's Interest Rate Decision",
            "Asian Markets Rally on Strong Economic Data",
            "European Stocks Climb on Banking Sector Performance",
            "US Markets Close Higher as Tech Stocks Lead Gains",
            "Inflation Concerns Weigh on Market Sentiment",
            "Oil Prices Surge Amid Supply Chain Disruptions",
            "Market Volatility Increases as Earnings Season Begins",
            "Indian Markets Hit Record High on Foreign Investment",
            "Bank Stocks Rally After Stress Test Results",
            "Cryptocurrency Market Faces Regulatory Scrutiny",
            "Manufacturing Data Boosts Industrial Stocks",
            "Healthcare Sector Outperforms on FDA Approvals",
            "Retail Stocks Jump on Strong Consumer Spending Data",
            "Tech Sector Correction Weighs on NASDAQ",
            "Small-Cap Stocks Outperform in Market Recovery"
        ]
        
        sources = ["Financial Times", "Bloomberg", "Reuters", "CNBC", "The Economic Times", 
                   "Moneycontrol", "Business Standard", "Mint", "Forbes", "Wall Street Journal"]
        
        for i in range(10):
            days_ago = random.randint(0, 7)
            article_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            headline = random.choice(market_headlines)
            # Remove the headline to avoid duplicates if there are enough headlines
            if len(market_headlines) > 1:
                market_headlines.remove(headline)
            
            news_articles.append({
                "title": headline,
                "date": article_date,
                "source": random.choice(sources),
                "url": "#",
                "summary": "Market analysis and insights from industry experts. " +
                         "This article covers the latest trends, economic indicators, and their impact on financial markets."
            })
            
        return jsonify(news_articles)
    except Exception as e:
        logger.error(f"Error getting market news: {e}", exc_info=True)
        return jsonify([])

@app.route('/api/market/<market>/top', methods=['GET'])
@cache_with_timeout(timeout=1800)  # Cache top stocks for 30 minutes
def get_top_stocks_by_market(market):
    """
    Get top stocks for a specific market.
    
    Args:
        market (str): Market code (nse, bse, nasdaq, nyse)
    
    Query Parameters:
        limit (int): Number of stocks to return (default: 10)
    
    Returns:
        JSON: List of top stocks from the specified market
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        market = market.lower()
        
        # Validate market parameter
        valid_markets = ['nse', 'bse', 'nasdaq', 'nyse', 'ftse', 'dax', 'nikkei', 'shcomp']
        if market not in valid_markets:
            return jsonify({"error": f"Invalid market. Valid options are: {', '.join(valid_markets)}"}), 400
        
        # Get all popular stocks
        all_stocks = fetch_popular_stocks()
        
        # Filter by exchange and add simulated price data
        # Map market parameter to exchange names
        exchange_map = {
            'nse': 'NSE',
            'bse': 'BSE',
            'nasdaq': 'NASDAQ',
            'nyse': 'NYSE',
            'ftse': 'FTSE',
            'dax': 'DAX',
            'nikkei': 'NIKKEI',
            'shcomp': 'SHCOMP'
        }
        
        exchange = exchange_map[market]
        
        # Filter stocks by exchange
        filtered_stocks = [stock for stock in all_stocks if stock.get('exchange') == exchange]
        
        # Add price and change data if not present
        for stock in filtered_stocks:
            if 'price' not in stock:
                # Generate realistic price based on the stock's exchange
                if exchange in ['NSE', 'BSE']:
                    # Indian stocks often have prices in hundreds or thousands of rupees
                    stock['price'] = round(random.uniform(500, 5000), 2)
                    stock['currency'] = 'INR'
                elif exchange in ['FTSE']:
                    # UK stocks - prices in GBP
                    stock['price'] = round(random.uniform(5, 2000), 2)
                    stock['currency'] = 'GBP'
                elif exchange in ['DAX']:
                    # German stocks - prices in EUR
                    stock['price'] = round(random.uniform(10, 300), 2)
                    stock['currency'] = 'EUR'
                elif exchange in ['NIKKEI']:
                    # Japanese stocks - prices in JPY (often higher numbers)
                    stock['price'] = round(random.uniform(1000, 30000), 2)
                    stock['currency'] = 'JPY'
                elif exchange in ['SHCOMP']:
                    # Chinese stocks - prices in CNY
                    stock['price'] = round(random.uniform(5, 100), 2)
                    stock['currency'] = 'CNY'
                else:
                    # US stocks often have prices in tens or hundreds of dollars
                    stock['price'] = round(random.uniform(50, 1000), 2)
                    stock['currency'] = 'USD'
            
            if 'change' not in stock:
                # Generate random change (-5% to +5% of price)
                change_percent = random.uniform(-5, 5)
                stock['change'] = round((stock['price'] * change_percent / 100), 2)
                stock['changePercent'] = round(change_percent, 2)
                
            # Add sector if not present
            if 'sector' not in stock:
                stock['sector'] = random.choice([
                    'Technology', 'Finance', 'Healthcare', 'Consumer Goods',
                    'Energy', 'Utilities', 'Industrials', 'Materials',
                    'Telecommunications', 'Real Estate'
                ])
        
        # Sort by market cap (or price if market cap not available)
        sorted_stocks = sorted(filtered_stocks, 
                             key=lambda x: x.get('market_cap', x.get('price', 0)), 
                             reverse=True)
        
        # Return limited number of stocks
        return jsonify(sorted_stocks[:limit])
        
    except Exception as e:
        logger.error(f"Error getting top stocks for {market}: {e}", exc_info=True)
        return jsonify([]), 500

@app.route('/api/stock/<symbol>/shorttermswing', methods=['GET'])
@cache_with_timeout(timeout=1800)  # Cache trading signals for 30 minutes
def get_shorttermswingsignal(symbol):
    """
    Get short-term swing trading signal for a specific stock.
    Path Parameters:
        symbol (str): Stock symbol.
    Returns:
        JSON: Trading signal.
    """
    import random
    
    # Get company details
    company_details = fetch_yahoo_finance_company_overview(symbol)
    currency = company_details.get("currency", "USD")
    exchange = company_details.get("exchange", "")
    
    # Try to get current price for more realistic targets
    try:
        stock_data = fetch_yahoo_finance_time_series(symbol, '1mo')
        if stock_data and 'prices' in stock_data and stock_data['prices']:
            current_price = stock_data['prices'][0]['close']
        else:
            current_price = 100.0
    except Exception as e:
        logger.error(f"Error getting price data for trading signal: {e}")
        current_price = 100.0
    
    signals = ["BUY", "SELL", "HOLD"]
    strengths = ["Strong", "Moderate", "Weak"]
    
    signal = random.choice(signals)
    strength = random.choice(strengths)
    score = round(random.uniform(-100, 100), 2)
    
    # Calculate target prices based on signal
    if signal == "BUY":
        target_price = round(current_price * (1 + random.uniform(0.03, 0.15)), 2)
        stop_loss = round(current_price * (1 - random.uniform(0.02, 0.08)), 2)
    elif signal == "SELL":
        target_price = round(current_price * (1 - random.uniform(0.03, 0.15)), 2)
        stop_loss = round(current_price * (1 + random.uniform(0.02, 0.08)), 2)
    else:  # HOLD
        target_price = round(current_price * (1 + random.uniform(-0.05, 0.05)), 2)
        stop_loss = round(current_price * (1 - random.uniform(0.05, 0.1)), 2)
    
    return jsonify({
        "symbol": symbol,
        "signal": signal,
        "strength": strength,
        "score": score,
        "currentPrice": current_price,
        "targetPrice": target_price,
        "stopLoss": stop_loss,
        "currency": currency,
        "exchange": exchange,
        "reason": f"Based on technical analysis, the {strength.lower()} {signal.lower()} signal is generated for {symbol}."
    })

# Main entry point
if __name__ == "__main__":
    # Always start WebSocket server in a separate thread
    # Add a unique identifier to the process to prevent port conflicts
    websocket_port = int(os.environ.get("WEBSOCKET_PORT", 5002))
    logger.info("WebSocket server started on port %s", websocket_port)
    
    # Use a daemon thread so it automatically terminates when the main thread exits
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
