"""
PyTrade - Utilities Module

This module provides utility functions and helpers used throughout the PyTrade application.
It includes functionality for data fetching, parsing, logging, and other common operations
that are shared across different components of the system.

Key features:
- External API integration (Alpha Vantage, Yahoo Finance, etc.)
- Data parsing and formatting utilities
- Logging configuration and helpers
- File operations for data caching
- Error handling and retry mechanisms

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""

import os
import requests
import json
import logging
from bs4 import BeautifulSoup
import time
import pandas as pd
from typing import Dict, List, Optional, Any

# Determine the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the log directory relative to the script directory
log_dir = os.path.join(script_dir, "log")

try:
    os.makedirs(log_dir, exist_ok=True, mode=0o777)  # Ensure the directory exists with full permissions
    log_file = os.path.join(log_dir, "utils.log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.debug("Logger initialized successfully.")
except Exception as e:
    print(f"Error configuring logging: {e}")  # Print to console if logging fails
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # Fallback to console logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to configure file logging: {e}")

logger.info("utils module initialized.")

def get_alpha_vantage_data(ticker, api_key, function="TIME_SERIES_DAILY"):
    """
    Fetch stock data from Alpha Vantage API.

    Args:
        ticker (str): Stock ticker symbol.
        api_key (str): Alpha Vantage API key.
        function (str): API function to call (default: "TIME_SERIES_DAILY").

    Returns:
        dict: JSON response from Alpha Vantage API.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": ticker,
        "apikey": api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Alpha Vantage for {ticker}: {e}")
        return None

class RateLimiter:
    def __init__(self, rate, period):
        self.rate = rate
        self.period = period
        self.requests = []

    def allow_request(self):
        current_time = time.time()
        self.requests = [t for t in self.requests if current_time - t < self.period]
        if len(self.requests) < self.rate:
            self.requests.append(current_time)
            return True
        else:
            logger.warning("Rate limit exceeded. Request denied.")
            return False

# NSEPython utility wrappers
def get_nse_indices():
    """
    Wrapper for nsepython.indices() function.
    
    Returns:
        dict: NSE indices data
    """
    try:
        from nsepython import indices
        return indices()
    except Exception as e:
        logger.error(f"Error fetching NSE indices: {e}")
        return {}

def get_nse_eq(symbol):
    """
    Wrapper for nsepython.nse_eq() function.
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        dict: NSE equity data
    """
    try:
        from nsepython import nse_eq
        return nse_eq(symbol)
    except Exception as e:
        logger.error(f"Error fetching NSE equity data for {symbol}: {e}")
        return {}

def get_index_info(index):
    """
    Wrapper for nsepython.index_info() function.
    
    Args:
        index (str): Index name
        
    Returns:
        dict: Index information
    """
    try:
        from nsepython import index_info
        return index_info(index)
    except Exception as e:
        logger.error(f"Error fetching index info for {index}: {e}")
        return {}

def get_nse_index_quote(index):
    """
    Wrapper for nsepython.nse_get_index_quote() function.
    
    Args:
        index (str): Index name
        
    Returns:
        dict: Index quote data
    """
    try:
        from nsepython import nse_get_index_quote
        return nse_get_index_quote(index)
    except Exception as e:
        logger.error(f"Error fetching index quote for {index}: {e}")
        return {}

def get_nse_symbols():
    """
    Wrapper for nsepython.nse_eq_symbols() function.
    
    Returns:
        list: List of NSE equity symbols
    """
    try:
        from nsepython import nse_eq_symbols
        return nse_eq_symbols()
    except Exception as e:
        logger.error(f"Error fetching NSE equity symbols: {e}")
        return []