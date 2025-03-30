"""
This patch fixes the numpy.NaN import error in pandas_ta
"""
import numpy as np
import sys

# Add NaN to numpy if it doesn't exist
if not hasattr(np, 'NaN'):
    np.NaN = np.nan

# Now import pandas_ta
import pandas_ta
