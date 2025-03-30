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