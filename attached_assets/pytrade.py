from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import talib
import math
import requests
from priceprediction import predict_return
#from intradaytrading import predictintraday
from shorttermswingtrading import get_shorttermswingsignal

app = Flask(__name__)

@app.route('/trade/shorttermswingtrading', methods=['POST'])
def analyze_all():
    """
    Analyze all given tickers for swing trading signals.
    
    Request Body:
        {
            "ticker": ["AAPL", "MSFT"],
            "timeframe": "short" | "medium" | "long"
        }
    
    Returns:
        JSON: A list of results with signals for each ticker.
    """
    try:
        data = request.get_json()
        logger.info(f"Received swing trading request: {data}")
        
        # Validate input
        if not data or 'ticker' not in data:
            logger.error("Missing 'ticker' in request data.")
            return jsonify({"error": "Missing ticker data"}), 400
        
        tickers = data['ticker']
        
        # Normalize timeframe parameter
        timeframe = data.get('timeframe', 'short').lower().strip()
        
        # Validate timeframe and provide clear debug info
        if timeframe not in ['short', 'medium', 'long']:
            logger.warning(f"Received invalid timeframe '{timeframe}'. Defaulting to 'short'")
            timeframe = 'short'
        else:
            logger.info(f"Using timeframe: {timeframe}")
        
        # Log that we're using live data
        logger.info(f"Using LIVE data sources only for {len(tickers)} tickers with {timeframe} timeframe")
        
        # Initialize an empty list to store results
        results = []
        
        # Process each ticker - with live data only
        for ticker in tickers:
            try:
                logger.info(f"Processing ticker: {ticker} with timeframe: {timeframe}")
                
                # Get live data for this ticker directly from the source
                result = get_shorttermswingsignal(ticker, timeframe=timeframe)
                
                # Add to results
                results.append({
                    "symbol": ticker,
                    "result": result
                })
                
                logger.info(f"Successfully processed {ticker}")
                
            except Exception as e:
                # Log the error but continue with other tickers
                logger.error(f"Error processing {ticker}: {e}", exc_info=True)
                results.append({
                    "symbol": ticker,
                    "result": {
                        "error": f"Failed to process: {str(e)}",
                        "ticker": ticker
                    }
                })
        
        logger.info(f"Completed processing {len(tickers)} tickers with live data")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in analyze_all: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def get_nifty100():
    nifty100_list = [
          {"company": "ABB India Ltd", "symbol": "ABB.NS"},
          {"company": "Adani Enterprises Ltd", "symbol": "ADANIENT.NS"},
          {"company": "Adani Total Gas Ltd", "symbol": "ATGL.NS"},
          {"company": "Adani Green Energy Ltd", "symbol": "ADANIGREEN.NS"},
          {"company": "Adani Ports and Special Economic Zone Ltd", "symbol": "ADANIPORTS.NS"},
          {"company": "Adani Power Ltd", "symbol": "ADANIPOWER.NS"},
          {"company": "Adani Energy Solutions Ltd", "symbol": "ADANIENSOL.NS"},
          {"company": "Ambuja Cements Ltd", "symbol": "AMBUJACEM.NS"},
          {"company": "Apollo Hospitals Enterprise Ltd", "symbol": "APOLLOHOSP.NS"},
          {"company": "Asian Paints Ltd", "symbol": "ASIANPAINT.NS"},
          {"company": "Axis Bank Ltd", "symbol": "AXISBANK.NS"},
          {"company": "Bajaj Auto Limited", "symbol": "BAJAJ-AUTO.NS"},
          {"company": "Bajaj Finserv Ltd", "symbol": "BAJAJFINSV.NS"},
          {"company": "Bajaj Holdings and Investment Ltd", "symbol": "BAJAJHLDNG.NS"},
          {"company": "Bajaj Finance Ltd", "symbol": "BAJFINANCE.NS"},
          {"company": "Bank of Baroda Ltd", "symbol": "BANKBARODA.NS"},
          {"company": "Bharat Electronics Ltd", "symbol": "BEL.NS"},
          {"company": "Bharti Airtel Ltd", "symbol": "BHARTIARTL.NS"},
          {"company": "Bharat Heavy Electricals Ltd", "symbol": "BHEL.NS"},
          {"company": "Bosch Ltd", "symbol": "BOSCHLTD.NS"},
          {"company": "Bharat Petroleum Corporation Ltd", "symbol": "BPCL.NS"},
          {"company": "Britannia Industries Ltd", "symbol": "BRITANNIA.NS"},
          {"company": "Zydus Lifesciences Ltd", "symbol": "ZYDUSLIFE.NS"},
          {"company": "Canara Bank Ltd", "symbol": "CANBK.NS"},
          {"company": "Cholamandalam Investment and Finance Company Ltd", "symbol": "CHOLAFIN.NS"},
          {"company": "Cipla Ltd", "symbol": "CIPLA.NS"},
          {"company": "Coal India Ltd", "symbol": "COALINDIA.NS"},
          {"company": "Dabur India Ltd", "symbol": "DABUR.NS"},
          {"company": "Divi's Laboratories Ltd", "symbol": "DIVISLAB.NS"},
          {"company": "DLF Ltd", "symbol": "DLF.NS"},
          {"company": "Avenue Supermarts Ltd", "symbol": "DMART.NS"},
          {"company": "Dr Reddy's Laboratories Ltd", "symbol": "DRREDDY.NS"},
          {"company": "Eicher Motors Ltd", "symbol": "EICHERMOT.NS"},
          {"company": "Gail (India) Ltd", "symbol": "GAIL.NS"},
          {"company": "Godrej Consumer Products Ltd", "symbol": "GODREJCP.NS"},
          {"company": "Grasim Industries Ltd", "symbol": "GRASIM.NS"},
          {"company": "Hindustan Aeronautics Ltd", "symbol": "HAL.NS"},
          {"company": "Havells India Ltd", "symbol": "HAVELLS.NS"},
          {"company": "HCL Technologies Ltd", "symbol": "HCLTECH.NS"},
          {"company": "HDFC Bank Ltd", "symbol": "HDFCBANK.NS"},
          {"company": "HDFC Life Insurance Company Ltd", "symbol": "HDFCLIFE.NS"},
          {"company": "Hero MotoCorp Ltd", "symbol": "HEROMOTOCO.NS"},
          {"company": "Hindalco Industries Ltd", "symbol": "HINDALCO.NS"},
          {"company": "Hindustan Unilever Ltd", "symbol": "HINDUNILVR.NS"},
          {"company": "ICICI Bank Ltd", "symbol": "ICICIBANK.NS"},
          {"company": "ICICI Lombard General Insurance Company Ltd", "symbol": "ICICIGI.NS"},
          {"company": "ICICI Prudential Life Insurance Company Ltd", "symbol": "ICICIPRULI.NS"},
          {"company": "Interglobe Aviation Ltd", "symbol": "INDIGO.NS"},
          {"company": "Indusind Bank Ltd", "symbol": "INDUSINDBK.NS"},
          {"company": "Infosys Ltd", "symbol": "INFY.NS"},
          {"company": "Indian Oil Corporation Ltd", "symbol": "IOC.NS"},
          {"company": "Indian Railway Catering and Tourism Corporation Ltd", "symbol": "IRCTC.NS"},
          {"company": "ITC Ltd", "symbol": "ITC.NS"},
          {"company": "Jindal Steel And Power Ltd", "symbol": "JINDALSTEL.NS"},
          {"company": "JSW Energy Ltd", "symbol": "JSWENERGY.NS"},
          {"company": "JSW Steel Ltd", "symbol": "JSWSTEEL.NS"},
          {"company": "Kotak Mahindra Bank Ltd", "symbol": "KOTAKBANK.NS"},
          {"company": "Larsen and Toubro Ltd", "symbol": "LT.NS"},
          {"company": "LTIMindtree Ltd", "symbol": "LTIM.NS"},
          {"company": "Mahindra and Mahindra Ltd", "symbol": "M&M.NS"},
          {"company": "Maruti Suzuki India Ltd", "symbol": "MARUTI.NS"},
          {"company": "United Spirits Ltd", "symbol": "UNITDSPR.NS"},
          {"company": "Samvardhana Motherson International Ltd", "symbol": "MOTHERSON.NS"},
          {"company": "Info Edge (India) Ltd", "symbol": "NAUKRI.NS"},
          {"company": "Nestle India Ltd", "symbol": "NESTLEIND.NS"},
          {"company": "NHPC Ltd", "symbol": "NHPC.NS"},
          {"company": "NTPC Ltd", "symbol": "NTPC.NS"},
          {"company": "Oil and Natural Gas Corporation Ltd", "symbol": "ONGC.NS"},
          {"company": "Power Finance Corporation Ltd", "symbol": "PFC.NS"},
          {"company": "Pidilite Industries Ltd", "symbol": "PIDILITIND.NS"},
          {"company": "Punjab National Bank", "symbol": "PNB.NS"},
          {"company": "Power Grid Corporation of India Ltd", "symbol": "POWERGRID.NS"},
          {"company": "REC Limited", "symbol": "RECLTD.NS"},
          {"company": "Reliance Industries Ltd", "symbol": "RELIANCE.NS"},
          {"company": "SBI Life Insurance Company Ltd", "symbol": "SBILIFE.NS"},
          {"company": "State Bank of India", "symbol": "SBIN.NS"},
          {"company": "Shree Cement Ltd", "symbol": "SHREECEM.NS"},
          {"company": "Siemens Ltd", "symbol": "SIEMENS.NS"},
          {"company": "Shriram Finance Ltd", "symbol": "SHRIRAMFIN.NS"},
          {"company": "Sun Pharmaceutical Industries Ltd", "symbol": "SUNPHARMA.NS"},
          {"company": "Tata Consumer Products Ltd", "symbol": "TATACONSUM.NS"},
          {"company": "Tata Motors Ltd", "symbol": "TATAMOTORS.NS"},
          {"company": "Tata Power Company Ltd", "symbol": "TATAPOWER.NS"},
          {"company": "Tata Steel Ltd", "symbol": "TATASTEEL.NS"},
          {"company": "Tata Consultancy Services Ltd", "symbol": "TCS.NS"},
          {"company": "Tech Mahindra Ltd", "symbol": "TECHM.NS"},
          {"company": "Titan Company Ltd", "symbol": "TITAN.NS"},
          {"company": "Torrent Pharmaceuticals Ltd", "symbol": "TORNTPHARM.NS"},
          {"company": "Trent Ltd", "symbol": "TRENT.NS"},
          {"company": "TVS Motor Company Ltd", "symbol": "TVSMOTOR.NS"},
          {"company": "UltraTech Cement Ltd", "symbol": "ULTRACEMCO.NS"},
          {"company": "Union Bank of India Ltd", "symbol": "UNIONBANK.NS"},
          {"company": "Varun Beverages Ltd", "symbol": "VBL.NS"},
          {"company": "Vedanta Ltd", "symbol": "VEDL.NS"},
          {"company": "Wipro Ltd", "symbol": "WIPRO.NS"},
          {"company": "Indian Railway Finance Corp Ltd", "symbol": "IRFC.NS"},
          {"company": "Macrotech Developers Ltd", "symbol": "LODHA.NS"},
          {"company": "Zomato Ltd", "symbol": "ZOMATO.NS"},
          {"company": "Life Insurance Corporation Of India", "symbol": "LICI.NS"},
          {"company": "Jio Financial Services Ltd", "symbol": "JIOFIN.NS"}
        ]


    return nifty100_list

def get_nifty150():
    nifty150_list = [
    {"company": "3M India Ltd", "symbol": "3MINDIA.NS"},
    {"company": "Abbott India Ltd", "symbol": "ABBOTINDIA.NS"},
    {"company": "Aditya Birla Capital Ltd", "symbol": "ABCAPITAL.NS"},
    {"company": "Aditya Birla Fashion and Retail Ltd", "symbol": "ABFRL.NS"},
    {"company": "ACC Ltd", "symbol": "ACC.NS"},
    {"company": "AIA Engineering Ltd", "symbol": "AIAENG.NS"},
    {"company": "Ajanta Pharma Ltd", "symbol": "AJANTPHARM.NS"},
    {"company": "Alkem Laboratories Ltd", "symbol": "ALKEM.NS"},
    {"company": "APL Apollo Tubes Ltd", "symbol": "APLAPOLLO.NS"},
    {"company": "Apollo Tyres Ltd", "symbol": "APOLLOTYRE.NS"},
    {"company": "Ashok Leyland Ltd", "symbol": "ASHOKLEY.NS"},
    {"company": "Astral Ltd", "symbol": "ASTRAL.NS"},
    {"company": "AU Small Finance Bank Ltd", "symbol": "AUBANK.NS"},
    {"company": "Aurobindo Pharma Ltd", "symbol": "AUROPHARMA.NS"},
    {"company": "Balkrishna Industries Ltd", "symbol": "BALKRISIND.NS"},
    {"company": "Bandhan Bank Ltd", "symbol": "BANDHANBNK.NS"},
    {"company": "Bank of India Ltd", "symbol": "BANKINDIA.NS"},
    {"company": "Bayer Cropscience Ltd", "symbol": "BAYERCROP.NS"},
    {"company": "Bharat Dynamics Ltd", "symbol": "BDL.NS"},
    {"company": "Berger Paints India Ltd", "symbol": "BERGEPAINT.NS"},
    {"company": "Bharti Hexacom Ltd", "symbol": "BHARTIHEXA.NS"},
    {"company": "Biocon Ltd", "symbol": "BIOCON.NS"},
    {"company": "BSE Ltd", "symbol": "BSE.NS"},
    {"company": "Carborundum Universal Ltd", "symbol": "CARBORUNIV.NS"},
    {"company": "CG Power and Industrial Solutions Ltd", "symbol": "CGPOWER.NS"},
    {"company": "Cochin Shipyard Ltd", "symbol": "COCHINSHIP.NS"},
    {"company": "Coforge Ltd", "symbol": "COFORGE.NS"},
    {"company": "Colgate-Palmolive (India) Ltd", "symbol": "COLPAL.NS"},
    {"company": "Container Corporation of India Ltd", "symbol": "CONCOR.NS"},
    {"company": "Coromandel International Ltd", "symbol": "COROMANDEL.NS"},
    {"company": "CRISIL Ltd", "symbol": "CRISIL.NS"},
    {"company": "Cummins India Ltd", "symbol": "CUMMINSIND.NS"},
    {"company": "Dalmia Bharat Ltd", "symbol": "DALBHARAT.NS"},
    {"company": "Deepak Nitrite Ltd", "symbol": "DEEPAKNTR.NS"},
    {"company": "Dixon Technologies (India) Ltd", "symbol": "DIXON.NS"},
    {"company": "Emami Ltd", "symbol": "EMAMILTD.NS"},
    {"company": "Endurance Technologies Ltd", "symbol": "ENDURANCE.NS"},
    {"company": "Escorts Kubota Ltd", "symbol": "ESCORTS.NS"},
    {"company": "Exide Industries Ltd", "symbol": "EXIDEIND.NS"},
    {"company": "Fertilisers And Chemicals Travancore Ltd", "symbol": "FACT.NS"},
    {"company": "Federal Bank Ltd", "symbol": "FEDERALBNK.NS"},
    {"company": "Gujarat Fluorochemicals Ltd", "symbol": "FLUOROCHEM.NS"},
    {"company": "Fortis Healthcare Ltd", "symbol": "FORTIS.NS"},
    {"company": "General Insurance Corporation of India", "symbol": "GICRE.NS"},
    {"company": "GlaxoSmithKline Pharmaceuticals Ltd", "symbol": "GLAXO.NS"},
    {"company": "GMR Airports Ltd", "symbol": "GMRAIRPORT.NS"},
    {"company": "Godrej Industries Ltd", "symbol": "GODREJIND.NS"},
    {"company": "Godrej Properties Ltd", "symbol": "GODREJPROP.NS"},
    {"company": "Grindwell Norton Ltd", "symbol": "GRINDWELL.NS"},
    {"company": "Gujarat Gas Ltd", "symbol": "GUJGASLTD.NS"},
    {"company": "HDFC Asset Management Company Ltd", "symbol": "HDFCAMC.NS"},
    {"company": "Hindustan Petroleum Corp Ltd", "symbol": "HINDPETRO.NS"},
    {"company": "Hindustan Zinc Ltd", "symbol": "HINDZINC.NS"},
    {"company": "Honeywell Automation India Ltd", "symbol": "HONAUT.NS"},
    {"company": "Housing and Urban Development Corporation Ltd", "symbol": "HUDCO.NS"},
    {"company": "IDBI Bank Ltd", "symbol": "IDBI.NS"},
    {"company": "Vodafone Idea Ltd", "symbol": "IDEA.NS"},
    {"company": "IDFC First Bank Ltd", "symbol": "IDFCFIRSTB.NS"},
    {"company": "Indraprastha Gas Ltd", "symbol": "IGL.NS"},
    {"company": "Indian Hotels Company Ltd", "symbol": "INDHOTEL.NS"},
    {"company": "Indian Bank", "symbol": "INDIANB.NS"},
    {"company": "Indus Towers Ltd", "symbol": "INDUSTOWER.NS"},
    {"company": "Indian Overseas Bank", "symbol": "IOB.NS"},
    {"company": "IPCA Laboratories Ltd", "symbol": "IPCALAB.NS"},
    {"company": "IRB Infrastructure Developers Ltd", "symbol": "IRB.NS"},
    {"company": "J K Cement Ltd", "symbol": "JKCEMENT.NS"},
    {"company": "Jindal Stainless Ltd", "symbol": "JSL.NS"},
    {"company": "Jubilant Foodworks Ltd", "symbol": "JUBLFOOD.NS"},
    {"company": "KEI Industries Ltd", "symbol": "KEI.NS"},
    {"company": "KPIT Technologies Ltd", "symbol": "KPITTECH.NS"},
    {"company": "KPR Mill Ltd", "symbol": "KPRMILL.NS"},
    {"company": "L&T Finance Ltd", "symbol": "LTF.NS"},
    {"company": "LIC Housing Finance Ltd", "symbol": "LICHSGFIN.NS"},
    {"company": "Linde India Ltd", "symbol": "LINDEINDIA.NS"},
    {"company": "L&T Technology Services Ltd", "symbol": "LTTS.NS"},
    {"company": "Lupin Ltd", "symbol": "LUPIN.NS"},
    {"company": "Mahindra and Mahindra Financial Services Ltd", "symbol": "M&MFIN.NS"},
    {"company": "Poonawalla Fincorp Ltd", "symbol": "POONAWALLA.NS"},
    {"company": "Bank of Maharashtra Ltd", "symbol": "MAHABANK.NS"},
    {"company": "Marico Ltd", "symbol": "MARICO.NS"},
    {"company": "Max Healthcare Institute Ltd", "symbol": "MAXHEALTH.NS"},
    {"company": "Max Financial Services Ltd", "symbol": "MFSL.NS"},
    {"company": "UNO Minda Ltd", "symbol": "UNOMINDA.NS"},
    {"company": "Mphasis Ltd", "symbol": "MPHASIS.NS"},
    {"company": "MRF Ltd", "symbol": "MRF.NS"},
    {"company": "Mangalore Refinery and Petrochemicals Ltd", "symbol": "MRPL.NS"},
    {"company": "Muthoot Finance Ltd", "symbol": "MUTHOOTFIN.NS"},
    {"company": "Nippon Life India Asset Management Ltd", "symbol": "NAM-INDIA.NS"},
    {"company": "New India Assurance Company Ltd", "symbol": "NIACL.NS"},
    {"company": "NLC India Ltd", "symbol": "NLCINDIA.NS"},
    {"company": "NMDC Ltd", "symbol": "NMDC.NS"},
    {"company": "Oberoi Realty Ltd", "symbol": "OBEROIRLTY.NS"},
    {"company": "Oracle Financial Services Software Ltd", "symbol": "OFSS.NS"},
    {"company": "Oil India Ltd", "symbol": "OIL.NS"},
    {"company": "Page Industries Ltd", "symbol": "PAGEIND.NS"},
    {"company": "Persistent Systems Ltd", "symbol": "PERSISTENT.NS"},
    {"company": "Petronet LNG Ltd", "symbol": "PETRONET.NS"},
    {"company": "Procter & Gamble Hygiene and Health Care Ltd", "symbol": "PGHH.NS"},
          {"company": "Phoenix Mills Ltd", "symbol": "PHOENIXLTD.NS"},
          {"company": "PI Industries Ltd", "symbol": "PIIND.NS"},
          {"company": "Polycab India Ltd", "symbol": "POLYCAB.NS"},
          {"company": "Hitachi Energy India Ltd", "symbol": "POWERINDIA.NS"},
          {"company": "Prestige Estates Projects Ltd", "symbol": "PRESTIGE.NS"},
          {"company": "Patanjali Foods Ltd", "symbol": "PATANJALI.NS"},
          {"company": "Rail Vikas Nigam Ltd", "symbol": "RVNL.NS"},
          {"company": "Steel Authority of India Ltd", "symbol": "SAIL.NS"},
          {"company": "SBI Cards and Payment Services Ltd", "symbol": "SBICARD.NS"},
          {"company": "Schaeffler India Ltd", "symbol": "SCHAEFFLER.NS"},
          {"company": "SJVN Ltd", "symbol": "SJVN.NS"},
          {"company": "SKF India Ltd", "symbol": "SKFINDIA.NS"},
          {"company": "Solar Industries India Ltd", "symbol": "SOLARINDS.NS"},
          {"company": "SRF Ltd", "symbol": "SRF.NS"},
          {"company": "Sundaram Finance Ltd", "symbol": "SUNDARMFIN.NS"},
          {"company": "Sundram Fasteners Ltd", "symbol": "SUNDRMFAST.NS"},
          {"company": "Sun Tv Network Ltd", "symbol": "SUNTV.NS"},
          {"company": "Supreme Industries Ltd", "symbol": "SUPREMEIND.NS"},
          {"company": "Suzlon Energy Ltd", "symbol": "SUZLON.NS"},
          {"company": "Syngene International Ltd", "symbol": "SYNGENE.NS"},
          {"company": "Tata Chemicals Ltd", "symbol": "TATACHEM.NS"},
          {"company": "Tata Communications Ltd", "symbol": "TATACOMM.NS"},
          {"company": "Tata Elxsi Ltd", "symbol": "TATAELXSI.NS"},
          {"company": "Tata Investment Corporation Ltd", "symbol": "TATAINVEST.NS"},
          {"company": "Thermax Limited", "symbol": "THERMAX.NS"},
          {"company": "Tube Investments of India Ltd", "symbol": "TIINDIA.NS"},
          {"company": "Timken India Ltd", "symbol": "TIMKEN.NS"},
          {"company": "Torrent Power Ltd", "symbol": "TORNTPOWER.NS"},
          {"company": "United Breweries Ltd", "symbol": "UBL.NS"},
          {"company": "UPL Ltd", "symbol": "UPL.NS"},
          {"company": "Voltas Ltd", "symbol": "VOLTAS.NS"},
          {"company": "ZF Commercial Vehicle Control Systems India Ltd", "symbol": "ZFCVINDIA.NS"},
          {"company": "Yes Bank Ltd", "symbol": "YESBANK.NS"},
          {"company": "Lloyds Metals And Energy Ltd", "symbol": "LLOYDSME.NS"},
          {"company": "Mazagon Dock Shipbuilders Ltd", "symbol": "MAZDOCK.NS"},
          {"company": "Gland Pharma Ltd", "symbol": "GLAND.NS"},
          {"company": "Kalyan Jewellers India Ltd", "symbol": "KALYANKJIL.NS"},
          {"company": "Sona BLW Precision Forgings Ltd", "symbol": "SONACOMS.NS"},
          {"company": "Fsn E-Commerce Ventures Ltd", "symbol": "NYKAAV"},
          {"company": "PB Fintech Ltd", "symbol": "POLICYBZR.NS"},
          {"company": "One 97 Communications Ltd", "symbol": "PAYTM.NS"},
          {"company": "Star Health and Allied Insurance Company Ltd", "symbol": "STARHEALTH.NS"},
          {"company": "Metro Brands Ltd", "symbol": "METROBRAND.NS"},
          {"company": "Adani Wilmar Ltd", "symbol": "AWL.NS"},
          {"company": "Motherson Sumi Wiring India Ltd", "symbol": "MSUMI.NS"},
          {"company": "Delhivery Ltd", "symbol": "DELHIVERY.NS"},
          {"company": "Global Health Ltd", "symbol": "MEDANTA.NS"},
          {"company": "Mankind Pharma Ltd", "symbol": "MANKIND.NS"},
          {"company": "JSW Infrastructure Ltd", "symbol": "JSWINFRA.NS"},
          {"company": "Indian Renewable Energy Development Agency Ltd", "symbol": "IREDA.NS"},
          {"company": "Tata Technologies Ltd", "symbol": "TATATECH.NS"},
          {"company": "Bharti Hexacom Ltd", "symbol": "BHARTIHEXA.NS"}
        ]
    return nifty150_list


# Function to fetch stock index data
def get_stock_index(url, table_index, symbol_col=0, company_col=1, suffix=False):
    try:
        tables = pd.read_html(url)
        stock_df = tables[table_index]
        
        # Extract symbol and company name columns
        stock_df = stock_df.iloc[:, [symbol_col, company_col]]
        stock_df.columns = ["symbol", "company"]
        
        # Add '.NS' suffix to NIFTY symbols
        if suffix:
            stock_df["symbol"] = stock_df["symbol"].apply(lambda x: f"{x}.NS")
        
        return stock_df.to_dict(orient="records")
    except IndexError:
        return {"error": f"Could not find table at index {table_index} in {url}."}
    except Exception as e:
        return {"error": str(e)}

@app.route('/getcompanies', methods=['GET'])
def get_companies():
    # Fetch stock indices and apply '.NS' suffix only for NIFTY 50 and NIFTY 500
    indexes = {
        "S&P 100": get_stock_index("https://en.wikipedia.org/wiki/S%26P_100", table_index=2, symbol_col=0, company_col=1),
        "S&P 500": get_stock_index("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", table_index=0, symbol_col=0, company_col=1),
        "S&P 400": get_stock_index("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", table_index=0, symbol_col=0, company_col=1),
        "S&P 600": get_stock_index("https://en.wikipedia.org/wiki/List_of_S%26P_600_companies", table_index=0, symbol_col=0, company_col=1),
        "Nasdaq-100": get_stock_index("https://en.wikipedia.org/wiki/NASDAQ-100", table_index=4, symbol_col=1, company_col=0),
        "Dow Jones IA": get_stock_index("https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average", table_index=2, symbol_col=2, company_col=0),
        "Dow Jones TA": get_stock_index("https://en.wikipedia.org/wiki/Dow_Jones_Transportation_Average", table_index=0, symbol_col=1, company_col=0),
        "Dow Jones UA": get_stock_index("https://en.wikipedia.org/wiki/Dow_Jones_Utility_Average", table_index=1, symbol_col=1, company_col=0),
        "Russell 1000": get_stock_index("https://en.wikipedia.org/wiki/Russell_1000_Index", table_index=3, symbol_col=1, company_col=0),
        "BSE 30": get_stock_index("https://en.wikipedia.org/wiki/BSE_SENSEX", table_index=2, symbol_col=1, company_col=0),
        
        # NIFTY 50 and NIFTY 500 with '.NS' suffix
        "NIFTY 50": get_stock_index("https://en.wikipedia.org/wiki/NIFTY_50", table_index=1, symbol_col=1, company_col=0, suffix=True),
        "NIFTY 500": get_stock_index("https://en.wikipedia.org/wiki/NIFTY_500", table_index=2, symbol_col=3, company_col=1, suffix=True),
        "NIFTY 100": get_nifty100(),
        "NIFTY 150": get_nifty150()

    }

    return jsonify(indexes)

@app.route('/tools', methods=['GET'])
def tools():
    try:
        # Logic to fetch tools data
        tools_data = {"tools": ["Tool 1", "Tool 2", "Tool 3"]}
        return jsonify(tools_data)
    except Exception as e:
        logger.error(f"Error in tools endpoint: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)