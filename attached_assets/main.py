import os
import logging
from .data.stock_data import StockData
from .data.indices_manager import IndicesManager
from .analysis.technical_analysis import TechnicalAnalysis
from .analysis.correlation import CorrelationAnalysis
from .visualization.charts import ChartGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PyTradeAnalytics:
    def __init__(self, data_path=None):
        # Use default path if none provided
        if data_path is None:
            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        self.data_path = data_path
        self.stock_data = StockData(data_path)
        self.indices_manager = IndicesManager(data_path)
        self.technical_analysis = TechnicalAnalysis(self.stock_data)
        self.correlation = CorrelationAnalysis(self.stock_data, self.indices_manager)
        self.charts = ChartGenerator(self.stock_data)
        
        logger.info("PyTradeAnalytics initialized successfully")
    
    def get_available_indices(self):
        """Return a list of available indices"""
        return self.indices_manager.list_available_indices()
        
    def analyze_stock_with_index(self, ticker, index_name, period='1y'):
        """Analyze a stock's correlation with a specific index"""
        correlation = self.correlation.calculate_correlation_with_index(ticker, index_name, period)
        return {
            'ticker': ticker,
            'index': index_name,
            'period': period,
            'correlation': correlation
        }
    
    def compare_stocks_with_indices(self, tickers, index_names):
        """Compare multiple stocks against multiple indices"""
        return self.correlation.plot_correlation_heatmap(tickers, index_names)
        
    # ... existing code ...
