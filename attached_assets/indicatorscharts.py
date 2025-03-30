from flask import Flask, jsonify
import pandas as pd
import talib
import numpy as np

def compute_rsi(df, period=14):
    close_prices = df['Close'].to_numpy().flatten()
    rsi = talib.RSI(close_prices, timeperiod=period)
    
    return rsi


    # Compute MACD and Signal Line
def compute_macd(df):
    close_prices = df['Close'].to_numpy().flatten()
    macd, macd_signal, macd_hist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
    
    return macd, macd_signal

def compute_ema(df):
    close_prices = df['Close'].to_numpy().flatten()
    ema_9 = talib.EMA(close_prices, timeperiod=9)
    ema_20 = talib.EMA(close_prices, timeperiod=20)
    ema_50 = talib.EMA(close_prices, timeperiod=50)
    
    return ema_9, ema_20,ema_50

def compute_atr(df,atr_period=14, atr_multiplier=2):
    close_prices = df['Close'].to_numpy().flatten()
    high_prices = df['High'].to_numpy().flatten()
    low_prices = df['Low'].to_numpy().flatten()

    atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=atr_period)
    upperATRBand = close_prices + (atr * atr_multiplier)
    lowerATRBand = close_prices - (atr * atr_multiplier)
    
    
    return atr, upperATRBand,lowerATRBand

def compute_fibo(df):      

    df['Swing_High'] = df['High'].rolling(window=20).max()
    df['Swing_Low'] = df['Low'].rolling(window=20).min()
    fib_38_2 = df['Swing_Low'] + (df['Swing_High'] - df['Swing_Low']) * 0.382
    fib_50 = df['Swing_Low'] + (df['Swing_High'] - df['Swing_Low']) * 0.50
    fib_61_8 = df['Swing_Low'] + (df['Swing_High'] - df['Swing_Low']) * 0.618
    
    return fib_38_2, fib_50, fib_61_8
    

