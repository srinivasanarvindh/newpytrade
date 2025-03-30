# app.py
from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense,Dropout
from keras.optimizers import Adam
import talib
from sklearn.metrics import mean_absolute_error


def create_dataset(data, look_back=60, pred_steps=15):
    X, y = [], []
    for i in range(len(data) - look_back - pred_steps):
        X.append(data[i:(i + look_back), :])
        y.append(data[(i + look_back):(i + look_back + pred_steps), 0])
    return np.array(X), np.array(y)

def train_lstm(X, y):
    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dropout(0.2))
    model.add(LSTM(64, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(32, return_sequences=True))  # Added another LSTM layer
    model.add(Dropout(0.2))
    model.add(LSTM(16))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(y.shape[1]))
    optimizer = Adam(learning_rate=0.0005)  # Corrected learning rate placement
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    model.fit(X, y, epochs=2, batch_size=64, validation_split=0.2, verbose=1)  # Increased epochs to 150
    return model



def predict(df_processed, last_date, pred_steps=15):
    

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df_processed)

    X, y = create_dataset(scaled_data)

    model = train_lstm(X, y)

    # Predict on test sample (last sample in dataset)
    last_data = scaled_data[-60:]
    pred_input = np.expand_dims(last_data, axis=0)
    predictions = model.predict(pred_input)[0]

    # For comparison, get the actual values (last 'y' in the dataset)
    actual_scaled = y[-1]
    
    # Inverse transform both actual and predicted Close prices
    predictions = predictions.reshape(-1, 1)
    actual_scaled = actual_scaled.reshape(-1, 1)

    close_scaler = MinMaxScaler()
    close_scaler.min_, close_scaler.scale_ = scaler.min_[0], scaler.scale_[0]

    predictions_inv = close_scaler.inverse_transform(predictions).flatten()
    actual_inv = close_scaler.inverse_transform(actual_scaled).flatten()

    # Compute MAE
    mae = mean_absolute_error(actual_inv, predictions_inv)
    print(f"Mean Absolute Error (MAE): {mae:.2f}")

    predicted_dates = pd.date_range(last_date, periods=pred_steps + 1, freq='B')[1:]

    prediction_results = pd.DataFrame({
        'Date': predicted_dates,
        'Predicted Close': predictions_inv
    })

    return prediction_results

