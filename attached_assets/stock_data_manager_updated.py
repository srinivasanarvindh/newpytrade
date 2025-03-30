"""
PyTrade - Stock Data Manager Module

This module manages the retrieval, caching, and serving of stock market data for PyTrade.
It provides functionality to fetch data from various sources, handle data freshness,
and fall back to cached data when needed.

Key features:
- Data freshness management with configurable refresh intervals
- Support for multiple global indices (US, India, Europe, Asia)
- Automatic fallback to cached data when live sources are unavailable
- Efficient data format for frontend consumption

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""

import os
import json
import logging
from fetchstockdata import (
    fetch_nifty_constituents,
    fetch_bse_30_constituents,
    fetch_wikipedia_constituents,
)
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Constants
STOCK_DATA_DIR = os.path.join(os.path.dirname(__file__), "../stockdata")
REFRESH_INTERVAL = timedelta(days=1)
SUPPORTED_INDICES = [
    "NIFTY 50",
    "NIFTY 150",
    "NIFTY 500",
    "Dow Jones IA",
    "Dow Jones TA",
    "Dow Jones UA",
    "S&P 100",
    "S&P 500",
    "S&P MidCap 400",
    "S&P SmallCap 600",
    "Russell 1000",
    "BSE 30",
    "Nasdaq-100",
]

# Ensure stock data directory exists
os.makedirs(STOCK_DATA_DIR, exist_ok=True)

def is_file_outdated(file_path, refresh_interval):
    """Check if a file is outdated based on the refresh interval."""
    if not os.path.exists(file_path):
        return True
    last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - last_modified_time > refresh_interval

def fetch_live_data(index_name):
    """Fetch live data for a given index."""
    try:
        if "NIFTY" in index_name:
            logger.info(f"Fetching NIFTY data for {index_name}...")
            # Use fetch_nifty_constituents instead of nse_fno
            return fetch_nifty_constituents(index_name)
        elif index_name == "BSE 30":
            return fetch_bse_30_constituents()
        else:
            return fetch_wikipedia_constituents(index_name)
    except Exception as e:
        logger.error(f"Error fetching live data for {index_name}: {e}")
        return []

def load_fallback_data(index_name):
    """Load fallback data for a given index from JSON files."""
    try:
        file_path = os.path.join(STOCK_DATA_DIR, f"{index_name.replace(' ', '_')}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Fallback file for {index_name} not found.")
            return []
    except Exception as e:
        logger.error(f"Error loading fallback data for {index_name}: {e}")
        return []

def save_data(index_name, data):
    """Save data to a JSON file."""
    try:
        file_path = os.path.join(STOCK_DATA_DIR, f"{index_name.replace(' ', '_')}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Data for {index_name} saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data for {index_name}: {e}")

def get_data(index_name):
    """Get data for a given index, using live data or fallback as needed."""
    file_path = os.path.join(STOCK_DATA_DIR, f"{index_name.replace(' ', '_')}.json")
    if is_file_outdated(file_path, REFRESH_INTERVAL):
        logger.info(f"Fetching live data for {index_name}...")
        data = fetch_live_data(index_name)
        if data:
            save_data(index_name, data)
            return data
        else:
            logger.warning(f"Live data fetch failed for {index_name}. Using fallback data.")
    else:
        logger.info(f"Live data is up-to-date for {index_name}.")
    fallback_data = load_fallback_data(index_name)
    if not fallback_data:
        logger.error(f"No fallback data found for {index_name}.")
    return fallback_data

def refresh_all_indices():
    """Refresh data for all supported indices."""
    logger.info("Starting refresh for all indices...")
    for i, index_name in enumerate(SUPPORTED_INDICES, start=1):
        try:
            logger.info(f"[{i}/{len(SUPPORTED_INDICES)}] Refreshing data for {index_name}...")
            data = fetch_live_data(index_name)
            if data:
                save_data(index_name, data)
                logger.info(f"Data refreshed successfully for {index_name}.")
            else:
                logger.warning(f"Failed to refresh data for {index_name}.")
        except Exception as e:
            logger.error(f"Error refreshing data for {index_name}: {e}")
    logger.info("Completed refresh for all indices.")