"""
PyTrade - WebSocket Server Module

This module implements a WebSocket server for delivering real-time stock data updates 
to connected clients. It handles client connections, subscription management, and 
periodic data fetching from external financial data sources.

Key features:
- Real-time stock price updates
- Client subscription management 
- Automatic data refresh
- Support for global markets, with special handling for Indian stocks (NSE/BSE)
- Connection health monitoring with ping/pong

Author: PyTrade Development Team
Version: 1.0.0
Date: March 25, 2025
License: Proprietary
"""
import asyncio
import json
import logging
import websockets
import random
import time
import yfinance as yf
from datetime import datetime
import argparse
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients
connected_clients = set()
# Store subscriptions: { symbol: [client1, client2, ...] }
subscriptions = {}
# Store latest price data: { symbol: { price, change, ... } }
latest_prices = {}

async def handle_websocket_connection(websocket):
    """
    Handle a WebSocket connection.
    
    Args:
        websocket: The WebSocket connection.
    """
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")
    
    # Add client to connected clients
    connected_clients.add(websocket)
    client_subscriptions = set()
    
    try:
        # Listen for messages from the client
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get('action')
                symbol = data.get('symbol')
                
                if action == 'subscribe' and symbol:
                    # Subscribe to a symbol
                    if symbol not in subscriptions:
                        subscriptions[symbol] = set()
                    subscriptions[symbol].add(websocket)
                    client_subscriptions.add(symbol)
                    
                    # If we have latest data, send it immediately
                    if symbol in latest_prices:
                        await websocket.send(json.dumps({
                            'type': 'price_update',
                            'symbol': symbol,
                            'data': latest_prices[symbol]
                        }))
                    
                    # Fetch initial data if needed
                    if symbol not in latest_prices:
                        await fetch_stock_data(symbol)
                    
                    logger.info(f"Client {client_id} subscribed to {symbol}")
                    
                elif action == 'unsubscribe' and symbol:
                    # Unsubscribe from a symbol
                    if symbol in subscriptions and websocket in subscriptions[symbol]:
                        subscriptions[symbol].remove(websocket)
                        client_subscriptions.discard(symbol)
                        logger.info(f"Client {client_id} unsubscribed from {symbol}")
                
                elif action == 'ping':
                    # Ping to keep connection alive
                    await websocket.send(json.dumps({'type': 'pong'}))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for client {client_id}")
    finally:
        # Clean up when client disconnects
        for symbol in client_subscriptions:
            if symbol in subscriptions and websocket in subscriptions[symbol]:
                subscriptions[symbol].remove(websocket)
        connected_clients.discard(websocket)
        logger.info(f"Client {client_id} disconnected, removed from {len(client_subscriptions)} subscriptions")

async def fetch_stock_data(symbol):
    """
    Fetch stock data for a symbol.
    
    Args:
        symbol (str): Stock symbol to fetch data for.
    """
    try:
        # Try with suffix for Indian stocks first
        ticker_symbol = symbol
        if not "." in symbol:
            # For Indian stocks, we'll try NSE by default
            indian_exchanges = {".NS": "NSE", ".BO": "BSE"}
            for suffix, exchange in indian_exchanges.items():
                try:
                    ticker = yf.Ticker(f"{symbol}{suffix}")
                    info = ticker.info
                    if info and 'regularMarketPrice' in info:
                        ticker_symbol = f"{symbol}{suffix}"
                        break
                except Exception:
                    continue
        
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or 'regularMarketPrice' not in info:
            logger.warning(f"No data available for {symbol}")
            return
        
        price = info.get('regularMarketPrice')
        previous_close = info.get('regularMarketPreviousClose')
        change = price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        # Include date, time, and timezone information in the timestamp
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S %Z')
        
        price_data = {
            'price': price,
            'change': change,
            'changePercent': change_percent,
            'high': info.get('dayHigh', price),
            'low': info.get('dayLow', price),
            'volume': info.get('regularMarketVolume', 0),
            'timestamp': current_time,  # Show full date, time and timezone
            'currency': info.get('currency', 'USD')
        }
        
        latest_prices[symbol] = price_data
        
        # Broadcast to subscribed clients
        if symbol in subscriptions:
            message = json.dumps({
                'type': 'price_update',
                'symbol': symbol,
                'data': price_data
            })
            
            await asyncio.gather(
                *[client.send(message) for client in subscriptions[symbol]],
                return_exceptions=True
            )
            
        logger.info(f"Updated price for {symbol}: {price}")
        return price_data
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

async def update_prices():
    """
    Update prices periodically for all subscribed symbols.
    """
    while True:
        update_tasks = []
        for symbol in list(subscriptions.keys()):
            # Only update if there are subscribers
            if subscriptions[symbol]:
                update_tasks.append(fetch_stock_data(symbol))
        
        if update_tasks:
            await asyncio.gather(*update_tasks, return_exceptions=True)
        
        # Wait before next update (15 seconds)
        await asyncio.sleep(15)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="WebSocket Server for PyTrade")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--port", type=int, help="Port to listen on")
    parser.add_argument("--host", type=str, help="Host to bind to")
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from file."""
    if not config_path or not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

async def start_websocket_server(host='0.0.0.0', port=5012):
    """
    Start the WebSocket server.
    
    Args:
        host (str): Host to bind to.
        port (int): Port to bind to.
    """
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Start price updater task
    asyncio.create_task(update_prices())
    
    # Start WebSocket server with retry logic
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with websockets.serve(handle_websocket_connection, host, port):
                logger.info(f"WebSocket server successfully started on {host}:{port}")
                await asyncio.Future()  # Run forever
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.warning(f"Port {port} already in use, trying port {port+1}")
                port += 1
                retry_count += 1
            else:
                logger.error(f"WebSocket server error: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

def run_websocket_server():
    """Run the WebSocket server."""
    args = parse_args()
    
    # Load configuration from file if provided
    config = load_config(args.config)
    
    # Get host and port from command line arguments, config file, or environment variables
    host = args.host or config.get("host") or os.environ.get("WEBSOCKET_HOST", "0.0.0.0")
    port = args.port or config.get("port") or int(os.environ.get("WEBSOCKET_PORT", 5012))
    
    # Set up asyncio event loop and run the server
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_websocket_server(host, port))
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped by user")
    finally:
        loop.close()

if __name__ == "__main__":
    run_websocket_server()