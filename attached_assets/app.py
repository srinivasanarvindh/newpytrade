"""
PyTrade - API Gateway

This file serves as the main entry point for the PyTrade API.
It includes routes for the swing trading feature and other functionalities.

Author: PyTrade Development Team
Version: 1.0.0
Date: March 26, 2025
License: Proprietary
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import os
import json
import pandas as pd
import numpy as np
import random
import requests
from bs4 import BeautifulSoup
import traceback
import functools
import time
from datetime import datetime
# Modified imports for nsepython - removing nse_eq_symbols
from nsepython import nse_eq, indices, nsefetch, index_info, nse_get_index_quote
import yfinance as yf
from swing_trading import analyze_swing_trading, analyze_tickers
from attached_assets.indicesdownload import get_indices_list, get_index_constituents as download_index_constituents
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import os

import sys
sys.path.append('C:\\Users\\Arvindh\\Downloads\\PyTradeAnalytics')
from config import config
from PyTradeAnalytics.data_processor import DataProcessor
from PyTradeAnalytics.strategy import MovingAverageCrossover, RSIStrategy
from PyTradeAnalytics.visualizer import plot_candlestick_with_indicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """
    Create Flask application.
    
    Returns:
        Flask: Flask application
    """
    app = Flask(__name__, static_folder='static')
    CORS(app)
    
    @app.route('/')
    def home():
        """
        Home endpoint.
        """
        return send_from_directory(app.static_folder, 'index.html')
        
    @app.route('/api')
    def api_info():
        """
        API information endpoint.
        """
        return jsonify({
            "name": "PyTrade API",
            "version": "1.0.0",
            "description": "API for PyTrade platform",
            "features": [
                "Swing Trading Analysis"
            ]
        })
    
    @app.route('/swing-trading', methods=['POST'])
    @app.route('/api/swing-trading', methods=['POST'])
    def swing_trading():
        """
        API endpoint for swing trading analysis.
        
        Returns:
            JSON: Analysis results
        """
        try:
            data = request.json
            tickers = data.get('tickers', [])
            timeframe = data.get('timeframe', 'short')
            
            if not tickers:
                return jsonify({"error": "No tickers provided"}), 400
            
            results = analyze_tickers(tickers, timeframe)
            return jsonify(results)
        
        except Exception as e:
            logger.error(f"Error in swing trading endpoint: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/swing-trading/<ticker>', methods=['GET'])
    @app.route('/api/swing-trading/<ticker>', methods=['GET'])
    def swing_trading_single(ticker):
        """
        API endpoint for swing trading analysis of a single ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            JSON: Analysis results
        """
        try:
            timeframe = request.args.get('timeframe', 'short')
            result = analyze_swing_trading(ticker, timeframe)
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error in swing trading single endpoint: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Utility function for caching
    def cache_result(func):
        """
        Simple decorator for caching function results.
        """
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key not in cache:
                logger.debug(f"Cache miss for {func.__name__}, calling original function")
                result = func(*args, **kwargs)
                cache[key] = result
            else:
                logger.debug(f"Cache hit for {func.__name__}")
            return cache[key]
        
        return wrapper
    
    @cache_result
    def get_nifty_companies():
        """
        Fetch NIFTY 50 companies using NSEPython.
        
        Returns:
            list: List of company objects
        """
        try:
            logger.info("Fetching NIFTY 50 companies using NSEPython")
            
            # List of NIFTY 50 stocks - top companies in India
            nifty50_symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "HINDUNILVR", 
                "INFY", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", 
                "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI"
            ]
            
            companies = []
            
            # Try to get all NSE symbols first
            all_symbols = nse_eq_symbols()
            
            if all_symbols:
                logger.info(f"Processing NSE symbols for NIFTY 50")
                
                # Company name mappings for NIFTY 50 stocks
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
                    "MARUTI": "Maruti Suzuki India Ltd."
                }
                
                # Process symbols
                for symbol in nifty50_symbols:
                    # Generate random price data for demonstration
                    price = round(random.uniform(1000, 10000), 2)
                    change_percent = round(random.uniform(-3, 5), 2)
                    change = round(price * (change_percent / 100), 2)
                    
                    company_name = company_name_map.get(symbol, f"{symbol} Ltd.")
                    sector = "Technology" if "TECH" in symbol or "INFO" in symbol else "Finance" if "BANK" in symbol or "FIN" in symbol else "Manufacturing"
                    
                    company = {
                        "symbol": symbol,
                        "company": company_name,
                        "sector": sector,
                        "price": price,
                        "change": change,
                        "changePercent": change_percent,
                        "currency": "INR",
                        "exchange": "NSE"
                    }
                    
                    companies.append(company)
                
                logger.info(f"Successfully processed {len(companies)} NIFTY 50 companies")
            
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching NIFTY 50 companies: {e}", exc_info=True)
            return []
    
    @cache_result
    def get_sp100_companies():
        """
        Fetch S&P 100 companies.
        
        Returns:
            list: List of company objects
        """
        try:
            logger.info("Fetching S&P 100 companies")
            
            # Top companies in S&P 100
            sp100_symbols = [
                "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", 
                "META", "TSLA", "JPM", "V", "UNH", 
                "HD", "XOM", "LLY", "AVGO", "MA"
            ]
            
            companies = []
            
            # Company name mappings
            company_name_map = {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "AMZN": "Amazon.com, Inc.",
                "NVDA": "NVIDIA Corporation",
                "GOOGL": "Alphabet Inc. (Google)",
                "META": "Meta Platforms, Inc.",
                "TSLA": "Tesla, Inc.",
                "JPM": "JPMorgan Chase & Co.",
                "V": "Visa Inc.",
                "UNH": "UnitedHealth Group Inc.",
                "HD": "The Home Depot, Inc.",
                "XOM": "Exxon Mobil Corporation",
                "LLY": "Eli Lilly and Company",
                "AVGO": "Broadcom Inc.",
                "MA": "Mastercard Incorporated"
            }
            
            for symbol in sp100_symbols:
                # Generate random price data for demonstration
                price = round(random.uniform(100, 1000), 2)
                change_percent = round(random.uniform(-2, 4), 2)
                change = round(price * (change_percent / 100), 2)
                
                company_name = company_name_map.get(symbol, f"{symbol} Inc.")
                sector = "Technology" if symbol in ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AVGO"] else "Consumer Services" if symbol in ["AMZN", "HD"] else "Financials"
                
                company = {
                    "symbol": symbol,
                    "company": company_name,
                    "sector": sector,
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "currency": "USD",
                    "exchange": "NASDAQ" if symbol in ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META"] else "NYSE"
                }
                
                companies.append(company)
            
            logger.info(f"Successfully processed {len(companies)} S&P 100 companies")
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching S&P 100 companies: {e}", exc_info=True)
            return []
    
    @cache_result
    def get_dowjones_companies():
        """
        Fetch Dow Jones companies.
        
        Returns:
            list: List of company objects
        """
        try:
            logger.info("Fetching Dow Jones companies")
            
            # Top companies in Dow Jones
            dow_symbols = [
                "AAPL", "AMGN", "AXP", "BA", "CAT",
                "CRM", "CSCO", "CVX", "DIS", "DOW",
                "GS", "HD", "HON", "IBM", "INTC"
            ]
            
            companies = []
            
            # Company name mappings
            company_name_map = {
                "AAPL": "Apple Inc.",
                "AMGN": "Amgen Inc.",
                "AXP": "American Express Company",
                "BA": "The Boeing Company",
                "CAT": "Caterpillar Inc.",
                "CRM": "Salesforce, Inc.",
                "CSCO": "Cisco Systems, Inc.",
                "CVX": "Chevron Corporation",
                "DIS": "The Walt Disney Company",
                "DOW": "Dow Inc.",
                "GS": "The Goldman Sachs Group, Inc.",
                "HD": "The Home Depot, Inc.",
                "HON": "Honeywell International Inc.",
                "IBM": "International Business Machines Corporation",
                "INTC": "Intel Corporation"
            }
            
            for symbol in dow_symbols:
                # Generate random price data for demonstration
                price = round(random.uniform(50, 500), 2)
                change_percent = round(random.uniform(-1.5, 3), 2)
                change = round(price * (change_percent / 100), 2)
                
                company_name = company_name_map.get(symbol, f"{symbol} Corporation")
                
                # Assign sectors based on the symbol
                if symbol in ["AAPL", "CRM", "CSCO", "IBM", "INTC"]:
                    sector = "Technology"
                elif symbol in ["CVX", "DOW"]:
                    sector = "Energy"
                elif symbol in ["AXP", "GS"]:
                    sector = "Financials"
                elif symbol in ["BA", "CAT", "HON"]:
                    sector = "Industrials"
                elif symbol in ["AMGN"]:
                    sector = "Healthcare"
                elif symbol in ["DIS", "HD"]:
                    sector = "Consumer Discretionary"
                else:
                    sector = "Miscellaneous"
                
                company = {
                    "symbol": symbol,
                    "company": company_name,
                    "sector": sector,
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "currency": "USD",
                    "exchange": "NYSE"
                }
                
                companies.append(company)
            
            logger.info(f"Successfully processed {len(companies)} Dow Jones companies")
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching Dow Jones companies: {e}", exc_info=True)
            return []
    
    @cache_result
    def get_indices():
        """
        Fetch all available market indices using NSEPython for Indian markets
        and other sources for global markets.
        
        Returns:
            dict: Dictionary of market indices by country and region
        """
        try:
            logger.info("Fetching all NSE indices data in a single call")
            
            # Fetch NSE indices data
            try:
                # Using NSEPython to fetch all NSE indices
                nse_indices_data = None
                try:
                    nse_indices_data = indices()
                except Exception as e:
                    logger.error(f"Error fetching NSE indices data: {e}")
                
                # Fallback to NSE data from a public JSON endpoint
                if not nse_indices_data:
                    logger.info("Trying fallback NSE indices data source")
                    try:
                        nse_indices_url = "https://iislliveblob.niftyindices.com/jsonfiles/LiveIndicesWatch.json"
                        response = requests.get(nse_indices_url)
                        if response.status_code == 200:
                            nse_indices_data = response.json()
                    except Exception as e:
                        logger.error(f"Error fetching NSE indices data from fallback: {e}")
                
                if nse_indices_data:
                    logger.info(f"Successfully fetched NSE indices data")
                else:
                    logger.error(f"Failed to fetch or invalid NSE indices data")
            except Exception as e:
                logger.error(f"Error processing NSE indices: {e}")
                nse_indices_data = None
            
            # Define the market structure
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
                },
                "Europe": {
                    "UK": ["FTSE 100", "FTSE 250", "FTSE 350"],
                    "Germany": ["DAX"],
                    "France": ["CAC 40"],
                    "Switzerland": ["SMI"],
                    "Other European": ["STOXX Europe 50", "EURO STOXX 50"]
                },
                "Asia Pacific": {
                    "Japan": ["Nikkei 225", "TOPIX"],
                    "China": ["Shanghai Composite", "SZSE Component", "Hang Seng"],
                    "South Korea": ["KOSPI"],
                    "Australia": ["S&P/ASX 200"],
                    "Other Asian": ["FTSE Asia Pacific", "MSCI AC Asia Pacific"]
                }
            }
            
            # Generate index data for all markets
            all_indices = {}
            
            for country, exchanges in markets.items():
                country_indices = {}
                
                for exchange, indices_list in exchanges.items():
                    exchange_indices = []
                    
                    for index_name in indices_list:
                        # Try to get data from NSE source for Indian markets
                        if country == "India" and exchange == "NSE" and nse_indices_data:
                            try:
                                # Process NSE data
                                index_data = None
                                
                                # Different structure handling based on data source
                                if isinstance(nse_indices_data, list):
                                    # Process list structure
                                    for item in nse_indices_data:
                                        if item.get("name", "").lower() == index_name.lower() or item.get("indexName", "").lower() == index_name.lower():
                                            index_data = {
                                                "name": index_name,
                                                "value": item.get("last", item.get("lastPrice", 0)),
                                                "change": item.get("change", 0),
                                                "changePercent": item.get("pChange", item.get("percentChange", 0)),
                                                "isUp": float(item.get("change", 0)) > 0
                                            }
                                            break
                                elif isinstance(nse_indices_data, dict) and "data" in nse_indices_data:
                                    # Process dict structure with data field
                                    for item in nse_indices_data["data"]:
                                        if item.get("name", "").lower() == index_name.lower() or item.get("indexName", "").lower() == index_name.lower():
                                            index_data = {
                                                "name": index_name,
                                                "value": item.get("last", item.get("lastPrice", 0)),
                                                "change": item.get("change", 0),
                                                "changePercent": item.get("pChange", item.get("percentChange", 0)),
                                                "isUp": float(item.get("change", 0)) > 0
                                            }
                                            break
                                
                                # If we didn't find the index in NSE data, create a placeholder
                                if not index_data:
                                    logger.warning(f"Index {index_name} not found in NSE data, using placeholder")
                                    
                                    # For special indices like VIX
                                    if index_name == "Nifty VIX":
                                        index_data = {
                                            "name": index_name,
                                            "value": round(random.uniform(12, 20), 2),  # VIX values typically range from 10-30
                                            "change": round(random.uniform(-1, 1), 2),
                                            "changePercent": round(random.uniform(-5, 5), 2),
                                            "isUp": random.choice([True, False]),
                                            "description": "India VIX is India's volatility index that measures the degree of volatility or fluctuation expected by the Nifty50 over the next 30 days."
                                        }
                                    elif index_name == "GIFT Nifty":
                                        index_data = {
                                            "name": index_name,
                                            "value": round(random.uniform(22000, 23000), 2),  # GIFT Nifty follows NIFTY 50
                                            "change": round(random.uniform(-100, 100), 2),
                                            "changePercent": round(random.uniform(-1, 1), 2),
                                            "isUp": random.choice([True, False]),
                                            "description": "GIFT Nifty is a futures contract on the NSE Nifty50 Index, traded at the GIFT City in Gujarat."
                                        }
                                    else:
                                        index_data = {
                                            "name": index_name,
                                            "value": round(random.uniform(10000, 25000), 2),
                                            "change": round(random.uniform(-150, 150), 2),
                                            "changePercent": round(random.uniform(-1, 1), 2),
                                            "isUp": random.choice([True, False])
                                        }
                            except Exception as e:
                                logger.error(f"Error processing NSE data for {index_name}: {e}")
                                index_data = None
                        
                        # For other markets or if NSE data failed, create data with reasonable ranges
                        if not index_data:
                            # Generate realistic ranges based on the index
                            if "NIFTY" in index_name or "NSE" in index_name:
                                base_value = random.uniform(18000, 22000)
                            elif "BSE" in index_name or "SENSEX" in index_name:
                                base_value = random.uniform(60000, 70000)
                            elif "Dow" in index_name:
                                base_value = random.uniform(38000, 40000)
                            elif "S&P" in index_name:
                                base_value = random.uniform(5000, 5500)
                            elif "NASDAQ" in index_name:
                                base_value = random.uniform(16000, 18000)
                            elif "DAX" in index_name:
                                base_value = random.uniform(17000, 18000)
                            elif "FTSE" in index_name:
                                base_value = random.uniform(7500, 8000)
                            elif "Nikkei" in index_name:
                                base_value = random.uniform(38000, 40000)
                            elif "Shanghai" in index_name:
                                base_value = random.uniform(3000, 3500)
                            elif "Hang Seng" in index_name:
                                base_value = random.uniform(16000, 18000)
                            else:
                                base_value = random.uniform(1000, 10000)
                            
                            # Generate change values proportional to the index value
                            change_pct = random.uniform(-1.0, 1.0)
                            change_abs = base_value * change_pct / 100
                            
                            index_data = {
                                "name": index_name,
                                "value": round(base_value, 2),
                                "change": round(change_abs, 2),
                                "changePercent": round(change_pct, 2),
                                "isUp": change_pct > 0
                            }
                        
                        exchange_indices.append(index_data)
                    
                    country_indices[exchange] = exchange_indices
                
                all_indices[country] = country_indices
            
            return all_indices
            
        except Exception as e:
            logger.error(f"Error in get_indices: {e}", exc_info=True)
            return {}

    @cache_result
    def get_index_constituents(index_name):
        """
        Fetch constituents for a given index.
        
        Args:
            index_name (str): Name of the index
            
        Returns:
            list: List of constituent companies
        """
        try:
            logger.info(f"Fetching constituents for {index_name}")
            constituents = []
            constituents_metadata = {}
            
            # List of NIFTY indices
            nifty_indices = [
                "NIFTY 50", "NIFTY Next 50", "NIFTY 100", "NIFTY 200",
                "NIFTY 500", "NIFTY Midcap 50", "NIFTY Midcap 100",
                "NIFTY Smallcap 50", "NIFTY Smallcap 100", "NIFTY Smallcap 250",
                "NIFTY Bank", "NIFTY IT", "NIFTY Auto", "NIFTY Financial Services",
                "NIFTY FMCG", "NIFTY Healthcare", "NIFTY Media", "NIFTY Metal",
                "NIFTY Pharma", "NIFTY PSU Bank", "NIFTY Realty", 
                "Nifty VIX", "GIFT Nifty"
            ]
            
            # List of BSE indices
            bse_indices = [
                "S&P BSE - 30", "S&P BSE - 100", "S&P BSE - 200", "S&P BSE - 500",
                "S&P BSE MidCap", "S&P BSE SmallCap", "S&P BSE Auto",
                "S&P BSE Bankex", "S&P BSE Capital Goods", "S&P BSE Consumer Durables",
                "S&P BSE FMCG", "S&P BSE Healthcare", "S&P BSE IT", "S&P BSE Metal",
                "S&P BSE Oil & Gas", "S&P BSE Power", "S&P BSE Realty", "S&P BSE Teck"
            ]
            
            if index_name in nifty_indices:
                try:
                    logger.info(f"Fetching constituents for {index_name} using NSEPython")
                    
                    # For NIFTY 50, we'll use nse_eq_symbols to get all NSE stocks 
                    # and filter for the top/large-cap companies
                    if index_name == "NIFTY 50":
                        logger.info("Fetching NIFTY 50 constituents")
                        
                        # List of NIFTY 50 stocks
                        nifty50_symbols = [
                            "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "HINDUNILVR", 
                            "INFY", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", 
                            "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI"
                        ]
                        
                        # Add metadata for the index
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "NSE",
                            "description": "NIFTY 50 is the flagship index on the National Stock Exchange of India Ltd. (NSE). The Index tracks the behavior of a portfolio of blue chip companies, the largest and most liquid Indian securities.",
                            "count": len(nifty50_symbols)
                        }
                        
                        # Company name mapping
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
                            "MARUTI": "Maruti Suzuki India Ltd."
                        }
                        
                        # Process each symbol
                        for symbol in nifty50_symbols:
                            # Generate price data
                            price = round(random.uniform(1000, 10000), 2)
                            change_percent = round(random.uniform(-3, 5), 2)
                            change = round(price * (change_percent / 100), 2)
                            
                            company_name = company_name_map.get(symbol, f"{symbol} Ltd.")
                            sector = "Technology" if "TECH" in symbol or "INFO" in symbol else "Finance" if "BANK" in symbol or "FIN" in symbol else "Manufacturing"
                            
                            company = {
                                "symbol": symbol,
                                "company": company_name,
                                "sector": sector,
                                "price": price,
                                "change": change,
                                "changePercent": change_percent,
                                "currency": "INR",
                                "exchange": "NSE"
                            }
                            
                            constituents.append(company)
                        
                    # Special case for Nifty Bank
                    elif index_name == "NIFTY Bank":
                        logger.info("Fetching NIFTY Bank constituents")
                        
                        bank_symbols = [
                            "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK",
                            "INDUSINDBK", "BANKBARODA", "FEDERALBNK", "PNB", "IDFCFIRSTB"
                        ]
                        
                        # Add metadata for the index
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "NSE",
                            "description": "NIFTY Bank Index is designed to reflect the behavior and performance of the Indian banking sector. The index comprises the most liquid Indian Banking stocks.",
                            "count": len(bank_symbols)
                        }
                        
                        company_name_map = {
                            "HDFCBANK": "HDFC Bank Ltd.",
                            "ICICIBANK": "ICICI Bank Ltd.",
                            "KOTAKBANK": "Kotak Mahindra Bank Ltd.",
                            "SBIN": "State Bank of India",
                            "AXISBANK": "Axis Bank Ltd.",
                            "INDUSINDBK": "IndusInd Bank Ltd.",
                            "BANKBARODA": "Bank of Baroda",
                            "FEDERALBNK": "Federal Bank Ltd.",
                            "PNB": "Punjab National Bank",
                            "IDFCFIRSTB": "IDFC First Bank Ltd."
                        }
                        
                        for symbol in bank_symbols:
                            price = round(random.uniform(200, 2000), 2)
                            change_percent = round(random.uniform(-3, 5), 2)
                            change = round(price * (change_percent / 100), 2)
                            
                            company = {
                                "symbol": symbol,
                                "company": company_name_map.get(symbol, f"{symbol} Bank"),
                                "sector": "Banking",
                                "price": price,
                                "change": change,
                                "changePercent": change_percent,
                                "currency": "INR",
                                "exchange": "NSE"
                            }
                            
                            constituents.append(company)
                    
                    # Special case for Nifty VIX and GIFT Nifty - not regular indices with constituents
                    elif index_name in ["Nifty VIX", "GIFT Nifty"]:
                        logger.info(f"{index_name} is a special index without constituents")
                        # Create placeholder data (since VIX doesn't have real constituents)
                        us_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "NFLX"]
                        us_names = {
                            "AAPL": "Apple Inc.",
                            "MSFT": "Microsoft Corporation",
                            "GOOGL": "Alphabet Inc.",
                            "AMZN": "Amazon.com, Inc.",
                            "META": "Meta Platforms, Inc.",
                            "TSLA": "Tesla, Inc.",
                            "NVDA": "NVIDIA Corporation",
                            "JPM": "JPMorgan Chase & Co.",
                            "V": "Visa Inc.",
                            "NFLX": "Netflix, Inc."
                        }
                        
                        for symbol in us_symbols:
                            company = {
                                "symbol": symbol,
                                "company": us_names.get(symbol, symbol)
                            }
                            constituents.append(company)
                    
                    # For NIFTY IT
                    elif index_name == "NIFTY IT":
                        logger.info("Fetching NIFTY IT constituents")
                        
                        it_symbols = [
                            "TCS", "INFY", "HCLTECH", "TECHM", "WIPRO",
                            "LTI", "MINDTREE", "COFORGE", "MPHASIS", "LTTS"
                        ]
                        
                        # Add metadata for the index
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "NSE",
                            "description": "NIFTY IT Index is designed to reflect the behavior of IT companies. The index comprises top IT companies listed on the NSE, representing the Indian IT sector.",
                            "count": len(it_symbols)
                        }
                        
                        company_name_map = {
                            "TCS": "Tata Consultancy Services Ltd.",
                            "INFY": "Infosys Ltd.",
                            "HCLTECH": "HCL Technologies Ltd.",
                            "TECHM": "Tech Mahindra Ltd.",
                            "WIPRO": "Wipro Ltd.",
                            "LTI": "Larsen & Toubro Infotech Ltd.",
                            "MINDTREE": "Mindtree Ltd.",
                            "COFORGE": "Coforge Ltd.",
                            "MPHASIS": "Mphasis Ltd.",
                            "LTTS": "L&T Technology Services Ltd."
                        }
                        
                        for symbol in it_symbols:
                            price = round(random.uniform(500, 4000), 2)
                            change_percent = round(random.uniform(-3, 5), 2)
                            change = round(price * (change_percent / 100), 2)
                            
                            company = {
                                "symbol": symbol,
                                "company": company_name_map.get(symbol, f"{symbol} Technologies"),
                                "sector": "IT Services",
                                "price": price,
                                "change": change,
                                "changePercent": change_percent,
                                "currency": "INR",
                                "exchange": "NSE"
                            }
                            
                            constituents.append(company)
                            
                    # Handle other NSE indices
                    else:
                        logger.info(f"Using fallback data for {index_name}")
                        # For other NSE indices, create placeholder data
                        constituents = []
                        # Add sector-specific companies based on the index
                        
                except Exception as e:
                    logger.error(f"Error fetching NSE index constituents for {index_name}: {e}", exc_info=True)
                    
            # For BSE indices
            elif index_name in bse_indices:
                try:
                    logger.info(f"Fetching constituents for {index_name} using BSE data")
                    
                    if index_name == "S&P BSE - 30":
                        # Add metadata for BSE 30 (SENSEX)
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "BSE",
                            "description": "S&P BSE SENSEX is a free-float market-weighted stock market index of 30 well-established and financially sound companies listed on the Bombay Stock Exchange.",
                            "count": 30
                        }
                        
                        # BSE 30 (SENSEX) companies
                        bse30_companies = [
                            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2500, "change": 35, "changePercent": 1.4, "currency": "INR", "sector": "Energy"},
                            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3400, "change": -50, "changePercent": -1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1600, "change": 12, "changePercent": 0.8, "currency": "INR", "sector": "Banking"},
                            {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "price": 1700, "change": 25, "changePercent": 1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 930, "change": 15, "changePercent": 1.6, "currency": "INR", "sector": "Banking"},
                            {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "price": 2400, "change": -18, "changePercent": -0.8, "currency": "INR", "sector": "FMCG"},
                            {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "exchange": "BSE", "price": 1080, "change": 12, "changePercent": 1.4, "currency": "INR", "sector": "Telecom"},
                            {"symbol": "BAJFINANCE", "company": "Bajaj Finance Ltd.", "exchange": "BSE", "price": 6900, "change": 80, "changePercent": 1.2, "currency": "INR", "sector": "Finance"},
                            {"symbol": "SBIN", "company": "State Bank of India", "exchange": "BSE", "price": 650, "change": 10, "changePercent": 1.5, "currency": "INR", "sector": "Banking"},
                            {"symbol": "HCLTECH", "company": "HCL Technologies Ltd.", "exchange": "BSE", "price": 1320, "change": 18, "changePercent": 1.4, "currency": "INR", "sector": "IT"}
                        ]
                        constituents = bse30_companies
                        
                    elif index_name == "S&P BSE - 100":
                        # Add metadata for BSE 100
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "BSE",
                            "description": "S&P BSE 100 is a broad-based index designed to measure the performance of the top 100 companies in India based on size and liquidity across diverse sectors.",
                            "count": 100
                        }
                        
                        # Similar to BSE 30 but with more companies
                        bse100_companies = [
                            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2500, "change": 35, "changePercent": 1.4, "currency": "INR", "sector": "Energy"},
                            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3400, "change": -50, "changePercent": -1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1600, "change": 12, "changePercent": 0.8, "currency": "INR", "sector": "Banking"},
                            {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "price": 1700, "change": 25, "changePercent": 1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 930, "change": 15, "changePercent": 1.6, "currency": "INR", "sector": "Banking"},
                            {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "price": 2400, "change": -18, "changePercent": -0.8, "currency": "INR", "sector": "FMCG"},
                            {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "exchange": "BSE", "price": 1080, "change": 12, "changePercent": 1.4, "currency": "INR", "sector": "Telecom"},
                            {"symbol": "BAJFINANCE", "company": "Bajaj Finance Ltd.", "exchange": "BSE", "price": 6900, "change": 80, "changePercent": 1.2, "currency": "INR", "sector": "Finance"},
                            {"symbol": "SBIN", "company": "State Bank of India", "exchange": "BSE", "price": 650, "change": 10, "changePercent": 1.5, "currency": "INR", "sector": "Banking"},
                            {"symbol": "HCLTECH", "company": "HCL Technologies Ltd.", "exchange": "BSE", "price": 1320, "change": 18, "changePercent": 1.4, "currency": "INR", "sector": "IT"},
                            {"symbol": "ASIANPAINT", "company": "Asian Paints Ltd.", "exchange": "BSE", "price": 3200, "change": 42, "changePercent": 1.3, "currency": "INR", "sector": "Consumer"},
                            {"symbol": "AXISBANK", "company": "Axis Bank Ltd.", "exchange": "BSE", "price": 950, "change": 15, "changePercent": 1.6, "currency": "INR", "sector": "Banking"},
                            {"symbol": "BAJAJFINSV", "company": "Bajaj Finserv Ltd.", "exchange": "BSE", "price": 1585, "change": 30, "changePercent": 1.9, "currency": "INR", "sector": "Finance"},
                            {"symbol": "KOTAKBANK", "company": "Kotak Mahindra Bank Ltd.", "exchange": "BSE", "price": 1850, "change": 25, "changePercent": 1.4, "currency": "INR", "sector": "Banking"},
                            {"symbol": "MARUTI", "company": "Maruti Suzuki India Ltd.", "exchange": "BSE", "price": 10500, "change": 125, "changePercent": 1.2, "currency": "INR", "sector": "Auto"},
                            {"symbol": "LT", "company": "Larsen & Toubro Ltd.", "exchange": "BSE", "price": 2700, "change": 35, "changePercent": 1.3, "currency": "INR", "sector": "Construction"},
                            {"symbol": "ONGC", "company": "Oil and Natural Gas Corporation Ltd.", "exchange": "BSE", "price": 240, "change": 3.5, "changePercent": 1.5, "currency": "INR", "sector": "Energy"},
                            {"symbol": "POWERGRID", "company": "Power Grid Corporation of India Ltd.", "exchange": "BSE", "price": 265, "change": 4, "changePercent": 1.5, "currency": "INR", "sector": "Power"},
                            {"symbol": "SUNPHARMA", "company": "Sun Pharmaceutical Industries Ltd.", "exchange": "BSE", "price": 1050, "change": 15, "changePercent": 1.5, "currency": "INR", "sector": "Pharmaceuticals"},
                            {"symbol": "TATAMOTORS", "company": "Tata Motors Ltd.", "exchange": "BSE", "price": 820, "change": 12, "changePercent": 1.5, "currency": "INR", "sector": "Auto"},
                            {"symbol": "TATASTEEL", "company": "Tata Steel Ltd.", "exchange": "BSE", "price": 135, "change": 2, "changePercent": 1.5, "currency": "INR", "sector": "Metals"},
                            {"symbol": "TECHM", "company": "Tech Mahindra Ltd.", "exchange": "BSE", "price": 1250, "change": 20, "changePercent": 1.6, "currency": "INR", "sector": "IT"},
                            {"symbol": "TITAN", "company": "Titan Company Ltd.", "exchange": "BSE", "price": 2950, "change": 40, "changePercent": 1.4, "currency": "INR", "sector": "Consumer"},
                            {"symbol": "ULTRACEMCO", "company": "UltraTech Cement Ltd.", "exchange": "BSE", "price": 8800, "change": 120, "changePercent": 1.4, "currency": "INR", "sector": "Cement"},
                            {"symbol": "WIPRO", "company": "Wipro Ltd.", "exchange": "BSE", "price": 425, "change": 6, "changePercent": 1.4, "currency": "INR", "sector": "IT"},
                            {"symbol": "ZEEL", "company": "Zee Entertainment Enterprises Ltd.", "exchange": "BSE", "price": 290, "change": 5, "changePercent": 1.8, "currency": "INR", "sector": "Media"},
                            {"symbol": "ADANIPORTS", "company": "Adani Ports and Special Economic Zone Ltd.", "exchange": "BSE", "price": 915, "change": 15, "changePercent": 1.7, "currency": "INR", "sector": "Infrastructure"},
                            {"symbol": "COALINDIA", "company": "Coal India Ltd.", "exchange": "BSE", "price": 350, "change": 6, "changePercent": 1.7, "currency": "INR", "sector": "Mining"},
                            {"symbol": "DRREDDY", "company": "Dr. Reddy's Laboratories Ltd.", "exchange": "BSE", "price": 5400, "change": 80, "changePercent": 1.5, "currency": "INR", "sector": "Pharmaceuticals"},
                            {"symbol": "GRASIM", "company": "Grasim Industries Ltd.", "exchange": "BSE", "price": 2150, "change": 35, "changePercent": 1.7, "currency": "INR", "sector": "Diversified"},
                            {"symbol": "HEROMOTOCO", "company": "Hero MotoCorp Ltd.", "exchange": "BSE", "price": 3350, "change": 45, "changePercent": 1.4, "currency": "INR", "sector": "Auto"},
                            {"symbol": "HINDALCO", "company": "Hindalco Industries Ltd.", "exchange": "BSE", "price": 530, "change": 9, "changePercent": 1.7, "currency": "INR", "sector": "Metals"},
                            {"symbol": "INDUSINDBK", "company": "IndusInd Bank Ltd.", "exchange": "BSE", "price": 1440, "change": 25, "changePercent": 1.8, "currency": "INR", "sector": "Banking"},
                            {"symbol": "JSWSTEEL", "company": "JSW Steel Ltd.", "exchange": "BSE", "price": 870, "change": 15, "changePercent": 1.8, "currency": "INR", "sector": "Metals"},
                            {"symbol": "M&M", "company": "Mahindra & Mahindra Ltd.", "exchange": "BSE", "price": 1520, "change": 25, "changePercent": 1.7, "currency": "INR", "sector": "Auto"}
                        ]
                        constituents = bse100_companies[:35]  # Limit to 35 companies
                        
                    elif index_name == "S&P BSE - 200":
                        # Add metadata for BSE 200
                        constituents_metadata = {
                            "index": index_name,
                            "market": "India",
                            "currency": "INR",
                            "exchange": "BSE",
                            "description": "S&P BSE 200 represents the top 200 companies listed on BSE Ltd., providing a broader spectrum of the Indian equity market across various sectors.",
                            "count": 200
                        }
                        
                        # Build on BSE 100
                        # Same data as for BSE 100 but with more companies (simplified)
                        bse200_companies = [
                            {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2500, "change": 35, "changePercent": 1.4, "currency": "INR", "sector": "Energy"},
                            {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3400, "change": -50, "changePercent": -1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1600, "change": 12, "changePercent": 0.8, "currency": "INR", "sector": "Banking"},
                            {"symbol": "INFY", "company": "Infosys Ltd.", "exchange": "BSE", "price": 1700, "change": 25, "changePercent": 1.5, "currency": "INR", "sector": "IT"},
                            {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 930, "change": 15, "changePercent": 1.6, "currency": "INR", "sector": "Banking"},
                            {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "price": 2400, "change": -18, "changePercent": -0.8, "currency": "INR", "sector": "FMCG"},
                            {"symbol": "BHARTIARTL", "company": "Bharti Airtel Ltd.", "exchange": "BSE", "price": 1080, "change": 12, "changePercent": 1.4, "currency": "INR", "sector": "Telecom"},
                            {"symbol": "BAJFINANCE", "company": "Bajaj Finance Ltd.", "exchange": "BSE", "price": 6900, "change": 80, "changePercent": 1.2, "currency": "INR", "sector": "Finance"},
                            # Add more companies
                            {"symbol": "AMBUJACEM", "company": "Ambuja Cements Ltd.", "exchange": "BSE", "price": 585.45, "change": 6.85, "changePercent": 1.18, "currency": "INR", "sector": "Materials"},
                            {"symbol": "AUROPHARMA", "company": "Aurobindo Pharma Ltd.", "exchange": "BSE", "price": 1135.70, "change": 14.55, "changePercent": 1.30, "currency": "INR", "sector": "Healthcare"},
                            {"symbol": "BAJAJHLDNG", "company": "Bajaj Holdings & Investment Ltd.", "exchange": "BSE", "price": 7540.25, "change": 85.35, "changePercent": 1.14, "currency": "INR", "sector": "Financials"},
                            {"symbol": "BANKBARODA", "company": "Bank of Baroda", "exchange": "BSE", "price": 235.45, "change": 3.25, "changePercent": 1.40, "currency": "INR", "sector": "Financials"},
                            {"symbol": "BIOCON", "company": "Biocon Ltd.", "exchange": "BSE", "price": 315.80, "change": 4.25, "changePercent": 1.36, "currency": "INR", "sector": "Healthcare"},
                            {"symbol": "CHOLAFIN", "company": "Cholamandalam Investment and Finance Company Ltd.", "exchange": "BSE", "price": 1245.35, "change": 16.80, "changePercent": 1.37, "currency": "INR", "sector": "Financials"},
                            {"symbol": "DABUR", "company": "Dabur India Ltd.", "exchange": "BSE", "price": 535.65, "change": 6.35, "changePercent": 1.20, "currency": "INR", "sector": "Consumer Staples"},
                            {"symbol": "ESCORTS", "company": "Escorts Kubota Ltd.", "exchange": "BSE", "price": 3185.45, "change": 42.30, "changePercent": 1.35, "currency": "INR", "sector": "Industrials"},
                            {"symbol": "FEDERALBNK", "company": "The Federal Bank Ltd.", "exchange": "BSE", "price": 145.90, "change": 1.95, "changePercent": 1.35, "currency": "INR", "sector": "Financials"},
                            {"symbol": "GODREJCP", "company": "Godrej Consumer Products Ltd.", "exchange": "BSE", "price": 1035.55, "change": 13.80, "changePercent": 1.35, "currency": "INR", "sector": "Consumer Staples"},
                            {"symbol": "HAVELLS", "company": "Havells India Ltd.", "exchange": "BSE", "price": 1355.75, "change": 18.10, "changePercent": 1.35, "currency": "INR", "sector": "Industrials"},
                            {"symbol": "HDFCAMC", "company": "HDFC Asset Management Company Ltd.", "exchange": "BSE", "price": 2845.30, "change": 38.00, "changePercent": 1.35, "currency": "INR", "sector": "Financials"},
                            {"symbol": "INDIGO", "company": "InterGlobe Aviation Ltd.", "exchange": "BSE", "price": 2655.40, "change": 35.45, "changePercent": 1.35, "currency": "INR", "sector": "Industrials"},
                            {"symbol": "JINDALSTEL", "company": "Jindal Steel & Power Ltd.", "exchange": "BSE", "price": 756.30, "change": 10.10, "changePercent": 1.35, "currency": "INR", "sector": "Materials"},
                            {"symbol": "JUBLFOOD", "company": "Jubilant FoodWorks Ltd.", "exchange": "BSE", "price": 535.25, "change": 7.15, "changePercent": 1.35, "currency": "INR", "sector": "Consumer Discretionary"},
                            {"symbol": "LUPIN", "company": "Lupin Ltd.", "exchange": "BSE", "price": 1245.65, "change": 16.65, "changePercent": 1.35, "currency": "INR", "sector": "Healthcare"},
                            {"symbol": "MUTHOOTFIN", "company": "Muthoot Finance Ltd.", "exchange": "BSE", "price": 1435.55, "change": 19.20, "changePercent": 1.35, "currency": "INR", "sector": "Financials"},
                            {"symbol": "NMDC", "company": "NMDC Ltd.", "exchange": "BSE", "price": 155.35, "change": 2.10, "changePercent": 1.37, "currency": "INR", "sector": "Materials"},
                            {"symbol": "NTPC", "company": "NTPC Ltd.", "exchange": "BSE", "price": 276.45, "change": 3.70, "changePercent": 1.36, "currency": "INR", "sector": "Utilities"},
                            {"symbol": "PIDILITIND", "company": "Pidilite Industries Ltd.", "exchange": "BSE", "price": 2535.85, "change": 33.95, "changePercent": 1.36, "currency": "INR", "sector": "Materials"},
                            {"symbol": "PNB", "company": "Punjab National Bank", "exchange": "BSE", "price": 86.35, "change": 1.15, "changePercent": 1.35, "currency": "INR", "sector": "Financials"},
                            {"symbol": "SBILIFE", "company": "SBI Life Insurance Company Ltd.", "exchange": "BSE", "price": 1355.45, "change": 18.15, "changePercent": 1.36, "currency": "INR", "sector": "Financials"}
                        ]
                        constituents = bse200_companies[:40]  # Limit to 40 companies
                    else:
                        # For other BSE indices, default to using a subset of the above
                        constituents = []
                        
                except Exception as e:
                    logger.error(f"Error fetching BSE index constituents for {index_name}: {e}", exc_info=True)
                    constituents = []
                    
            # For US indices
            elif index_name in ["S&P 100", "S&P 500", "Dow Jones Industrial Average", "NASDAQ-100", "NASDAQ Composite"]:
                try:
                    logger.info(f"Fetching constituents for {index_name}")
                    
                    if index_name == "S&P 100":
                        # Top companies in S&P 100
                        sp100_symbols = [
                            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", 
                            "META", "TSLA", "JPM", "V", "UNH", 
                            "HD", "XOM", "LLY", "AVGO", "MA"
                        ]
                        
                        # Company name mappings
                        company_name_map = {
                            "AAPL": "Apple Inc.",
                            "MSFT": "Microsoft Corporation",
                            "AMZN": "Amazon.com, Inc.",
                            "NVDA": "NVIDIA Corporation",
                            "GOOGL": "Alphabet Inc. (Google)",
                            "META": "Meta Platforms, Inc.",
                            "TSLA": "Tesla, Inc.",
                            "JPM": "JPMorgan Chase & Co.",
                            "V": "Visa Inc.",
                            "UNH": "UnitedHealth Group Inc.",
                            "HD": "The Home Depot, Inc.",
                            "XOM": "Exxon Mobil Corporation",
                            "LLY": "Eli Lilly and Company",
                            "AVGO": "Broadcom Inc.",
                            "MA": "Mastercard Incorporated"
                        }
                        
                        constituents = []
                        constituents_metadata = {
                            "index": index_name,
                            "market": "US",
                            "currency": "USD",
                            "exchange": "NYSE/NASDAQ",
                            "description": "The S&P 100 Index is a stock market index of United States stocks maintained by Standard & Poor's.",
                            "count": len(sp100_symbols)
                        }
                        
                        for symbol in sp100_symbols:
                            # Generate price data for demonstration
                            price = round(random.uniform(100, 1000), 2)
                            change_percent = round(random.uniform(-2, 4), 2)
                            change = round(price * (change_percent / 100), 2)
                            
                            company_name = company_name_map.get(symbol, f"{symbol} Inc.")
                            sector = "Technology" if symbol in ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AVGO"] else "Consumer Services" if symbol in ["AMZN", "HD"] else "Financials"
                            
                            company = {
                                "symbol": symbol,
                                "company": company_name,
                                "sector": sector,
                                "price": price,
                                "change": change,
                                "changePercent": change_percent,
                                "currency": "USD",
                                "exchange": "NASDAQ" if symbol in ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META"] else "NYSE"
                            }
                            
                            constituents.append(company)
                    
                    elif index_name == "Dow Jones Industrial Average":
                        # Top companies in Dow Jones
                        dow_symbols = [
                            "AAPL", "AMGN", "AXP", "BA", "CAT",
                            "CRM", "CSCO", "CVX", "DIS", "DOW",
                            "GS", "HD", "HON", "IBM", "INTC"
                        ]
                        
                        # Company name mappings
                        company_name_map = {
                            "AAPL": "Apple Inc.",
                            "AMGN": "Amgen Inc.",
                            "AXP": "American Express Company",
                            "BA": "The Boeing Company",
                            "CAT": "Caterpillar Inc.",
                            "CRM": "Salesforce, Inc.",
                            "CSCO": "Cisco Systems, Inc.",
                            "CVX": "Chevron Corporation",
                            "DIS": "The Walt Disney Company",
                            "DOW": "Dow Inc.",
                            "GS": "The Goldman Sachs Group, Inc.",
                            "HD": "The Home Depot, Inc.",
                            "HON": "Honeywell International Inc.",
                            "IBM": "International Business Machines Corporation",
                            "INTC": "Intel Corporation"
                        }
                        
                        constituents = []
                        constituents_metadata = {
                            "index": index_name,
                            "market": "US",
                            "currency": "USD",
                            "exchange": "NYSE/NASDAQ",
                            "description": "The Dow Jones Industrial Average is a stock market index that measures the stock performance of 30 large companies listed on stock exchanges in the United States.",
                            "count": len(dow_symbols)
                        }
                        
                        for symbol in dow_symbols:
                            # Generate price data for demonstration
                            price = round(random.uniform(50, 500), 2)
                            change_percent = round(random.uniform(-1.5, 3), 2)
                            change = round(price * (change_percent / 100), 2)
                            
                            company_name = company_name_map.get(symbol, f"{symbol} Corporation")
                            
                            # Assign sectors based on the symbol
                            if symbol in ["AAPL", "CRM", "CSCO", "IBM", "INTC"]:
                                sector = "Technology"
                            elif symbol in ["CVX", "DOW"]:
                                sector = "Energy"
                            elif symbol in ["AXP", "GS"]:
                                sector = "Financials"
                            elif symbol in ["BA", "CAT", "HON"]:
                                sector = "Industrials"
                            elif symbol in ["AMGN"]:
                                sector = "Healthcare"
                            elif symbol in ["DIS", "HD"]:
                                sector = "Consumer Discretionary"
                            else:
                                sector = "Miscellaneous"
                            
                            company = {
                                "symbol": symbol,
                                "company": company_name,
                                "sector": sector,
                                "price": price,
                                "change": change,
                                "changePercent": change_percent,
                                "currency": "USD",
                                "exchange": "NYSE" if symbol not in ["AAPL", "CSCO", "INTC", "AMGN"] else "NASDAQ"
                            }
                            
                            constituents.append(company)
                    
                    # Similar implementations for NASDAQ 100 and S&P 500
                    else:
                        logger.info(f"Using placeholder data for {index_name}")
                        constituents = []
                    
                except Exception as e:
                    logger.error(f"Error fetching US index constituents for {index_name}: {e}", exc_info=True)
                    constituents = []
            
            # Australian indices
            elif index_name == "S&P/ASX 200":
                try:
                    logger.info("Fetching S&P/ASX 200 constituents")
                    
                    # Top Australian companies in the S&P/ASX 200
                    asx200_symbols = [
                        "BHP.AX", "CBA.AX", "CSL.AX", "NAB.AX", "WBC.AX",
                        "ANZ.AX", "WES.AX", "WOW.AX", "MQG.AX", "TLS.AX",
                        "RIO.AX", "FMG.AX", "TCL.AX", "NCM.AX", "QAN.AX"
                    ]
                    
                    # Company name mappings
                    company_name_map = {
                        "BHP.AX": "BHP Group Ltd",
                        "CBA.AX": "Commonwealth Bank of Australia",
                        "CSL.AX": "CSL Limited",
                        "NAB.AX": "National Australia Bank Ltd",
                        "WBC.AX": "Westpac Banking Corporation",
                        "ANZ.AX": "Australia and New Zealand Banking Group Ltd",
                        "WES.AX": "Wesfarmers Ltd",
                        "WOW.AX": "Woolworths Group Ltd",
                        "MQG.AX": "Macquarie Group Ltd",
                        "TLS.AX": "Telstra Corporation Ltd",
                        "RIO.AX": "Rio Tinto Ltd",
                        "FMG.AX": "Fortescue Metals Group Ltd",
                        "TCL.AX": "Transurban Group",
                        "NCM.AX": "Newcrest Mining Ltd",
                        "QAN.AX": "Qantas Airways Ltd"
                    }
                    
                    # Sector mappings
                    sector_map = {
                        "BHP.AX": "Materials",
                        "CBA.AX": "Financials",
                        "CSL.AX": "Healthcare",
                        "NAB.AX": "Financials",
                        "WBC.AX": "Financials",
                        "ANZ.AX": "Financials",
                        "WES.AX": "Consumer Staples",
                        "WOW.AX": "Consumer Staples",
                        "MQG.AX": "Financials",
                        "TLS.AX": "Communication Services",
                        "RIO.AX": "Materials",
                        "FMG.AX": "Materials",
                        "TCL.AX": "Industrials",
                        "NCM.AX": "Materials",
                        "QAN.AX": "Industrials"
                    }
                    
                    for symbol in asx200_symbols:
                        price = round(random.uniform(10, 150) if "BHP" not in symbol and "CBA" not in symbol else random.uniform(80, 150), 2)
                        change_percent = round(random.uniform(-2, 3), 2)
                        change = round(price * (change_percent / 100), 2)
                        
                        company = {
                            "symbol": symbol,
                            "company": company_name_map.get(symbol, f"{symbol} Company"),
                            "sector": sector_map.get(symbol, "Other"),
                            "price": price,
                            "change": change,
                            "changePercent": change_percent,
                            "currency": "AUD",
                            "exchange": "ASX"
                        }
                        
                        constituents.append(company)
                    
                    constituents_metadata = {
                        "count": len(constituents),
                        "total_market_cap": "AUD 2.5 trillion",
                        "last_rebalance": "March 15, 2025",
                        "source": "S&P Dow Jones Indices"
                    }
                    
                except Exception as e:
                    logger.error(f"Error fetching ASX index constituents: {e}", exc_info=True)
                    constituents = []
                    
            # Other international indices (fallback to yfinance in a real implementation)
            else:
                logger.info(f"Using fallback data for {index_name}")
                constituents = []
            
            return constituents, constituents_metadata
            
        except Exception as e:
            logger.error(f"Error in get_index_constituents for {index_name}: {e}", exc_info=True)
            return [], {}

    @app.route('/indices', methods=['GET'])
    @app.route('/api/indices', methods=['GET'])
    def get_indices_endpoint():
        """
        API endpoint to get market indices data.
        
        Returns:
            JSON: Market indices data organized by country and exchange
        """
        try:
            # Clear old cache files if the refresh parameter is set
            refresh = request.args.get('refresh', 'false').lower() == 'true'
            if refresh:
                logger.info("Refresh parameter detected, clearing indices cache")
                try:
                    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                           'attached_assets', 'cache')
                    indices_cache = os.path.join(cache_dir, 'indices_data.json')
                    if os.path.exists(indices_cache):
                        os.remove(indices_cache)
                        logger.info("Cleared indices cache file")
                except Exception as e:
                    logger.error(f"Error clearing cache: {e}", exc_info=True)
            
            # Get real-time indices data using the indicesdownload module
            try:
                logger.info("Fetching real-time indices data from indicesdownload module")
                indices_list = get_indices_list()
                
                if indices_list:
                    logger.info(f"Successfully retrieved {len(indices_list)} indices")
                    return jsonify(indices_list)
                else:
                    logger.warning("No indices data returned from indicesdownload module, falling back to original method")
            except Exception as e:
                logger.error(f"Error fetching indices from indicesdownload module: {e}", exc_info=True)
                logger.warning("Falling back to original indices data method")
            
            # Fallback to original method if new method fails
            indices_data = get_indices()
            return jsonify(indices_data)
        except Exception as e:
            logger.error(f"Error in indices endpoint: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
            
    @app.route('/index/<path:index_name>/constituents', methods=['GET'])
    @app.route('/api/index/<path:index_name>/constituents', methods=['GET'])
    def get_index_constituents_endpoint(index_name):
        """
        API endpoint to get constituents of a specific index.
        
        Args:
            index_name (str): Name of the index
            
        Returns:
            JSON: List of constituent companies with metadata
        """
        try:
            # Log the received index name for debugging
            logger.info(f"Received request for index constituents: {index_name}")
            
            # Clear old cache files if the refresh parameter is set
            refresh = request.args.get('refresh', 'false').lower() == 'true'
            if refresh:
                logger.info(f"Refresh parameter detected, clearing constituent cache for {index_name}")
                try:
                    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          'attached_assets', 'cache', 'constituents')
                    # Safe encoding for filename
                    cache_filename = index_name.replace('/', '_').replace(' ', '_')
                    constituent_cache = os.path.join(cache_dir, f"{cache_filename}.json")
                    if os.path.exists(constituent_cache):
                        os.remove(constituent_cache)
                        logger.info(f"Cleared constituent cache file for {index_name}")
                except Exception as e:
                    logger.error(f"Error clearing constituent cache for {index_name}: {e}", exc_info=True)
            
            # Try to fetch real-time constituents using the indicesdownload module
            try:
                logger.info(f"Fetching real-time constituents for {index_name} using indicesdownload module")
                real_time_constituents = download_index_constituents(index_name, refresh=refresh)
                
                if real_time_constituents and len(real_time_constituents) > 0:
                    logger.info(f"Successfully retrieved {len(real_time_constituents)} real-time constituents for {index_name}")
                    
                    # Generate metadata based on index name
                    exchange = "Unknown"
                    currency = "Unknown"
                    market = "Unknown"
                    description = f"Index data for {index_name}"
                    
                    # Determine exchange, currency, and market based on index name
                    if "NIFTY" in index_name.upper() or "NSE" in index_name.upper():
                        exchange = "NSE"
                        currency = "INR"
                        market = "India"
                        description = f"Indian market index {index_name} from National Stock Exchange"
                    elif "BSE" in index_name.upper() or "SENSEX" in index_name.upper():
                        exchange = "BSE"
                        currency = "INR"
                        market = "India"
                        description = f"Indian market index {index_name} from Bombay Stock Exchange"
                    elif "S&P" in index_name or "SP500" in index_name or "S&P 500" in index_name:
                        exchange = "NYSE"
                        currency = "USD"
                        market = "United States"
                        description = f"US market index {index_name}"
                    elif "DOW" in index_name.upper() or "DOWJONES" in index_name.upper():
                        exchange = "NYSE"
                        currency = "USD"
                        market = "United States"
                        description = f"US market index {index_name}"
                    elif "NASDAQ" in index_name.upper():
                        exchange = "NASDAQ"
                        currency = "USD"
                        market = "United States"
                        description = f"US market index {index_name}"
                    elif "FTSE" in index_name.upper():
                        exchange = "LSE"
                        currency = "GBP"
                        market = "United Kingdom"
                        description = f"UK market index {index_name}"
                    elif "DAX" in index_name.upper():
                        exchange = "XETRA"
                        currency = "EUR"
                        market = "Germany"
                        description = f"German market index {index_name}"
                    elif "CAC" in index_name.upper():
                        exchange = "Euronext Paris"
                        currency = "EUR"
                        market = "France"
                        description = f"French market index {index_name}"
                    
                    metadata = {
                        "index": index_name,
                        "market": market,
                        "currency": currency,
                        "exchange": exchange,
                        "description": description,
                        "count": len(real_time_constituents),
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    return jsonify({"constituents": real_time_constituents, "metadata": metadata})
                else:
                    logger.warning(f"No constituents returned from indicesdownload module for {index_name}, falling back to original method")
            except Exception as e:
                logger.error(f"Error fetching constituents for {index_name} from indicesdownload module: {e}", exc_info=True)
                logger.warning(f"Falling back to original constituents method for {index_name}")
            
            # Special case for BSE SENSEX to ensure reliable response if real-time data fails
            if index_name == "BSE SENSEX":
                logger.info("Generating direct BSE SENSEX response in app.py")
                
                # Generate BSE SENSEX constituents
                bse_sensex_constituents = [
                    {"symbol": "RELIANCE", "company": "Reliance Industries Ltd.", "exchange": "BSE", "price": 2568.35, "change": 25.75, "changePercent": 1.01, "currency": "INR", "sector": "Energy"},
                    {"symbol": "TCS", "company": "Tata Consultancy Services Ltd.", "exchange": "BSE", "price": 3450.65, "change": 42.50, "changePercent": 1.25, "currency": "INR", "sector": "Technology"},
                    {"symbol": "HDFCBANK", "company": "HDFC Bank Ltd.", "exchange": "BSE", "price": 1648.25, "change": 12.50, "changePercent": 0.76, "currency": "INR", "sector": "Financials"},
                    {"symbol": "ICICIBANK", "company": "ICICI Bank Ltd.", "exchange": "BSE", "price": 1054.75, "change": 8.45, "changePercent": 0.81, "currency": "INR", "sector": "Financials"},
                    {"symbol": "HINDUNILVR", "company": "Hindustan Unilever Ltd.", "exchange": "BSE", "price": 2485.30, "change": 18.70, "changePercent": 0.76, "currency": "INR", "sector": "Consumer Staples"}
                ]
                
                metadata = {
                    "index_name": "BSE SENSEX",
                    "count": len(bse_sensex_constituents),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "index_type": "equity",
                    "description": "BSE SENSEX is a free-float market-weighted stock market index of 30 well-established and financially sound companies listed on the Bombay Stock Exchange."
                }
                
                logger.info(f"Returning BSE SENSEX response directly from app.py with {len(bse_sensex_constituents)} constituents")
                return jsonify({"constituents": bse_sensex_constituents, "metadata": metadata})
            
            # For all other indices, use the standard function
            try:
                # Try downloading with the new function first
                constituents = download_index_constituents(index_name, refresh=refresh)
                metadata = {
                    "index": index_name,
                    "count": len(constituents),
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                constituents_data = (constituents, metadata)
            except Exception as e:
                logger.error(f"Error using download_index_constituents for {index_name}: {e}")
                constituents_data = get_index_constituents(index_name)
            
            # Check if we have a tuple return (constituents, metadata)
            if isinstance(constituents_data, tuple) and len(constituents_data) == 2:
                constituents, metadata = constituents_data
                # Return both constituents and metadata in the response
                return jsonify({"constituents": constituents, "metadata": metadata})
            else:
                # For backward compatibility, create a metadata object based on index name
                constituents = constituents_data
                
                # Default metadata values
                exchange = "Unknown"
                currency = "Unknown"
                market = "Unknown"
                description = f"Index data for {index_name}"
                
                # Determine exchange, currency, and market based on index name
                if "NIFTY" in index_name.upper() or "NSE" in index_name.upper():
                    exchange = "NSE"
                    currency = "INR"
                    market = "India"
                    description = f"Indian market index {index_name} from National Stock Exchange"
                elif "BSE" in index_name.upper() or "SENSEX" in index_name.upper():
                    exchange = "BSE"
                    currency = "INR"
                    market = "India"
                    description = f"Indian market index {index_name} from Bombay Stock Exchange"
                elif "S&P" in index_name or "SP500" in index_name or "S&P 500" in index_name:
                    exchange = "NYSE"
                    currency = "USD"
                    market = "United States"
                    description = f"US market index {index_name}"
                elif "DOW" in index_name.upper() or "DOWJONES" in index_name.upper():
                    exchange = "NYSE"
                    currency = "USD"
                    market = "United States"
                    description = f"US market index {index_name}"
                elif "NASDAQ" in index_name.upper():
                    exchange = "NASDAQ"
                    currency = "USD"
                    market = "United States"
                    description = f"US market index {index_name}"
                
                metadata = {
                    "index": index_name,
                    "market": market,
                    "currency": currency,
                    "exchange": exchange,
                    "description": description,
                    "count": len(constituents)
                }
                
                # Return both constituents and metadata in the response
                return jsonify({"constituents": constituents, "metadata": metadata})
        except Exception as e:
            logger.error(f"Error in index constituents endpoint for {index_name}: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/api/company/<ticker>/news', methods=['GET'])
    def get_company_news(ticker):
        """
        API endpoint to get news for a specific company.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            JSON: List of news articles for the company
        """
        try:
            logger.info(f"Fetching news for {ticker}")
            
            # Normalize ticker symbol
            ticker = ticker.upper().strip()
            
            # Try to get news from Yahoo Finance
            try:
                stock = yf.Ticker(ticker)
                news_items = stock.news
                
                if news_items:
                    processed_news = []
                    
                    for item in news_items[:10]:  # Limit to 10 news items
                        news_entry = {
                            'title': item.get('title', 'No Title'),
                            'publisher': item.get('publisher', 'Unknown Source'),
                            'link': item.get('link', '#'),
                            'published': item.get('providerPublishTime', 0),
                            'summary': item.get('summary', 'No summary available'),
                            'source': 'Yahoo Finance'
                        }
                        processed_news.append(news_entry)
                    
                    logger.info(f"Found {len(processed_news)} news items for {ticker} from Yahoo Finance")
                    return jsonify(processed_news)
                
            except Exception as e:
                logger.warning(f"Error fetching news from Yahoo Finance for {ticker}: {e}")
            
            # Fallback to searching for news via web scraping
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                search_url = f"https://www.google.com/search?q={ticker}+stock+news&tbm=nws"
                response = requests.get(search_url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    news_results = soup.select('div.SoaBEf')
                    
                    processed_news = []
                    for item in news_results[:10]:  # Limit to 10 news items
                        title_element = item.select_one('div.MBeuO')
                        link_element = item.select_one('a')
                        source_element = item.select_one('div.CEMjEf')
                        time_element = item.select_one('div.OSrXXb')
                        
                        if title_element and link_element:
                            title = title_element.get_text(strip=True)
                            link = link_element.get('href', '#')
                            source = source_element.get_text(strip=True) if source_element else 'Unknown Source'
                            published_time = time_element.get_text(strip=True) if time_element else 'Recently'
                            
                            news_entry = {
                                'title': title,
                                'publisher': source,
                                'link': link,
                                'published': published_time,
                                'summary': '',  # No summary available from this source
                                'source': 'Web Search'
                            }
                            processed_news.append(news_entry)
                    
                    logger.info(f"Found {len(processed_news)} news items for {ticker} from web search")
                    return jsonify(processed_news)
                
            except Exception as e:
                logger.warning(f"Error scraping news for {ticker}: {e}")
                
            # If all methods fail, return empty array
            logger.warning(f"No news found for {ticker} from any source")
            return jsonify([])
            
        except Exception as e:
            logger.error(f"Error in company news endpoint: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/companies', methods=['GET'])
    @app.route('/api/companies', methods=['GET'])
    def get_companies():
        """
        API endpoint to get company lists for different market indices.
        
        Returns:
            JSON: Lists of companies in various market indices
        """
        try:
            # Get the indices data to fetch the structure
            indices_data = get_indices()
            logger.info("Fetching companies for indices: NIFTY 50, S&P 100, Dow Jones IA")
            
            # Fetch companies using the download_index_constituents function
            try:
                # Try to get NIFTY 50 constituents
                nifty_companies = download_index_constituents("NIFTY 50")
                nifty_metadata = {"index": "NIFTY 50", "count": len(nifty_companies), "exchange": "NSE", "currency": "INR"}
            except Exception as e:
                logger.error(f"Error fetching NIFTY 50 constituents: {e}")
                nifty_companies, nifty_metadata = [], {}
                
            try:
                # Try to get S&P 100 constituents
                sp100_companies = download_index_constituents("S&P 100")
                sp100_metadata = {"index": "S&P 100", "count": len(sp100_companies), "exchange": "NYSE/NASDAQ", "currency": "USD"}
            except Exception as e:
                logger.error(f"Error fetching S&P 100 constituents: {e}")
                sp100_companies, sp100_metadata = [], {}
                
            try:
                # Try to get Dow Jones constituents
                dowjones_companies = download_index_constituents("Dow Jones Industrial Average")
                dowjones_metadata = {"index": "Dow Jones Industrial Average", "count": len(dowjones_companies), "exchange": "NYSE", "currency": "USD"}
            except Exception as e:
                logger.error(f"Error fetching Dow Jones constituents: {e}")
                dowjones_companies, dowjones_metadata = [], {}
                
            try:
                # Try to get ASX 200 constituents
                asx200_companies = download_index_constituents("S&P/ASX 200")
                asx_metadata = {"index": "S&P/ASX 200", "count": len(asx200_companies), "exchange": "ASX", "currency": "AUD"}
            except Exception as e:
                logger.error(f"Error fetching ASX 200 constituents: {e}")
                asx200_companies, asx_metadata = [], {}
            
            companies = {
                'NIFTY 50': {
                    'constituents': nifty_companies,
                    'metadata': nifty_metadata
                },
                'S&P 100': {
                    'constituents': sp100_companies,
                    'metadata': sp100_metadata
                },
                'Dow Jones Industrial Average': {
                    'constituents': dowjones_companies,
                    'metadata': dowjones_metadata
                },
                'S&P/ASX 200': {
                    'constituents': asx200_companies,
                    'metadata': asx_metadata
                }
            }
            
            total_companies = len(nifty_companies) + len(sp100_companies) + len(dowjones_companies) + len(asx200_companies)
            logger.info(f"Successfully prepared company data for {len(companies)} indices, total {total_companies} companies")
            return jsonify(companies)
            
        except Exception as e:
            logger.error(f"Error in get_companies endpoint: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
    
    return app

# Create Flask app
app = create_app()

# Run server in development mode
if __.name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)