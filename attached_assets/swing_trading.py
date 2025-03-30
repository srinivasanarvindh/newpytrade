"""
PyTrade - Swing Trading Backend

This file provides the backend functionality for the swing trading feature of PyTrade.
It interfaces with swing_trading_service.py for the actual implementation of the
technical analysis and provides endpoints for the Angular frontend.

Author: PyTrade Development Team
Version: 1.0.0
Date: March 26, 2025
License: Proprietary
"""

import yfinance as yf
import pandas as pd
import numpy as np
# Apply the pandas_ta patch before importing swing_trading_service
np.NaN = np.nan  # Add NaN to numpy namespace
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
import datetime
import json

# Import our clean implementation from swing_trading_service
from swing_trading_service import analyze_swing_trading as service_analyze_swing_trading
from swing_trading_service import analyze_swing_trading_batch as service_analyze_swing_trading_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Technical Analysis Functions
def compute_rsi(price_data, period=14):
    """
    Compute Relative Strength Index (RSI).
    
    Args:
        price_data (pd.Series): Series of price data
        period (int): Period for RSI calculation
        
    Returns:
        np.array: Array of RSI values
    """
    # Calculate price changes
    delta = price_data.diff()
    
    # Separate gains and losses
    gain = delta.copy()
    loss = delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    loss = abs(loss)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.to_numpy()

def compute_macd(price_data, fast_period=12, slow_period=26, signal_period=9):
    """
    Compute Moving Average Convergence Divergence (MACD).
    
    Args:
        price_data (pd.Series): Series of price data
        fast_period (int): Period for fast EMA
        slow_period (int): Period for slow EMA
        signal_period (int): Period for signal line
        
    Returns:
        tuple: MACD line, signal line, and histogram
    """
    # Calculate EMAs
    ema_fast = price_data.ewm(span=fast_period, adjust=False).mean()
    ema_slow = price_data.ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line.to_numpy(), signal_line.to_numpy(), histogram.to_numpy()

def compute_atr(high, low, close, period=14):
    """
    Compute Average True Range (ATR).
    
    Args:
        high (pd.Series): Series of high prices
        low (pd.Series): Series of low prices
        close (pd.Series): Series of close prices
        period (int): Period for ATR calculation
        
    Returns:
        np.array: Array of ATR values
    """
    # Calculate true range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR
    atr = tr.rolling(window=period).mean()
    
    return atr.to_numpy()

def bollinger_bands(price_data, period=20, multiplier=2):
    """
    Calculate Bollinger Bands.
    
    Args:
        price_data (pd.Series): Series of price data
        period (int): Period for SMA calculation
        multiplier (float): Multiplier for standard deviation
        
    Returns:
        tuple: Upper band, middle band (SMA), lower band
    """
    # Calculate SMA
    sma = price_data.rolling(window=period).mean()
    
    # Calculate standard deviation
    std_dev = price_data.rolling(window=period).std()
    
    # Calculate bands
    upper_band = sma + (std_dev * multiplier)
    lower_band = sma - (std_dev * multiplier)
    
    return upper_band.to_numpy(), sma.to_numpy(), lower_band.to_numpy()

def fibonacci_levels(high, low):
    """
    Calculate Fibonacci retracement levels.
    
    Args:
        high (float): Highest price in the range
        low (float): Lowest price in the range
        
    Returns:
        dict: Dictionary of Fibonacci levels
    """
    diff = high - low
    
    return {
        "0.0": low,
        "0.236": low + 0.236 * diff,
        "0.382": low + 0.382 * diff,
        "0.5": low + 0.5 * diff,
        "0.618": low + 0.618 * diff,
        "0.786": low + 0.786 * diff,
        "1.0": high
    }

def calculate_support_resistance(df, window=10):
    """
    Calculate support and resistance levels.
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC data
        window (int): Window size for finding pivots
        
    Returns:
        tuple: Support and resistance levels
    """
    # Find local maxima and minima
    df['min'] = df['Low'].rolling(window=window, center=True).min()
    df['max'] = df['High'].rolling(window=window, center=True).max()
    
    # Get latest support and resistance
    support = df['min'].iloc[-1]
    resistance = df['max'].iloc[-1]
    
    return support, resistance

def calculate_pivot_points(high, low, close):
    """
    Calculate pivot points (classic method).
    
    Args:
        high (float): High price
        low (float): Low price
        close (float): Close price
        
    Returns:
        dict: Dictionary of pivot points
    """
    pivot = (high + low + close) / 3
    
    support1 = (2 * pivot) - high
    support2 = pivot - (high - low)
    support3 = low - 2 * (high - pivot)
    
    resistance1 = (2 * pivot) - low
    resistance2 = pivot + (high - low)
    resistance3 = high + 2 * (pivot - low)
    
    return {
        "pivot": pivot,
        "s1": support1,
        "s2": support2,
        "s3": support3,
        "r1": resistance1,
        "r2": resistance2,
        "r3": resistance3
    }

def calculate_percentage_change(current, reference):
    """
    Calculate percentage change.
    
    Args:
        current (float): Current value
        reference (float): Reference value
        
    Returns:
        float: Percentage change
    """
    return ((current - reference) / reference) * 100

def analyze_swing_trading(ticker, timeframe='short'):
    """
    Perform swing trading analysis for a given ticker.
    
    Args:
        ticker (str): Stock ticker symbol
        timeframe (str): Trading timeframe ('short', 'medium', 'long')
        
    Returns:
        dict: Analysis results
    """
    try:
        logger.info(f"Starting swing trading analysis for {ticker}, timeframe: {timeframe}")
        
        # Call the service implementation
        return service_analyze_swing_trading(ticker, timeframe)
        
        # Get current price
        current_price = history['Close'].iloc[-1]
        previous_price = history['Close'].iloc[-2]
        price_change = current_price - previous_price
        percentage_change = calculate_percentage_change(current_price, previous_price)
        
        # Calculate technical indicators
        history['RSI'] = compute_rsi(history['Close'])
        history['MACD'], history['MACD_Signal'], history['MACD_Hist'] = compute_macd(history['Close'])
        history['ATR'] = compute_atr(history['High'], history['Low'], history['Close'])
        history['Upper_BB'], history['Middle_BB'], history['Lower_BB'] = bollinger_bands(history['Close'])
        
        # Calculate EMAs
        history['EMA_9'] = history['Close'].ewm(span=9, adjust=False).mean()
        history['EMA_20'] = history['Close'].ewm(span=20, adjust=False).mean()
        history['EMA_50'] = history['Close'].ewm(span=50, adjust=False).mean()
        
        # Generate signals
        # RSI signals
        rsi_value = history['RSI'].iloc[-1]
        rsi_signal = "Buy" if rsi_value < 40 else "DBuy" if rsi_value > 70 else "Neutral"
        
        # MACD signals
        macd_value = history['MACD'].iloc[-1]
        macd_signal_value = history['MACD_Signal'].iloc[-1]
        macd_hist = history['MACD_Hist'].iloc[-1]
        macd_signal = "Buy" if macd_value > macd_signal_value else "DBuy" if macd_value < macd_signal_value else "Neutral"
        
        # ATR for volatility
        atr_value = history['ATR'].iloc[-1]
        atr_signal = "Neutral"  # ATR is primarily used for stop-loss/take-profit, not as a direct signal
        
        # EMA signals
        ema_9 = history['EMA_9'].iloc[-1]
        ema_20 = history['EMA_20'].iloc[-1]
        ema_50 = history['EMA_50'].iloc[-1]
        ema_signal = "Buy" if (ema_9 > ema_20 and ema_20 > ema_50) else "DBuy" if (ema_9 < ema_20 and ema_20 < ema_50) else "Neutral"
        
        # Bollinger Bands signals
        upper_bb = history['Upper_BB'].iloc[-1]
        middle_bb = history['Middle_BB'].iloc[-1]
        lower_bb = history['Lower_BB'].iloc[-1]
        bb_signal = "Buy" if current_price < lower_bb else "DBuy" if current_price > upper_bb else "Neutral"
        
        # Market Structure analysis
        # Simple implementation - more complex versions would look at patterns
        support, resistance = calculate_support_resistance(history)
        ms_signal = "Buy" if current_price > support and current_price < middle_bb else "DBuy" if current_price < resistance and current_price > middle_bb else "Neutral"
        
        # Fibonacci analysis
        high = history['High'].max()
        low = history['Low'].min()
        fib_levels = fibonacci_levels(high, low)
        
        # Just a simple implementation for demo purposes
        fib_signal = "Buy" if current_price < fib_levels["0.382"] else "DBuy" if current_price > fib_levels["0.618"] else "Neutral"
        
        # Calculate pivot points
        latest_high = history['High'].iloc[-1]
        latest_low = history['Low'].iloc[-1]
        latest_close = history['Close'].iloc[-1]
        pivot_points = calculate_pivot_points(latest_high, latest_low, latest_close)
        
        # Calculate trading info
        entry_point = current_price
        stop_loss = current_price - (2 * atr_value)
        target_price = current_price + (3 * atr_value)
        
        # Create detailed signal objects
        rsi_details = {
            "Value": float(rsi_value),
            "Signal": rsi_signal,
            "Overbought": str(rsi_value > 70),
            "Oversold": str(rsi_value < 30),
            "Trend": "Bullish" if rsi_value > 50 else "Bearish",
            "Final_Trade_Signal": rsi_signal
        }
        
        macd_details = {
            "Value": float(macd_value),
            "Signal_Line": float(macd_signal_value),
            "Histogram": float(macd_hist),
            "Above_Signal": str(macd_value > macd_signal_value),
            "Above_Zero": str(macd_value > 0),
            "Convergence": str(abs(macd_value - macd_signal_value) < abs(history['MACD'].iloc[-2] - history['MACD_Signal'].iloc[-2])),
            "Final_Trade_Signal": macd_signal
        }
        
        atr_details = {
            "Value": float(atr_value),
            "Volatility": "High" if atr_value > history['ATR'].mean() * 1.5 else "Low" if atr_value < history['ATR'].mean() * 0.5 else "Normal",
            "Stop_Loss": float(stop_loss),
            "Take_Profit": float(target_price),
            "Final_Trade_Signal": atr_signal
        }
        
        ema_details = {
            "EMA_9": float(ema_9),
            "EMA_20": float(ema_20),
            "EMA_50": float(ema_50),
            "EMA_9_Above_20": str(ema_9 > ema_20),
            "EMA_20_Above_50": str(ema_20 > ema_50),
            "Overall_Trend": "Bullish" if (ema_9 > ema_20 and ema_20 > ema_50) else "Bearish" if (ema_9 < ema_20 and ema_20 < ema_50) else "Neutral",
            "Final_Trade_Signal": ema_signal
        }
        
        bb_details = {
            "Upper_Band": float(upper_bb),
            "Middle_Band": float(middle_bb),
            "Lower_Band": float(lower_bb),
            "Width": float((upper_bb - lower_bb) / middle_bb),
            "Position": "Above Upper" if current_price > upper_bb else "Below Lower" if current_price < lower_bb else "Within Bands",
            "Squeeze": str((upper_bb - lower_bb) < history['Upper_BB'].iloc[-20] - history['Lower_BB'].iloc[-20]),
            "Final_Trade_Signal": bb_signal
        }
        
        ms_details = {
            "Support": float(support),
            "Resistance": float(resistance),
            "Support_Distance": float(current_price - support),
            "Resistance_Distance": float(resistance - current_price),
            "Position": "Near Support" if (current_price - support) < (resistance - current_price) else "Near Resistance",
            "Final_Trade_Signal": ms_signal
        }
        
        fibo_details = {
            "Levels": {k: float(v) for k, v in fib_levels.items()},
            "Current_Level": next((k for k, v in fib_levels.items() if v >= current_price), "Above 1.0"),
            "Final_Trade_Signal": fib_signal
        }
        
        # Calculate fundamental metrics (simplified version)
        # In a real implementation, you'd want to do proper fundamental analysis
        try:
            # Get stock info from Yahoo Finance
            info = stock.info if hasattr(stock, 'info') else {}
            
            eps = info.get('trailingEPS', None)
            pe_ratio = info.get('trailingPE', None)
            revenue_growth = info.get('revenueGrowth', None)
            debt_to_equity = info.get('debtToEquity', None) / 100 if info.get('debtToEquity', None) else None
            earnings_growth = info.get('earningsGrowth', None) * 100 if info.get('earningsGrowth', None) else None
            
            # Determine status for each metric
            eps_status = "good" if eps and eps > 0 else "bad" if eps and eps <= 0 else "none"
            pe_ratio_status = "good" if pe_ratio and pe_ratio < 25 else "bad" if pe_ratio and pe_ratio >= 25 else "none"
            revenue_growth_status = "good" if revenue_growth and revenue_growth > 0.10 else "bad" if revenue_growth and revenue_growth <= 0.10 else "none"
            debt_to_equity_status = "good" if debt_to_equity and debt_to_equity < 1.5 else "bad" if debt_to_equity and debt_to_equity >= 1.5 else "none"
            earnings_growth_status = "good" if earnings_growth and earnings_growth > 10 else "bad" if earnings_growth and earnings_growth <= 10 else "none"
            
            # Calculate overall fundamental score (simplified)
            fa_score_components = [
                15 if eps_status == "good" else 0,
                15 if pe_ratio_status == "good" else 0,
                15 if revenue_growth_status == "good" else 0,
                15 if debt_to_equity_status == "good" else 0,
                15 if earnings_growth_status == "good" else 0
            ]
            
            overall_fa_score = sum(fa_score_components) / len(fa_score_components) * 15  # Scale to 15% of total
            
            fundamental_analysis = {
                "eps": eps,
                "pe_ratio": pe_ratio,
                "revenue_growth": revenue_growth,
                "debt_to_equity": debt_to_equity,
                "earnings_growth": earnings_growth,
                "eps_status": eps_status,
                "pe_ratio_status": pe_ratio_status,
                "revenue_growth_status": revenue_growth_status,
                "debt_to_equity_status": debt_to_equity_status,
                "earnings_growth_status": earnings_growth_status,
                "overall_fa_score": overall_fa_score
            }
        except Exception as e:
            logger.error(f"Error calculating fundamental metrics: {e}")
            fundamental_analysis = {
                "eps": None,
                "pe_ratio": None,
                "revenue_growth": None,
                "debt_to_equity": None,
                "earnings_growth": None,
                "eps_status": "none",
                "pe_ratio_status": "none",
                "revenue_growth_status": "none",
                "debt_to_equity_status": "none",
                "earnings_growth_status": "none", 
                "overall_fa_score": 7.5  # Default to middle score
            }
        
        # Mock news sentiment (in a real implementation, you'd use actual news API and sentiment analysis)
        news_score = 50  # Neutral score as a default
        
        # Calculate overall technical score
        ta_components = {
            "RSI": 15 if rsi_signal == "Buy" else 0 if rsi_signal == "DBuy" else 7.5,
            "MACD": 15 if macd_signal == "Buy" else 0 if macd_signal == "DBuy" else 7.5,
            "EMA": 15 if ema_signal == "Buy" else 0 if ema_signal == "DBuy" else 7.5,
            "BB": 15 if bb_signal == "Buy" else 0 if bb_signal == "DBuy" else 7.5,
            "MS": 10 if ms_signal == "Buy" else 0 if ms_signal == "DBuy" else 5,
            "Fibo": 10 if fib_signal == "Buy" else 0 if fib_signal == "DBuy" else 5
        }
        
        overall_ta_score = sum(ta_components.values()) / 80 * 80  # Scale to 80% of total
        
        # Calculate combined score
        # Ensure overall_fa_score has a value
        overall_fa_score = overall_fa_score if 'overall_fa_score' in locals() else 7.5  # Default if not set
        combined_overall_score = overall_ta_score + overall_fa_score + (news_score * 0.05)  # 80% TA, 15% FA, 5% News
        
        # Determine overall signal
        if combined_overall_score > 60:
            combined_overall_signal = "Buy"
        elif combined_overall_score < 40:
            combined_overall_signal = "DBuy"
        else:
            combined_overall_signal = "Neutral"
        
        # Calculate candlestick data for charting
        candlestick_data = []
        for index, row in history.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            candlestick_data.append({
                "x": date_str,
                "y": [float(row['Open']), float(row['High']), float(row['Low']), float(row['Close'])],
                "rsi": float(row['RSI']) if not np.isnan(row['RSI']) else None,
                "macd": float(row['MACD']) if not np.isnan(row['MACD']) else None,
                "macdsignal": float(row['MACD_Signal']) if not np.isnan(row['MACD_Signal']) else None,
                "atr": float(row['ATR']) if not np.isnan(row['ATR']) else None,
                "ema9": float(row['EMA_9']) if not np.isnan(row['EMA_9']) else None,
                "ema20": float(row['EMA_20']) if not np.isnan(row['EMA_20']) else None,
                "ema50": float(row['EMA_50']) if not np.isnan(row['EMA_50']) else None
            })
        
        # Generate fake prediction data for demo purposes
        # In a real implementation, you'd use an actual ML model
        last_date = history.index[-1].strftime('%Y-%m-%d')
        last_price = history['Close'].iloc[-1]
        
        prediction_dates = []
        prediction_prices = []
        
        # Generate 15 days of prediction
        for i in range(1, 16):
            next_date = (history.index[-1] + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            # Simple random walk prediction for demo
            next_price = last_price * (1 + np.random.normal(0.001, 0.015))
            
            prediction_dates.append(next_date)
            prediction_prices.append(float(next_price))
            
            last_price = next_price
        
        # Find maximum predicted price and date
        max_value = max(prediction_prices)
        max_index = prediction_prices.index(max_value)
        max_date = prediction_dates[max_index]
        
        # Calculate pivot point percentages
        pivot_point_percents = {
            "p1_pect": calculate_percentage_change(pivot_points["pivot"], current_price),
            "s1_pect": calculate_percentage_change(pivot_points["s1"], current_price),
            "s2_pect": calculate_percentage_change(pivot_points["s2"], current_price),
            "s3_pect": calculate_percentage_change(pivot_points["s3"], current_price),
            "r1_pect": calculate_percentage_change(pivot_points["r1"], current_price),
            "r2_pect": calculate_percentage_change(pivot_points["r2"], current_price),
            "r3_pect": calculate_percentage_change(pivot_points["r3"], current_price)
        }
        
        # Combine all data
        result = {
            "ticker": ticker,
            "company_name": company_name,
            "last_trading_date": history.index[-1].strftime('%Y-%m-%d'),
            "live_price": float(current_price),
            "price_change": float(price_change),
            "percentage_change": float(percentage_change),
            
            # Technical signals
            "RSI": rsi_details,
            "MACD": macd_details,
            "ATR": atr_details,
            "EMA": ema_details,
            "BB": bb_details,
            "MS": ms_details,
            "Fibonacci": fibo_details,
            
            # Strategy-specific data
            "rsistrategy": rsi_details,
            "macdstrategy": macd_details,
            "atrstrategy": atr_details,
            "emastrategy": ema_details,
            "bbstrategy": bb_details,
            "msstrategy": ms_details,
            "fibostrategy": fibo_details,
            
            # Overall scores
            "overall_ta_score": float(overall_ta_score),
            "overall_fa_score": float(overall_fa_score),
            "news_score": float(news_score),
            "combined_overall_score": float(combined_overall_score),
            "combined_overall_signal": combined_overall_signal,
            
            # Trading info
            "tradingInfo": {
                "entry_point": float(entry_point),
                "stop_loss": float(stop_loss),
                "target_price": float(target_price),
                "pivot_point": float(pivot_points["pivot"]),
                "support1": float(pivot_points["s1"]),
                "support2": float(pivot_points["s2"]),
                "support3": float(pivot_points["s3"]),
                "resistance1": float(pivot_points["r1"]),
                "resistance2": float(pivot_points["r2"]),
                "resistance3": float(pivot_points["r3"]),
                "p1_pect": float(pivot_point_percents["p1_pect"]),
                "s1_pect": float(pivot_point_percents["s1_pect"]),
                "s2_pect": float(pivot_point_percents["s2_pect"]),
                "s3_pect": float(pivot_point_percents["s3_pect"]),
                "r1_pect": float(pivot_point_percents["r1_pect"]),
                "r2_pect": float(pivot_point_percents["r2_pect"]),
                "r3_pect": float(pivot_point_percents["r3_pect"]),
                "remarks": f"Based on the {timeframe}-term analysis, the stock is currently in a {combined_overall_signal.lower()} phase."
            },
            
            # Chart data
            "candlestick_data": candlestick_data,
            "prediction_dates": prediction_dates,
            "prediction_prices": prediction_prices,
            "max_date": max_date,
            "max_value": float(max_value),
            
            # Fundamental analysis
            "fundamental_analysis": fundamental_analysis,
            
            # Demo news data
            "googlenews": {
                "news": [
                    {
                        "content": {
                            "title": f"Analyst Upgrades {ticker} After Strong Earnings",
                            "summary": f"{company_name} reported better than expected earnings for the quarter."
                        }
                    },
                    {
                        "content": {
                            "title": f"{ticker} Announces New Product Line",
                            "summary": f"{company_name} is expanding its product offerings with new innovations."
                        }
                    },
                    {
                        "content": {
                            "title": f"Market Outlook: How {ticker} Fits in Your Portfolio",
                            "summary": "Analysis of current market conditions and investment strategies."
                        }
                    }
                ]
            }
        }
        
        logger.info(f"Successfully completed swing trading analysis for {ticker}")
        return result
        
    except Exception as e:
        logger.error(f"Error in swing trading analysis for {ticker}: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def analyze_tickers(tickers, timeframe='short'):
    """
    Analyze multiple tickers for swing trading.
    
    Args:
        tickers (list): List of stock ticker symbols
        timeframe (str): Trading timeframe ('short', 'medium', 'long')
        
    Returns:
        list: List of analysis results for each ticker
    """
    # Call the service implementation
    return service_analyze_swing_trading_batch(tickers, timeframe)

def create_app():
    """
    Create Flask application.
    
    Returns:
        Flask: Flask application
    """
    app = Flask(__name__)
    CORS(app)
    
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
            
            # Normalize timeframe for consistency
            timeframe = timeframe.lower().strip()
            
            # Map normalized timeframes to standard values
            if 'medium' in timeframe:
                timeframe = 'medium'
            elif 'long' in timeframe:
                timeframe = 'long'
            else:
                timeframe = 'short'
            
            logger.info(f"Analyzing tickers with normalized timeframe: {timeframe}")
            
            if not tickers:
                return jsonify({"error": "No tickers provided"}), 400
            
            results = analyze_tickers(tickers, timeframe)
            return jsonify(results)
        
        except Exception as e:
            logger.error(f"Error in swing trading endpoint: {e}")
            return jsonify({"error": str(e)}), 500
    
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
            
            # Normalize timeframe for consistency
            timeframe = timeframe.lower().strip()
            
            # Map normalized timeframes to standard values
            if 'medium' in timeframe:
                timeframe = 'medium'
            elif 'long' in timeframe:
                timeframe = 'long'
            else:
                timeframe = 'short'
                
            logger.info(f"Analyzing ticker {ticker} with normalized timeframe: {timeframe}")
            
            result = analyze_swing_trading(ticker, timeframe)
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error in swing trading single endpoint: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/swing-trade', methods=['POST'])
    def swing_trade():
        try:
            tickers = request.json.get('tickers', [])
            results = analyze_swing_trading_batch(tickers)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error in swing trading endpoint: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app

# Create Flask app
app = create_app()

# Run server in development mode
if __name__ == '__main__':
    app.run(debug=True, port=5015)  # This runs the Flask server