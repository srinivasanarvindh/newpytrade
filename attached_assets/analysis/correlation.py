import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ..data.indices_manager import IndicesManager

class CorrelationAnalysis:
    def __init__(self, stock_data, indices_manager):
        self.stock_data = stock_data
        self.indices_manager = indices_manager
        
    def calculate_correlation_with_index(self, ticker, index_name, period='1y'):
        """Calculate correlation between a stock and an index for a specified period"""
        stock_df = self.stock_data.get_stock_data(ticker)
        if stock_df is None:
            return None
            
        # Get the index data and align it with stock data
        aligned_df = self.indices_manager.align_index_with_data(stock_df, index_name)
        
        # Calculate returns for both stock and index
        aligned_df['stock_returns'] = aligned_df['Close'].pct_change()
        aligned_df[f'{index_name}_returns'] = aligned_df[f'{index_name}_Close'].pct_change()
        
        # Filter based on the period
        if period == '1y':
            lookback_date = aligned_df.index[-1] - pd.DateOffset(years=1)
        elif period == '6m':
            lookback_date = aligned_df.index[-1] - pd.DateOffset(months=6)
        elif period == '3m':
            lookback_date = aligned_df.index[-1] - pd.DateOffset(months=3)
        else:
            lookback_date = aligned_df.index[0]
        
        period_df = aligned_df[aligned_df.index >= lookback_date]
        
        # Calculate correlation
        correlation = period_df['stock_returns'].corr(period_df[f'{index_name}_returns'])
        return correlation
        
    def plot_correlation_heatmap(self, tickers, index_names):
        """Create a heatmap of correlations between stocks and indices"""
        corr_matrix = pd.DataFrame(index=tickers, columns=index_names)
        
        for ticker in tickers:
            for index_name in index_names:
                corr = self.calculate_correlation_with_index(ticker, index_name)
                corr_matrix.loc[ticker, index_name] = corr
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('Stock-Index Correlation Matrix')
        plt.tight_layout()
        return plt.gcf()
