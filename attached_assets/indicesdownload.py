"""
Indices Download Module

This module provides functions for downloading market indices and their constituents.
"""

import os
import json
import requests
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create cache directory if it doesn't exist
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
CONSTITUENTS_CACHE_DIR = os.path.join(CACHE_DIR, 'constituents')

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
    
if not os.path.exists(CONSTITUENTS_CACHE_DIR):
    os.makedirs(CONSTITUENTS_CACHE_DIR)

def get_indices_list():
    """
    Get a list of all available market indices.
    
    Returns:
        dict: Dictionary of market indices by country and region
    """
    cache_file = os.path.join(CACHE_DIR, 'indices_data.json')
    
    # Check if cache file exists and is less than 1 hour old
    if os.path.exists(cache_file):
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
        if file_age < 3600:  # 1 hour in seconds
            logger.info(f"Using cached indices data from {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    logger.info("Fetching fresh indices data")
    
    # Define the market structure - this is a sample structure
    markets = {
        "India": {
            "NSE": [
                "NIFTY 50", "NIFTY Next 50", "NIFTY 100", "NIFTY 200",
                "NIFTY 500", "NIFTY Midcap 50", "NIFTY Midcap 100",
                "NIFTY Smallcap 50", "NIFTY Smallcap 100", "NIFTY Smallcap 250",
                "NIFTY Bank", "NIFTY IT", "NIFTY Auto", "NIFTY Financial Services",
                "NIFTY FMCG", "NIFTY Healthcare", "NIFTY Media", "NIFTY Metal",
                "NIFTY Pharma", "NIFTY PSU Bank", "NIFTY Realty", 
                "Nifty VIX", "GIFT Nifty"
            ],
            "BSE": [
                "S&P BSE - 30", "S&P BSE - 100", "S&P BSE - 200", "S&P BSE - 500",
                "S&P BSE MidCap", "S&P BSE SmallCap", "S&P BSE Auto",
                "S&P BSE Bankex", "S&P BSE Capital Goods", "S&P BSE Consumer Durables",
                "S&P BSE FMCG", "S&P BSE Healthcare", "S&P BSE IT", "S&P BSE Metal",
                "S&P BSE Oil & Gas", "S&P BSE Power", "S&P BSE Realty", "S&P BSE Teck"
            ]
        },
        "United States": {
            "NYSE": [
                "Dow Jones Industrial Average", "NYSE Composite"
            ],
            "NASDAQ": [
                "NASDAQ Composite", "NASDAQ 100"
            ],
            "Other US Indices": [
                "S&P 100", "S&P 500", "Russell 2000", "Russell 1000", "Wilshire 5000"
            ]
        }
    }
    
    # Cache the data
    with open(cache_file, 'w') as f:
        json.dump(markets, f)
    
    return markets

def get_index_constituents(index_name, refresh=False):
    """
    Get constituents for a specific index.
    
    Args:
        index_name (str): Name of the index
        refresh (bool): Whether to refresh the cache
        
    Returns:
        list: List of constituent companies
    """
    # Create a clean filename from the index name
    cache_filename = index_name.replace('/', '_').replace(' ', '_').replace('&', 'and')
    cache_file = os.path.join(CONSTITUENTS_CACHE_DIR, f"{cache_filename}.json")
    
    # Check if cache file exists and refresh is not requested
    if os.path.exists(cache_file) and not refresh:
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
        if file_age < 86400:  # 24 hours in seconds
            logger.info(f"Using cached constituents for {index_name}")
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    logger.info(f"Fetching fresh constituents for {index_name}")
    
    # This would be replaced with actual API calls or web scraping
    # For now, we'll return sample data
    constituents = []
    
    # Sample data based on the index name
    if index_name == "NIFTY 50":
        constituents = [
            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "sector": "Energy"},
            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "sector": "IT"},
            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "sector": "Financial Services"},
            {"symbol": "INFY", "company": "Infosys Ltd.", "sector": "IT"},
            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "sector": "Financial Services"}
        ]
    elif index_name == "S&P 500":
        constituents = [
            {"symbol": "AAPL", "company": "Apple Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "company": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "AMZN", "company": "Amazon.com, Inc.", "sector": "Consumer Discretionary"},
            {"symbol": "GOOGL", "company": "Alphabet Inc.", "sector": "Communication Services"},
            {"symbol": "TSLA", "company": "Tesla, Inc.", "sector": "Consumer Discretionary"}
        ]
    
    # Cache the data
    with open(cache_file, 'w') as f:
        json.dump(constituents, f)
    
    return constituents
