def generate_bse_constituents(index_name):
    """
    Generate constituent stocks for BSE indices with distinct data for each index.
    Args:
        index_name (str): Name of the BSE index
    Returns:
        list: List of constituent stocks
    """
    # Define common BSE/S&P BSE stocks with proper details
    bse_stocks = []
    
    # BSE SENSEX stocks or S&P BSE - 30 (30 stocks)
    if index_name == "BSE SENSEX" or index_name == "S&P BSE - 30":
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
        # Include some stocks from BSE SENSEX but not all, to make it more distinct
        bse_stocks = [
            {"symbol": "ADANIPORTS", "company": "Adani Ports and Special Economic Zone Ltd.", "exchange": "BSE", "price": 780.0, "change": 15.0, "changePercent": 2.0, "currency": "INR", "sector": "Infrastructure"},
            {"symbol": "HCLTECH", "company": "HCL Technologies Ltd.", "exchange": "BSE", "price": 1180.0, "change": -12.0, "changePercent": -1.0, "currency": "INR", "sector": "IT"},
            {"symbol": "DRREDDY", "company": "Dr. Reddy's Laboratories Ltd.", "exchange": "BSE", "price": 5200.0, "change": 80.0, "changePercent": 1.6, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "CIPLA", "company": "Cipla Ltd.", "exchange": "BSE", "price": 1280.0, "change": -15.0, "changePercent": -1.2, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "EICHERMOT", "company": "Eicher Motors Ltd.", "exchange": "BSE", "price": 3400.0, "change": 50.0, "changePercent": 1.5, "currency": "INR", "sector": "Automobile"},
            {"symbol": "BRITANNIA", "company": "Britannia Industries Ltd.", "exchange": "BSE", "price": 4600.0, "change": -65.0, "changePercent": -1.4, "currency": "INR", "sector": "FMCG"},
            {"symbol": "GRASIM", "company": "Grasim Industries Ltd.", "exchange": "BSE", "price": 1950.0, "change": 25.0, "changePercent": 1.3, "currency": "INR", "sector": "Diversified"},
            {"symbol": "BAJAJ-AUTO", "company": "Bajaj Auto Ltd.", "exchange": "BSE", "price": 4800.0, "change": -70.0, "changePercent": -1.5, "currency": "INR", "sector": "Automobile"},
            {"symbol": "HEROMOTOCO", "company": "Hero MotoCorp Ltd.", "exchange": "BSE", "price": 2850.0, "change": 35.0, "changePercent": 1.2, "currency": "INR", "sector": "Automobile"},
            {"symbol": "DIVISLAB", "company": "Divi's Laboratories Ltd.", "exchange": "BSE", "price": 3600.0, "change": -45.0, "changePercent": -1.3, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "AUROPHARMA", "company": "Aurobindo Pharma Ltd.", "exchange": "BSE", "price": 960.0, "change": 15.0, "changePercent": 1.6, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "LUPIN", "company": "Lupin Limited", "exchange": "BSE", "price": 1150.0, "change": 22.0, "changePercent": 1.9, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "DABUR", "company": "Dabur India Ltd.", "exchange": "BSE", "price": 550.0, "change": 8.0, "changePercent": 1.5, "currency": "INR", "sector": "FMCG"},
            {"symbol": "GODREJCP", "company": "Godrej Consumer Products Ltd.", "exchange": "BSE", "price": 980.0, "change": 18.0, "changePercent": 1.9, "currency": "INR", "sector": "FMCG"},
            {"symbol": "MARICO", "company": "Marico Ltd.", "exchange": "BSE", "price": 530.0, "change": 9.5, "changePercent": 1.8, "currency": "INR", "sector": "FMCG"}
        ]
    # S&P BSE - 500
    elif index_name == "S&P BSE - 500":
        # Use a completely different set of stocks for S&P BSE - 500
        bse_stocks = [
            {"symbol": "ADANIPOWER", "company": "Adani Power Ltd.", "exchange": "BSE", "price": 345.20, "change": 12.35, "changePercent": 3.71, "currency": "INR", "sector": "Power"},
            {"symbol": "CANBK", "company": "Canara Bank", "exchange": "BSE", "price": 420.15, "change": 8.25, "changePercent": 2.00, "currency": "INR", "sector": "Banking"},
            {"symbol": "IOC", "company": "Indian Oil Corporation Ltd.", "exchange": "BSE", "price": 122.60, "change": 2.15, "changePercent": 1.79, "currency": "INR", "sector": "Oil & Gas"},
            {"symbol": "TATAPOWER", "company": "Tata Power Company Ltd.", "exchange": "BSE", "price": 328.75, "change": 7.85, "changePercent": 2.45, "currency": "INR", "sector": "Power"},
            {"symbol": "COALINDIA", "company": "Coal India Ltd.", "exchange": "BSE", "price": 380.25, "change": 4.20, "changePercent": 1.12, "currency": "INR", "sector": "Mining"},
            {"symbol": "BANKBARODA", "company": "Bank of Baroda", "exchange": "BSE", "price": 230.45, "change": 5.60, "changePercent": 2.49, "currency": "INR", "sector": "Banking"},
            {"symbol": "VEDL", "company": "Vedanta Limited", "exchange": "BSE", "price": 305.15, "change": 9.30, "changePercent": 3.14, "currency": "INR", "sector": "Mining"},
            {"symbol": "RECLTD", "company": "REC Limited", "exchange": "BSE", "price": 280.90, "change": 6.85, "changePercent": 2.50, "currency": "INR", "sector": "Finance"},
            {"symbol": "NHPC", "company": "NHPC Limited", "exchange": "BSE", "price": 65.30, "change": 1.45, "changePercent": 2.27, "currency": "INR", "sector": "Power"},
            {"symbol": "NMDC", "company": "NMDC Limited", "exchange": "BSE", "price": 180.55, "change": 3.80, "changePercent": 2.15, "currency": "INR", "sector": "Mining"},
            {"symbol": "HINDALCO", "company": "Hindalco Industries Ltd.", "exchange": "BSE", "price": 560.25, "change": 12.40, "changePercent": 2.26, "currency": "INR", "sector": "Metals"},
            {"symbol": "ONGC", "company": "Oil and Natural Gas Corporation Ltd.", "exchange": "BSE", "price": 245.35, "change": 4.25, "changePercent": 1.76, "currency": "INR", "sector": "Oil & Gas"},
            {"symbol": "PFC", "company": "Power Finance Corporation Ltd.", "exchange": "BSE", "price": 310.45, "change": 8.30, "changePercent": 2.75, "currency": "INR", "sector": "Finance"},
            {"symbol": "SAIL", "company": "Steel Authority of India Ltd.", "exchange": "BSE", "price": 110.25, "change": 2.45, "changePercent": 2.27, "currency": "INR", "sector": "Metals"},
            {"symbol": "IRFC", "company": "Indian Railway Finance Corporation Ltd.", "exchange": "BSE", "price": 98.45, "change": 3.25, "changePercent": 3.41, "currency": "INR", "sector": "Finance"}
        ]
    else:
        # Generate a generic set of stocks for any other BSE index
        bse_stocks = [
            {"symbol": "BIOCON", "company": "Biocon Limited", "exchange": "BSE", "price": 285.75, "change": 5.40, "changePercent": 1.93, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "TATAELXSI", "company": "Tata Elxsi Limited", "exchange": "BSE", "price": 7850.25, "change": 165.30, "changePercent": 2.15, "currency": "INR", "sector": "IT"},
            {"symbol": "MINDTREE", "company": "MindTree Limited", "exchange": "BSE", "price": 4250.60, "change": 78.45, "changePercent": 1.88, "currency": "INR", "sector": "IT"},
            {"symbol": "LALPATHLAB", "company": "Dr. Lal PathLabs Ltd.", "exchange": "BSE", "price": 2450.15, "change": 36.85, "changePercent": 1.53, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "METROPOLIS", "company": "Metropolis Healthcare Ltd.", "exchange": "BSE", "price": 1580.45, "change": 22.75, "changePercent": 1.46, "currency": "INR", "sector": "Healthcare"},
            {"symbol": "DIXON", "company": "Dixon Technologies (India) Ltd.", "exchange": "BSE", "price": 5650.30, "change": 145.25, "changePercent": 2.64, "currency": "INR", "sector": "Consumer Durables"},
            {"symbol": "TRENT", "company": "Trent Ltd.", "exchange": "BSE", "price": 3420.85, "change": 65.40, "changePercent": 1.95, "currency": "INR", "sector": "Retail"},
            {"symbol": "AFFLE", "company": "Affle (India) Ltd.", "exchange": "BSE", "price": 1150.25, "change": 29.45, "changePercent": 2.63, "currency": "INR", "sector": "Technology"},
            {"symbol": "DEEPAKNTR", "company": "Deepak Nitrite Ltd.", "exchange": "BSE", "price": 2180.60, "change": 43.25, "changePercent": 2.02, "currency": "INR", "sector": "Chemicals"},
            {"symbol": "HAPPSTMNDS", "company": "Happiest Minds Technologies Ltd.", "exchange": "BSE", "price": 860.75, "change": 18.45, "changePercent": 2.19, "currency": "INR", "sector": "IT"}
        ]
        
    return bse_stocks