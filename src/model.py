import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from src.analysis import get_exchange_days
from sklearn.preprocessing import StandardScaler
import time
from sklearn.model_selection import train_test_split, TimeSeriesSplit, RandomizedSearchCV
try:
    from lightgbm import LGBMClassifier
except OSError as e:
    if sys.platform == "darwin" and 'libomp' in str(e):
        print(10 * "=" + " ERROR " + 10 * "=")
        print("LightGBM engine could not be started.")
        print("The C++ multi-threading library (libomp) is missing from your macOS system.")
        print("Run the command 'brew install libomp' on the terminal.")
        print(10 * "=" + " ERROR " + 10 * "=")
        sys.exit(1)
    else:
        raise e
import joblib

exchange_hours = {
    # 🇺🇸 US Stocks
    "NMS": 6.5,   # NASDAQ
    "NYQ": 6.5,   # NYSE
    "ASE": 6.5,   # AMEX

    # 🇹🇷 Turkey
    "IST": 6.0,   # BIST

    # 🇬🇧 UK
    "LSE": 8.5,

    # 🇩🇪 Germany
    "XETRA": 8.5,

    # 🇫🇷 France
    "EPA": 8.5,

    # 🇨🇭 Switzerland
    "SWX": 8.5,

    # 🇯🇵 Japan
    "TYO": 6.0,

    # 🇭🇰 Hong Kong
    "HKG": 6.5,

    # 🇨🇳 China
    "SHH": 4.0,
    "SHE": 4.0,

    # 🌍 Forex
    "CCY": 24.0,

    # 🪙 Crypto
    "CCC": 24.0,

    # 🟡 Commodities / Futures
    "CMX": 23.0,
    "NYM": 23.0,

    # fallback
    "UNKNOWN": 6.5
}

def get_trading_hours(exchange):
    return exchange_hours.get(exchange, exchange_hours['UNKNOWN'])

def add_indicators(df, ticker):
    exchange = ticker.fast_info['exchange']
    daily_exchange_hours = get_trading_hours(exchange)
    annual_exchange_days = get_exchange_days(exchange)

    # Adding indicators to increase prediction accuracy
    df['RSI'] = df.ta.rsi(length=14)
    df['SMA_50'] = df.ta.sma(length=50)
    df["SMA_200"] = df.ta.sma(length=200)
    df['Returns'] = df['Close'].pct_change()
    df['HV_21'] = df['Returns'].rolling(window=21).std() * ((annual_exchange_days * daily_exchange_hours) ** 0.5) * 100
    df['HV_63'] = df['Returns'].rolling(window=63).std() * ((annual_exchange_days * daily_exchange_hours) ** 0.5) * 100
    df['HV_252'] = df['Returns'].rolling(window=252).std() * ((annual_exchange_days * daily_exchange_hours) ** 0.5) * 100
    df['MACD'] = df.ta.macd()
    df['ATR'] = df.ta.atr(length=14)
    df['Bollinger'] = df.ta.bbands()
    df['OBV'] = df.ta.obv()
    return df

def delete_model(username,code):
    file_name = f"models/{username}_{code}_model.joblib"
    if os.path.exists(file_name):
        os.remove(file_name)

def save_model(username, code, best_model, scaler):
    file_name = f"models/{username}_{code}_model.joblib"
    packet = {
        "model": best_model,
        "scaler": scaler,
    }
    joblib.dump(packet, file_name)

def train_model(username,code):
    ticker = yf.Ticker(code)
    df = ticker.history(period="2y", interval="1h")
    time.sleep(0.5)

    # dropping redundant columns
    df.drop(columns=['Dividends', 'Stock Splits'], inplace=True, errors='ignore')

    # filling the missing values (due to API) with their previous rows' values
    df.ffill(inplace=True)

    # Adding indicators to increase prediction accuracy
    df = add_indicators(df, ticker)

    # Target that the model will try to predict
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    # cleaning the final data
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # X : Features , y: target
    X = df.drop(columns=['Target'])
    y = df['Target']

    # TRAIN/TEST SPLIT + SCALING
    X_train, y_train = train_test_split(X,y, test_size=0.2, shuffle=False)
    # to prevent data leakage, test data must be scaled according to
    # scaling parameters of train data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    # X_test_scaled = scaler.transform(X_test)

    # THE MODEL (LGBMClassifier)
    # to subsample parameter works, subsample_freq > 0
    # subsample = 0.8 and subsample_freq = 1 means that when a tree is created,
    # select the 80% of rows again randomly. This helps to prevent overfitting
    model = LGBMClassifier(n_jobs=-1, random_state=42, subsample_freq = 1)

    # HYPERPARAMETER TUNING
    parameters = {
        'num_leaves': [15, 31, 50],  # 31 is default. Fewer leaves prevent overfitting
        'max_depth': [3, 4, 5],

        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [100, 200, 300],

        'subsample': [0.8, 1.0],  # 80% of rows
        'colsample_bytree': [0.7, 1.0],  # 70% of columns

        'min_child_samples': [20, 50]
    }
    # TimeSeriesSplit is used because we are dealing with time-dependent data
    # therefore a method splitting the data randomly like K-Fold Cross Validation
    # cannot be used.
    tscv = TimeSeriesSplit(n_splits=5)
    random_search = RandomizedSearchCV(estimator = model, param_distributions = parameters, n_iter = 20, random_state = 42, cv = tscv, scoring = 'accuracy', n_jobs=-1)
    random_search.fit(X_train_scaled, y_train)
    best_model = random_search.best_estimator_

    # SAVING THE MODEL BY JOBLIB
    save_model(username, code, best_model, scaler)

