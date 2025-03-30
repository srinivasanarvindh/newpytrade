# ...existing code...

def get_shorttermswingsignal(ticker, timeframe='short'):
    """
    Get short-term swing trading signal for a ticker.
    
    Args:
        ticker (str): The stock ticker symbol
        timeframe (str): Trading timeframe - 'short', 'medium', or 'long'
    
    Returns:
        dict: Trading signals and analysis data
    """
    logger.info(f"Getting live signal for {ticker} with timeframe {timeframe}")
    try:
        # Download historical data directly from source
        stock = yf.Ticker(ticker)
        
        # Adjust the period based on timeframe
        if timeframe == 'medium':
            period = '6mo'  # Medium-term: 6 months of data
            logger.info(f"Using 6-month data period for medium-term analysis of {ticker}")
        elif timeframe == 'long':
            period = '1y'   # Long-term: 1 year of data
            logger.info(f"Using 1-year data period for long-term analysis of {ticker}")
        else:
            period = '3mo'  # Short-term: 3 months of data (default)
            logger.info(f"Using 3-month data period for short-term analysis of {ticker}")
        
        # Force cache to be refreshed by setting force_refresh
        logger.info(f"Requesting fresh live data for {ticker}")
        history = stock.history(period=period)
        
        if history.empty:
            logger.warning(f"No historical data found for {ticker}")
            return {"error": "No historical data available", "ticker": ticker}
            
        # Log data retrieval success
        logger.info(f"Successfully retrieved {len(history)} historical data points for {ticker}")
            
        # Calculate technical indicators
        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        history['SMA_200'] = history['Close'].rolling(window=200).mean()
        
        # Get the latest data point
        latest_data = history.iloc[-1]
        
        # Determine basic signal
        signal = "BUY" if latest_data['SMA_50'] > latest_data['SMA_200'] else "SELL"
        logger.debug(f"Generated signal for {ticker}: {signal}")

        # --- Calculate Technical Indicators ---
        df_rsi = rsi_strategies(history.copy())
        df_macd = macd_strategies(history.copy())
        df_atr = atr_strategies(history.copy())
        df_ema = ema_strategies(history.copy())
        df_ms = marketstructure_strategies(history.copy())
        df_fibo = fibonacci_strategies(history.copy())
        df_bb = bollinger_strategies(history.copy())

        # --- Get chart predictions ---
        # Use live data only for predictions
        try:
            prediction_data = predict(history.copy(), timeframe=timeframe)
        except Exception as e:
            logger.error(f"Error in prediction function: {e}", exc_info=True)
            # Continue without prediction data if there's an error
            prediction_data = {"prediction_prices": [], "prediction_dates": []}

        # Format prediction data
        if isinstance(prediction_data, dict):
            prediction_prices = prediction_data.get("prediction_prices", [])
            prediction_dates = prediction_data.get("prediction_dates", [])
        elif isinstance(prediction_data, np.ndarray):
            # Convert NumPy array to list and handle NaN values
            prediction_prices = [float(p) if not np.isnan(p) else None for p in prediction_data]
            prediction_dates = []
        else:
            prediction_prices = []
            prediction_dates = []

        # --- Get Fundamental Data ---
        # Get real-time fundamental data, no fallbacks
        fundamental_data = get_stock_details(ticker)
        
        # --- News Sentiment Analysis ---
        news_data = get_latest_news(ticker) or []
        sentiment_score = analyze_news_sentiment(news_data)
        news_score = convert_sentiment_to_news_score(sentiment_score)

        # --- Structure Output ---
        output = {
            "ticker": ticker,
            "signal": signal,
            "timeframe": timeframe,
            "latest_close": float(latest_data['Close']),
            "SMA_50": float(latest_data['SMA_50']) if not math.isnan(latest_data['SMA_50']) else None,
            "SMA_200": float(latest_data['SMA_200']) if not math.isnan(latest_data['SMA_200']) else None,
            "candlestick_data": history[["Open", "High", "Low", "Close"]].to_dict('records'),
            "prediction_prices": prediction_prices,
            "prediction_dates": prediction_dates,
            "fundamental_analysis": fundamental_data,
            "news": news_data,
            "news_sentiment_score": sentiment_score,
            "news_score": news_score,
            "rsi_values": df_rsi['RSI_14'].iloc[-1] if not df_rsi.empty else None,
            "macd_values": df_macd['MACD'].iloc[-1] if not df_macd.empty else None,
            "overall_ta_score": calculate_overall_score([
                df_rsi, df_macd, df_atr, df_ema, df_ms, df_fibo, df_bb
            ]),
            # Including all technical indicator signals
            "RSI": df_rsi.iloc[-1].to_dict() if not df_rsi.empty else {},
            "MACD": df_macd.iloc[-1].to_dict() if not df_macd.empty else {},
            "ATR": df_atr.iloc[-1].to_dict() if not df_atr.empty else {},
            "EMA": df_ema.iloc[-1].to_dict() if not df_ema.empty else {},
            "MS": df_ms.iloc[-1].to_dict() if not df_ms.empty else {},
            "Fibonacci": df_fibo.iloc[-1].to_dict() if not df_fibo.empty else {},
            "BB": df_bb.iloc[-1].to_dict() if not df_bb.empty else {},
            # Add calculated data for stop loss and take profit
            "stoploss": calculate_stoploss(history, signal),
            "takeprofit": calculate_takeprofit(history, signal),
            # Add combined overall signal based on all indicators
            "combined_overall_signal": calculate_combined_signal([
                df_rsi, df_macd, df_atr, df_ema, df_ms, df_fibo, df_bb
            ]),
            "combined_overall_score": calculate_combined_score([
                df_rsi, df_macd, df_atr, df_ema, df_ms, df_fibo, df_bb
            ], fundamental_data, news_score)
        }
        
        logger.info(f"Successfully generated live signals for {ticker} with timeframe {timeframe}")
        return output
    except Exception as e:
        logger.error(f"Error generating live signal for {ticker}: {e}", exc_info=True)
        return {"error": str(e), "ticker": ticker}

# Add a helper function to get the latest news directly
def get_latest_news(ticker, max_items=5):
    """
    Get the latest news for a ticker directly from a news API
    
    Args:
        ticker (str): Stock ticker symbol
        max_items (int): Maximum number of news items to return
        
    Returns:
        list: List of news items
    """
    try:
        # Use Yahoo Finance first
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if (news and len(news) > 0):
            formatted_news = []
            for item in news[:max_items]:
                formatted_news.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "date": datetime.datetime.fromtimestamp(item.get("providerPublishTime", 0)).strftime("%Y-%m-%d"),
                    "source": item.get("publisher", "Yahoo Finance"),
                    "url": item.get("link", "")
                })
            return formatted_news
            
        # If no news from Yahoo, return empty list
        return []
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

# ...existing code...
