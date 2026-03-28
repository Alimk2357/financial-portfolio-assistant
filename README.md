# Financial Portfolio Assistant (CLI) 📈

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## 🚀 Overview

**Financial Portfolio Assistant** is a comprehensive Command Line Interface (CLI) tool designed for traders, data engineers, and quantitative analysts. It bridges the gap between real-time market tracking, automated technical analysis, and highly concurrent alerting mechanisms.

Unlike simple API wrappers, this system leverages **Machine Learning** for trend forecasting and generates professional-grade **automatic Excel reports** for offline analysis. Built with advanced software engineering principles, it runs efficiently in the background using multi-layered concurrency (Threading & Multiprocessing). It monitors assets 24/7 without blocking the main user interface, utilizing delta-update caching to bypass API rate limits, and notifies the user via desktop alerts when precise market conditions are met.

## ✨ Key Features

### 1. 🔔 Intelligent Alarm System (3-Layer Logic)
The system moves beyond simple price targets by offering three distinct monitoring algorithms:
* **Fixed Price Alarm:** Triggers when an asset crosses a specific price threshold (e.g., *Bitcoin > $100,000*). Overcomes floating-point precision errors for exact matching.
* **Percentage Change Alarm:** Detects sudden volatility by monitoring percentage moves within a specific timeframe.
* **Period Extremum Alarm:** Monitors for breakout signals by triggering when the price exceeds the highest or lowest value of a user-defined historical period.
* **Asynchronous Tracking:** Alarm strategies are tracked in the background using optimized `threading`. Lock contention is strictly managed via "Copy & Release" mechanics, ensuring the main CLI thread remains lightning-fast.

### 2. 📑 Automated Financial Reporting
Generates automatic, detailed `.xlsx` files using `xlsxwriter` for in-depth post-market analysis.
* **Summary Sheet:** Provides a snapshot of performance including Start/End Prices, Total Return, Volatility, and Min/Max values over the selected period.
* **Raw Data & Charts:** Archives historical OHLCV data alongside calculated technical indicators. Incorporates headless `Agg` backend rendering to generate multi-pane `mplfinance` charts in the background without triggering OS window GUI interruptions.

### 3. 🤖 ML-Powered Price Prediction
* **Isolated Model Training:** Utilizes `ProcessPoolExecutor` (Multiprocessing) to train models on isolated CPU cores, bypassing Python's GIL. This ensures the CLI never freezes during heavy mathematical computations.
* **Advanced Modeling:** Incorporates `LightGBM` classifiers and `scikit-learn` pipelines. Uses `TimeSeriesSplit` for time-aware cross-validation and `RandomizedSearchCV` for hyperparameter tuning to prevent data leakage.
* **Smart Caching:** Models are serialized via `joblib`. The system uses file modified time (`mtime`) checks for Delta-Update caching, only retraining models when they become naturally outdated (e.g., > 7 days), saving massive Disk I/O.

### 4. 📊 Advanced Technical Analysis
* **Comprehensive Indicator Engine:** Powered by `pandas-ta`, the system automatically calculates and utilizes a wide array of metrics for both reporting and ML feature extraction:
  * **RSI (Relative Strength Index):** Evaluates overbought or oversold conditions.
  * **SMA (Simple Moving Averages):** Uses 50-period and 200-period SMAs to identify short and long-term trend directions.
  * **Historical Volatility (HV):** Calculated across 21, 63, and 252 periods to assess risk and price fluctuations over monthly, quarterly, and yearly bases.
  * **MACD (Moving Average Convergence Divergence):** Standard 12, 26, 9 settings (MACD line, signal line, and histogram) to spot momentum shifts.
  * **ATR (Average True Range):** A 14-period metric measuring market volatility by decomposing the entire range of an asset price.
  * **Bollinger Bands (20, 2.0):** Extracts Lower, Upper, Bandwidth, Percent, and Middle bands to identify dynamic support/resistance levels and volatility squeezes.
  * **OBV (On-Balance Volume):** Uses volume flow to predict changes in stock price.
* **Feature Alignment:** Handles real-time feature alignment and scaling to ensure continuous, error-free ML inference on live market data.

### 5. 🔒 Security & Data Integrity
* **Secure Authentication:** User credentials and sensitive configurations are hashed and secured using `bcrypt`.
* **Data Handling:** Robust data manipulation using `pandas` and `numpy` ensures mathematical accuracy. Missing API data is gracefully handled via localized forward-filling and exception shielding.

## 🛠️ Tech Stack

This project is built using a modern Python ecosystem tailored for Data Science, Concurrency, and Finance.

| Category | Libraries |
|----------|-----------|
| **Core & Data Processing** | `pandas`, `numpy` |
| **Financial Data** | `yfinance` |
| **Technical Analysis** | `pandas-ta` |
| **Machine Learning** | `scikit-learn`, `lightgbm`, `joblib` |
| **Visualization** | `matplotlib`, `mplfinance` |
| **Reporting** | `xlsxwriter` |
| **System & Security** | `notify-py`, `bcrypt` |

## 💻 Installation & Usage

Follow these steps to run the project locally on your machine.

### 1. Clone the Repository
```bash
git clone https://github.com/Alimk2357/financial-portfolio-assistant.git
cd financial-portfolio-assistant
```
### 2. Create a Virtual Environment
It is recommended to use a virtual environ.ment to avoid conflicts.

**For macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```
**For Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages listed in `requirements.txt`

```bash
pip install -r requirements.txt
```

**Important Note for macOS Users:**
The ML model (LightGBM) requires the `libomp` library to run. If it is not installed, install it via the terminal

```bash
`brew install libomp`
```

### 4. Run the Application

Start the app

```bash
python main.py
```

## 📂 Project Structure

```bash
financial-portfolio-assistant/
├── src/
│   ├── __init__.py        # Exists to define src as a Python package
│   ├── analysis.py        # Technical Analysis (pandas-ta) and Excel report
│   ├── portfolio.py       # Portfolio operations (adding and deleting financial assets) 
│   ├── alarms.py          # Implementation of Fixed, Percentage, and Extremum alarms
│   ├── utils.py           # Helper functions
│   ├── tracking.py        # Alarm tracking system and notifications
│   ├── storage.py         # Loading and saving operations to the data.json
│   ├── auth.py            # User account operations and encryption (bcrypt)
│   ├── shared.py          # Stores global variables, exists to prevent circular import
│   ├── model.py           # ML model and fetch-train-add pipeline
│   └── ui.py              # Terminal-based UI functions
├── main.py                # Menu operations
├── requirements.txt       # Dependencies
└── README.md              # Documentation
