"""
PyTrade - Swing Trading Service

This file provides functionality for short-term, medium-term, and long-term 
swing trading analysis for stocks. It processes stock data, calculates technical
indicators, and provides trading signals.

Author: PyTrade Development Team
Version: 1.0.0
Date: March 26, 2025
License: Proprietary
"""

from flask import jsonify
import yfinance as yf
import pandas as pd
import numpy as np
# Fix for numpy NaN import error - handle both cases
try:
    from numpy import NaN as npNaN
except ImportError:
    # Use numpy's nan instead if NaN is not available
    from numpy import nan as npNaN
import math
import requests
import logging
import traceback
import json
import random
import datetime
from nsepython import equity_history, nse_eq, indices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def analyze_swing_trading_batch(tickers, timeframe='short'):
    """
    Process a batch of tickers for swing trading analysis.
    
    Args:
        tickers (list): List of ticker symbols
        timeframe (str): Trading timeframe ('short', 'medium', 'long')
        
    Returns:
        list: List of analysis results
    """
    results = []
    
    # Iterate over each ticker and analyze
    for ticker in tickers:
        try:
            # Handle case where ticker might be a dictionary or other object
            if isinstance(ticker, dict) and 'symbol' in ticker:
                ticker_symbol = ticker['symbol']
            elif not isinstance(ticker, str):
                ticker_symbol = str(ticker)
            else:
                ticker_symbol = ticker
                
            # Get analysis for single ticker
            result = analyze_swing_trading(ticker_symbol, timeframe)
            results.append(result)
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            logger.error(traceback.format_exc())
            # Append error information
            results.append({"ticker": ticker, "error": str(e)})
    
    return results

def analyze_swing_trading(ticker, timeframe='short'):
    """
    Analyze a single ticker for swing trading opportunities.
    
    Args:
        ticker (str): Stock ticker symbol
        timeframe (str): Trading timeframe ('short', 'medium', 'long')
        
    Returns:
        dict: Analysis results including signals and indicators
    """
    try:
        logger.info(f"Starting swing trading analysis for ticker {ticker} with timeframe {timeframe}")
        
        # Make sure ticker is a string
        if not isinstance(ticker, str):
            ticker = str(ticker)
        
        # Normalize timeframe to handle case sensitivity and string variations
        timeframe_str = str(timeframe).lower().strip() if timeframe else "short-term"
        
        # Improved timeframe handling with better pattern matching
        # Add extensive logging to help identify issues
        logger.info(f"Original timeframe value: '{timeframe}'")
        logger.info(f"Normalized timeframe string: '{timeframe_str}'")
        
        # Handle various timeframe formats including those with hyphens
        if "short" in timeframe_str or "short-term" in timeframe_str:
            period = "60d"  # 60 days for short-term
            timeframe_lower = "short"
            logger.info(f"Identified as SHORT-TERM, using period={period} for ticker {ticker}")
        elif "medium" in timeframe_str or "medium-term" in timeframe_str:
            period = "120d"  # 120 days for medium-term
            timeframe_lower = "medium"
            logger.info(f"Identified as MEDIUM-TERM, using period={period} for ticker {ticker}")
        elif "long" in timeframe_str or "long-term" in timeframe_str:
            period = "250d"  # 250 days for long-term
            timeframe_lower = "long"
            logger.info(f"Identified as LONG-TERM, using period={period} for ticker {ticker}")
        else:
            # Default to short-term if unrecognized
            logger.warning(f"UNKNOWN timeframe '{timeframe}', using SHORT-TERM (60d) as default")
            period = "60d"
            timeframe_lower = "short"
        
        interval = "1d"  # Daily data
        
        # Check if ticker is an Indian stock (NSE)
        is_indian_stock = ticker in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "SBIN", 
                                     "BHARTIARTL", "ITC", "KOTAKBANK", "HCLTECH", "HINDUNILVR", 
                                     "MARUTI", "ONGC", "TATAMOTORS", "ADANIPORTS"] or ticker.endswith(".NS")
        
        # Ensure NSE tickers have .NS suffix for Yahoo Finance
        yahoo_ticker = ticker
        if is_indian_stock and not ticker.endswith(".NS"):
            yahoo_ticker = f"{ticker}.NS"
            logger.info(f"Adding .NS suffix to Indian stock: {ticker} -> {yahoo_ticker}")
        
        # Get historical data
        if is_indian_stock:
            try:
                # Try to get data from NSE Python
                symbol = ticker.replace(".NS", "")
                logger.info(f"Getting data for Indian stock {symbol} using nsepython")
                
                # For NSE stocks, fetch data using nsepython's equity_history
                # We'll create a DataFrame similar to what yfinance returns
                import datetime as dt
                
                # Calculate from_date based on timeframe
                # Use the already normalized timeframe_str from above
                timeframe_str_local = str(timeframe).lower().strip() if timeframe else "short-term"
                logger.info(f"NSE data timeframe local: '{timeframe_str_local}'")
                
                if "short" in timeframe_str_local or "short-term" in timeframe_str_local:
                    days_back = 60
                    logger.info(f"Using short-term (60 days) for NSE data")
                elif "medium" in timeframe_str_local or "medium-term" in timeframe_str_local:
                    days_back = 120
                    logger.info(f"Using medium-term (120 days) for NSE data")
                else:
                    days_back = 250
                    logger.info(f"Using long-term (250 days) for NSE data")
                
                from_date = (dt.datetime.now() - dt.timedelta(days=days_back)).strftime('%d-%b-%Y')
                to_date = dt.datetime.now().strftime('%d-%b-%Y')
                
                # Get stock data from NSE
                try:
                    nse_data = equity_history(symbol=symbol, from_date=from_date, to_date=to_date)
                    
                    # Convert NSE data to format similar to yfinance
                    hist = pd.DataFrame()
                    
                    if nse_data is not None and not nse_data.empty:
                        hist['Open'] = nse_data['OPEN']
                        hist['High'] = nse_data['HIGH'] 
                        hist['Low'] = nse_data['LOW']
                        hist['Close'] = nse_data['CLOSE']
                        hist['Volume'] = nse_data['VOLUME']
                        hist.index = pd.to_datetime(nse_data['DATE'])
                    else:
                        # Fallback to Yahoo Finance if NSE data is empty
                        logger.warning(f"NSE data empty for {symbol}, falling back to Yahoo Finance")
                        stock = yf.Ticker(yahoo_ticker)
                        hist = stock.history(period=period, interval=interval)
                except Exception as e:
                    logger.error(f"Error fetching NSE data for {symbol}: {e}")
                    # Fallback to Yahoo Finance
                    stock = yf.Ticker(yahoo_ticker)
                    hist = stock.history(period=period, interval=interval)
            except Exception as e:
                logger.error(f"Error with NSE Python for {ticker}: {e}")
                # Fallback to Yahoo Finance
                stock = yf.Ticker(yahoo_ticker)
                hist = stock.history(period=period, interval=interval)
        else:
            # For non-Indian stocks, use Yahoo Finance
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return {"ticker": ticker, "error": "No historical data available"}
        
        # Get company info
        try:
            company_name = stock.info.get('shortName', ticker)
        except:
            company_name = ticker
        
        # Analyze technical indicators
        analysis = analyze_technical_indicators(hist, ticker, timeframe)
        
        # Add company and ticker info
        analysis["ticker"] = ticker
        analysis["company_name"] = company_name
        
        # Generate sample prediction data (this would be replaced with actual ML model predictions)
        try:
            current_price = hist['Close'].iloc[-1]
            if not isinstance(current_price, (int, float)) or math.isnan(current_price):
                logger.warning(f"Invalid current price for {ticker}: {current_price}, using default value")
                current_price = 100.0  # Default fallback value
            
            # Generate prediction dates
            try:
                analysis["prediction_dates"] = generate_future_dates(timeframe)
            except Exception as e:
                logger.error(f"Error generating prediction dates for {ticker}: {e}")
                # Provide default dates
                today = datetime.date.today()
                dates = []
                for i in range(1, 6):  # Default to 5 days
                    future_date = today + datetime.timedelta(days=i)
                    dates.append(future_date.strftime("%Y-%m-%d"))
                analysis["prediction_dates"] = dates
            
            # Generate prediction prices
            try:
                overall_ta_score = analysis.get("overall_ta_score", 50)  # Default to neutral if not available
                analysis["prediction_prices"] = generate_prediction_prices(current_price, overall_ta_score, timeframe)
            except Exception as e:
                logger.error(f"Error generating prediction prices for {ticker}: {e}")
                # Provide default prices
                analysis["prediction_prices"] = [current_price] * len(analysis["prediction_dates"])
        except Exception as e:
            logger.error(f"Error in prediction generation: {e}")
            # Set default prediction data if outer try block fails
            today = datetime.date.today()
            dates = []
            for i in range(1, 6):  # Default to 5 days
                future_date = today + datetime.timedelta(days=i)
                dates.append(future_date.strftime("%Y-%m-%d"))
            analysis["prediction_dates"] = dates
            analysis["prediction_prices"] = [100.0] * 5  # Default prices
        
        # Add stop loss and take profit targets
        try:
            volatility = hist['Close'].pct_change().std() * 100
            if math.isnan(volatility):
                volatility = 2.0  # Default volatility if calculation fails
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            volatility = 2.0  # Default volatility
        
        # Make sure current_price is defined
        if 'current_price' not in locals() or not isinstance(current_price, (int, float)) or math.isnan(current_price):
            current_price = 100.0  # Default price if not set in try block
            
        analysis["stoploss"] = round(current_price * (1 - volatility / 100), 2)
        analysis["takeprofit"] = round(current_price * (1 + 2 * volatility / 100), 2)
        
        # Add news sentiment (simplified)
        news_sentiment = analyze_news_sentiment(ticker)
        analysis["news"] = news_sentiment["news"]
        analysis["news_sentiment_score"] = news_sentiment["score"]
        
        # Calculate fundamental score (simplified)
        fundamental_analysis = analyze_fundamentals(stock)
        analysis["fundamental_analysis"] = fundamental_analysis
        
        # Calculate combined score (80% technical, 15% fundamental, 5% news)
        technical_weight = 0.80
        fundamental_weight = 0.15
        news_weight = 0.05
        
        combined_score = (
            technical_weight * analysis["overall_ta_score"] +
            fundamental_weight * fundamental_analysis["overall_fa_score"] +
            news_weight * news_sentiment["score"]
        )
        
        analysis["combined_overall_score"] = round(combined_score, 2)
        
        # Determine combined signal
        if combined_score >= 70:
            analysis["combined_overall_signal"] = "Buy"
        elif combined_score <= 30:
            analysis["combined_overall_signal"] = "DBuy"  # Don't Buy
        else:
            analysis["combined_overall_signal"] = "Neutral"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in swing trading analysis for {ticker}: {e}")
        logger.error(traceback.format_exc())
        return {"ticker": ticker, "error": str(e)}

def analyze_technical_indicators(hist, ticker, timeframe):
    """
    Calculate and analyze technical indicators for swing trading.
    
    Args:
        hist (pd.DataFrame): Historical price data
        ticker (str): Stock ticker symbol
        timeframe (str): Trading timeframe
        
    Returns:
        dict: Technical analysis results
    """
    # Make a copy of the dataframe to avoid modifying the original
    df = hist.copy()
    
    # Calculate RSI using pandas_ta
    df.ta.rsi(length=14, append=True)
    rsi_col = [col for col in df.columns if 'RSI' in col][0]
    last_rsi = df[rsi_col].iloc[-1]
    
    # Calculate MACD using pandas_ta
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    macd_cols = [col for col in df.columns if 'MACD' in col]
    last_macd = df[macd_cols[0]].iloc[-1]  # MACD
    last_macd_signal = df[macd_cols[1]].iloc[-1]  # MACDs
    last_macd_hist = df[macd_cols[2]].iloc[-1]  # MACDh
    
    # Calculate ATR using pandas_ta
    df.ta.atr(length=14, append=True)
    atr_col = [col for col in df.columns if 'ATR' in col][0]
    last_atr = df[atr_col].iloc[-1]
    
    # Calculate EMAs using pandas_ta
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    last_ema_short = df['EMA_20'].iloc[-1]
    last_ema_long = df['EMA_50'].iloc[-1]
    
    # Calculate Bollinger Bands using pandas_ta
    df.ta.bbands(length=20, std=2, append=True)
    bb_cols = [col for col in df.columns if 'BBL' in col or 'BBM' in col or 'BBU' in col]
    last_lower = df[[col for col in bb_cols if 'BBL' in col][0]].iloc[-1]
    last_middle = df[[col for col in bb_cols if 'BBM' in col][0]].iloc[-1]
    last_upper = df[[col for col in bb_cols if 'BBU' in col][0]].iloc[-1]
    
    # Calculate Fibonacci retracement levels
    high_price = hist['High'].max()
    low_price = hist['Low'].min()
    
    fib_levels = {
        "0.0": low_price,
        "0.236": low_price + 0.236 * (high_price - low_price),
        "0.382": low_price + 0.382 * (high_price - low_price),
        "0.5": low_price + 0.5 * (high_price - low_price),
        "0.618": low_price + 0.618 * (high_price - low_price),
        "0.786": low_price + 0.786 * (high_price - low_price),
        "1.0": high_price
    }
    
    current_price = hist['Close'].iloc[-1]
    
    # Analyze technical indicators
    
    # RSI Analysis
    rsi_score = 0
    if last_rsi <= 30:
        rsi_signal = "Buy"  # Oversold
        rsi_score = 100
    elif last_rsi >= 70:
        rsi_signal = "DBuy"  # Overbought
        rsi_score = 0
    else:
        rsi_signal = "Neutral"
        rsi_score = 50
    
    # MACD Analysis
    macd_score = 0
    if last_macd > last_macd_signal and last_macd_hist > 0:
        macd_signal = "Buy"  # Bullish
        macd_score = 100
    elif last_macd < last_macd_signal and last_macd_hist < 0:
        macd_signal = "DBuy"  # Bearish
        macd_score = 0
    else:
        macd_signal = "Neutral"
        macd_score = 50
    
    # ATR Analysis (simplified)
    atr_score = 0
    atr_percentage = (last_atr / current_price) * 100
    
    if atr_percentage < 1.5:
        atr_signal = "DBuy"  # Low volatility
        atr_score = 30
    elif atr_percentage > 4:
        atr_signal = "DBuy"  # Too volatile
        atr_score = 30
    else:
        atr_signal = "Buy"  # Good volatility for swing trading
        atr_score = 80
    
    # EMA Analysis
    ema_score = 0
    if last_ema_short > last_ema_long and current_price > last_ema_short:
        ema_signal = "Buy"  # Strong uptrend
        ema_score = 100
    elif last_ema_short < last_ema_long and current_price < last_ema_short:
        ema_signal = "DBuy"  # Strong downtrend
        ema_score = 0
    else:
        ema_signal = "Neutral"
        ema_score = 50
    
    # Fibonacci Analysis
    fib_score = 0
    nearest_level = min(fib_levels.items(), key=lambda x: abs(float(x[1]) - current_price))
    
    if current_price <= fib_levels["0.236"]:
        fib_signal = "Buy"  # Near support
        fib_score = 90
    elif current_price >= fib_levels["0.786"]:
        fib_signal = "DBuy"  # Near resistance
        fib_score = 10
    else:
        fib_signal = "Neutral"
        fib_score = 50
    
    # Bollinger Bands Analysis
    bb_score = 0
    
    if current_price <= last_lower:
        bb_signal = "Buy"  # Price at or below lower band
        bb_score = 90
    elif current_price >= last_upper:
        bb_signal = "DBuy"  # Price at or above upper band
        bb_score = 10
    else:
        bb_signal = "Neutral"
        bb_score = 50
    
    # Market Structure Analysis (simplified)
    ms_score = 0
    
    # Calculate highest high and lowest low for last 10 days
    recent_highs = hist['High'].rolling(window=3).max().diff().iloc[-5:]
    recent_lows = hist['Low'].rolling(window=3).min().diff().iloc[-5:]
    
    # Check if price is making higher highs and higher lows (uptrend)
    is_uptrend = (recent_highs > 0).all() and (recent_lows > 0).all()
    
    # Check if price is making lower highs and lower lows (downtrend)
    is_downtrend = (recent_highs < 0).all() and (recent_lows < 0).all()
    
    if is_uptrend:
        ms_signal = "Buy"
        ms_score = 100
    elif is_downtrend:
        ms_signal = "DBuy"
        ms_score = 0
    else:
        ms_signal = "Neutral"
        ms_score = 50
    
    # Calculate overall technical score
    indicator_weights = {
        "RSI": 0.15,
        "MACD": 0.2,
        "ATR": 0.05,
        "EMA": 0.25,
        "Fibonacci": 0.1,
        "BB": 0.1,
        "MS": 0.15
    }
    
    overall_ta_score = (
        indicator_weights["RSI"] * rsi_score +
        indicator_weights["MACD"] * macd_score +
        indicator_weights["ATR"] * atr_score +
        indicator_weights["EMA"] * ema_score +
        indicator_weights["Fibonacci"] * fib_score +
        indicator_weights["BB"] * bb_score +
        indicator_weights["MS"] * ms_score
    )
    
    # Create response dictionary
    analysis = {
        "overall_ta_score": round(overall_ta_score, 2),
        "RSI": {
            "value": round(last_rsi, 2),
            "signal": rsi_signal,
            "score": rsi_score,
            "Final_Trade_Signal": rsi_signal
        },
        "MACD": {
            "value": round(last_macd, 4),
            "signal_line": round(last_macd_signal, 4),
            "histogram": round(last_macd_hist, 4),
            "score": macd_score,
            "Final_Trade_Signal": macd_signal
        },
        "ATR": {
            "value": round(last_atr, 2),
            "percentage": round(atr_percentage, 2),
            "score": atr_score,
            "Final_Trade_Signal": atr_signal
        },
        "EMA": {
            "short": round(last_ema_short, 2),
            "long": round(last_ema_long, 2),
            "score": ema_score,
            "Final_Trade_Signal": ema_signal
        },
        "Fibonacci": {
            "levels": {k: round(v, 2) for k, v in fib_levels.items()},
            "nearest_level": nearest_level[0],
            "score": fib_score,
            "Final_Trade_Signal": fib_signal
        },
        "BB": {
            "upper": round(last_upper, 2),
            "middle": round(last_middle, 2),
            "lower": round(last_lower, 2),
            "score": bb_score,
            "Final_Trade_Signal": bb_signal
        },
        "MS": {
            "is_uptrend": bool(is_uptrend),
            "is_downtrend": bool(is_downtrend),
            "score": ms_score,
            "Final_Trade_Signal": ms_signal
        }
    }
    
    return analysis

def analyze_fundamentals(stock):
    """
    Simple fundamental analysis of a stock.
    
    Args:
        stock (yf.Ticker): Yahoo Finance Ticker object
        
    Returns:
        dict: Fundamental analysis results
    """
    try:
        info = stock.info
        
        # Extract fundamental metrics
        pe_ratio = info.get('forwardPE', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        debt_to_equity = info.get('debtToEquity', 0)
        
        # Analyze P/E ratio
        if pe_ratio <= 0:
            pe_ratio_status = "none"  # No valid P/E
            pe_score = 50
        elif pe_ratio < 15:
            pe_ratio_status = "good"  # Potentially undervalued
            pe_score = 80
        elif pe_ratio > 30:
            pe_ratio_status = "bad"  # Potentially overvalued
            pe_score = 20
        else:
            pe_ratio_status = "none"  # Average valuation
            pe_score = 50
        
        # Analyze earnings growth
        if earnings_growth <= 0:
            earnings_growth_status = "bad"  # Declining earnings
            earnings_score = 20
        elif earnings_growth > 0.1:  # 10% growth
            earnings_growth_status = "good"  # Good growth
            earnings_score = 80
        else:
            earnings_growth_status = "none"  # Moderate growth
            earnings_score = 50
        
        # Analyze debt to equity
        if debt_to_equity <= 0:
            debt_to_equity_status = "none"  # No debt info
            debt_score = 50
        elif debt_to_equity < 0.5:
            debt_to_equity_status = "good"  # Low debt
            debt_score = 80
        elif debt_to_equity > 1.5:
            debt_to_equity_status = "bad"  # High debt
            debt_score = 20
        else:
            debt_to_equity_status = "none"  # Average debt
            debt_score = 50
        
        # Calculate overall fundamental score
        weights = {"pe_ratio": 0.3, "earnings_growth": 0.4, "debt_to_equity": 0.3}
        overall_fa_score = (
            weights["pe_ratio"] * pe_score +
            weights["earnings_growth"] * earnings_score +
            weights["debt_to_equity"] * debt_score
        )
        
        return {
            "overall_fa_score": round(overall_fa_score, 2),
            "pe_ratio": pe_ratio,
            "pe_ratio_status": pe_ratio_status,
            "earnings_growth": earnings_growth * 100 if earnings_growth else 0,  # Convert to percentage
            "earnings_growth_status": earnings_growth_status,
            "debt_to_equity": debt_to_equity,
            "debt_to_equity_status": debt_to_equity_status
        }
    except Exception as e:
        logger.error(f"Error in fundamental analysis: {e}")
        return {
            "overall_fa_score": 50,
            "pe_ratio": 0,
            "pe_ratio_status": "none",
            "earnings_growth": 0,
            "earnings_growth_status": "none",
            "debt_to_equity": 0,
            "debt_to_equity_status": "none",
            "error": str(e)
        }

def analyze_news_sentiment(ticker):
    """
    Analyze news sentiment for a ticker (simplified implementation).
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: News sentiment analysis results
    """
    # This would typically call a news API and perform sentiment analysis
    # For demonstration, we'll create sample data
    
    # Generate 0-3 random news items
    news_count = random.randint(0, 3)
    news = []
    
    for i in range(news_count):
        sentiment = random.choice(["positive", "neutral", "negative"])
        news_item = {
            "title": f"Sample news title for {ticker} #{i+1}",
            "url": f"https://example.com/news/{ticker}/{i+1}",
            "published": "2025-03-26",
            "sentiment": sentiment,
            "summary": f"This is a sample {sentiment} news summary for {ticker}"
        }
        news.append({"content": news_item})
    
    # Calculate a sentiment score (0-100)
    score = random.randint(30, 80)
    
    return {
        "news": news,
        "score": score
    }

def generate_future_dates(timeframe):
    """
    Generate future dates for predictions based on timeframe.
    
    Args:
        timeframe (str): Trading timeframe
        
    Returns:
        list: List of date strings
    """
    # For better code organization, use existing datetime import
    today = datetime.date.today()
    dates = []
    
    try:
        # Normalize timeframe string to handle any case variations
        timeframe_str = str(timeframe).lower().strip() if timeframe else "short-term"
        
        # Improved matching for various timeframe formats
        # Determine the number of days to predict based on timeframe
        if "short" in timeframe_str or "short-term" in timeframe_str:
            days = 5  # 5 days for short-term
            logger.info("Generating 5 future dates for short-term timeframe")
        elif "medium" in timeframe_str or "medium-term" in timeframe_str:
            days = 14  # 14 days for medium-term
            logger.info("Generating 14 future dates for medium-term timeframe")
        elif "long" in timeframe_str or "long-term" in timeframe_str:
            days = 30  # 30 days for long-term
            logger.info("Generating 30 future dates for long-term timeframe")
        else:
            logger.warning(f"Unknown timeframe '{timeframe}', using short-term (5 days) as default")
            days = 5  # Default to short-term
        
        for i in range(1, days + 1):
            future_date = today + datetime.timedelta(days=i)
            dates.append(future_date.strftime("%Y-%m-%d"))
        
        return dates
    except Exception as e:
        logger.error(f"Error generating future dates: {e}")
        # Return default dates (5 days) in case of any error
        default_dates = []
        for i in range(1, 6):
            future_date = today + datetime.timedelta(days=i)
            default_dates.append(future_date.strftime("%Y-%m-%d"))
        return default_dates

def generate_prediction_prices(current_price, score, timeframe):
    """
    Generate prediction prices based on current price and technical score.
    
    Args:
        current_price (float): Current stock price
        score (float): Technical analysis score
        timeframe (str): Trading timeframe
        
    Returns:
        list: List of predicted prices
    """
    try:
        # Check for invalid current_price
        if current_price is None or not isinstance(current_price, (int, float)) or math.isnan(current_price):
            logger.warning(f"Invalid current price detected: {current_price}. Using default value of 100.0")
            current_price = 100.0  # Default price if input is invalid
            
        # Normalize timeframe to handle case sensitivity
        timeframe_str = str(timeframe).lower().strip() if timeframe else "short-term"
        logger.info(f"Price prediction timeframe: '{timeframe_str}'")
        
        # Determine trend direction based on score
        # Score > 50 = uptrend, < 50 = downtrend
        trend_direction = 1 if score > 50 else -1
        
        # Adjust trend strength based on how far the score is from 50
        trend_strength = abs(score - 50) / 50  # 0 to 1
        
        # Set volatility multiplier based on timeframe with improved matching
        if "short" in timeframe_str or "short-term" in timeframe_str:
            max_change_pct = 0.05  # 5% for short-term
            logger.info("Using short-term volatility (5%) for price predictions")
        elif "medium" in timeframe_str or "medium-term" in timeframe_str:
            max_change_pct = 0.10  # 10% for medium-term
            logger.info("Using medium-term volatility (10%) for price predictions")
        elif "long" in timeframe_str or "long-term" in timeframe_str:
            max_change_pct = 0.15  # 15% for long-term
            logger.info("Using long-term volatility (15%) for price predictions")
        else:
            logger.warning(f"Unknown timeframe '{timeframe}', using short-term (5%) as default")
            max_change_pct = 0.05  # Default to short-term
        
        # Get dates to determine number of predictions
        dates = generate_future_dates(timeframe)
        num_predictions = len(dates)
        
        logger.info(f"Generating {num_predictions} price predictions for timeframe: {timeframe_str}")
        
        # Generate predictions with some randomness
        predictions = []
        last_price = current_price
        
        for i in range(num_predictions):
            # Calculate the change percentage for this step
            day_pct = max_change_pct * trend_strength * (i+1) / num_predictions
            
            # Add some randomness
            random_factor = random.uniform(-0.005, 0.005)  # ±0.5%
            
            # Calculate new price
            change = last_price * (day_pct * trend_direction + random_factor)
            new_price = last_price + change
            
            # Ensure the price doesn't go negative
            new_price = max(new_price, 0.01)
            
            predictions.append(round(new_price, 2))
            last_price = new_price
        
        logger.info(f"Successfully generated {len(predictions)} price predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error generating prediction prices: {e}")
        logger.error(traceback.format_exc())
        
        # Return default simple prediction data in case of any error
        default_predictions = []
        # Set a default trend direction if it's not defined in the try block
        default_trend_direction = 1  # Default to slight uptrend
        
        for i in range(1, 6):  # Default to 5 days
            default_predictions.append(round(current_price * (1 + i * 0.01 * default_trend_direction), 2))
        
        return default_predictions

# Export the functions we need in other modules
__all__ = [
    'analyze_swing_trading',
    'analyze_swing_trading_batch'
]