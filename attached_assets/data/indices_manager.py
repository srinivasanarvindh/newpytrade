import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class IndicesManager:
    def __init__(self, data_path):
        self.data_path = data_path
        self.indices_data = {}
        self.load_indices()
        
    def load_indices(self):
        """Load all available indices from the data directory"""
        indices_dir = os.path.join(self.data_path, 'indices')
        if not os.path.exists(indices_dir):
            logger.warning(f"Indices directory not found at {indices_dir}")
            return
            
        for filename in os.listdir(indices_dir):
            if filename.endswith('.csv'):
                index_name = filename.split('.')[0]
                file_path = os.path.join(indices_dir, filename)
                try:
                    df = pd.read_csv(file_path)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    self.indices_data[index_name] = df
                    logger.info(f"Loaded index data for {index_name}")
                except Exception as e:
                    logger.error(f"Failed to load index {index_name}: {str(e)}")
    
    def get_index_data(self, index_name):
        """Get data for a specific index"""
        if index_name in self.indices_data:
            return self.indices_data[index_name]
        else:
            logger.warning(f"Index {index_name} not found")
            return None
    
    def align_index_with_data(self, data_df, index_name):
        """Align index data with the given dataframe's dates"""
        if index_name not in self.indices_data:
            logger.warning(f"Index {index_name} not found")
            return data_df
            
        index_df = self.indices_data[index_name]
        # Join the index data with the provided dataframe
        aligned_df = data_df.join(index_df[['Close']], how='left')
        aligned_df.rename(columns={'Close': f'{index_name}_Close'}, inplace=True)
        
        # Forward fill any missing values
        aligned_df[f'{index_name}_Close'].fillna(method='ffill', inplace=True)
        
        return aligned_df
    
    def list_available_indices(self):
        """Return a list of all available indices"""
        return list(self.indices_data.keys())
