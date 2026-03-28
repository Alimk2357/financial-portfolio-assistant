# Financial Portfolio Assistant (CLI) 📈

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## 🚀 Overview

**Financial Portfolio Assistant** is a comprehensive Command Line Interface (CLI) tool designed for traders and data enthusiasts. It bridges the gap between real-time market tracking, automated technical analysis, and intelligent alerting mechanisms.

Unlike simple trackers, this system leverages **Machine Learning** for trend forecasting and generates professional-grade **Excel reports** for offline analysis. It is built to run efficiently in the background, monitoring assets 24/7 and notifying the user via desktop alerts when specific market conditions are met.

## ✨ Key Features

### 1. 🔔 Intelligent Alarm System (3-Layer Logic)
The system moves beyond simple price targets by offering three distinct monitoring algorithms:
* **Fixed Price Alarm:** Triggers when an asset crosses a specific price threshold (e.g., *Bitcoin > $100,000*).
* **Percentage Change Alarm:** Detects sudden volatility by monitoring percentage moves within a specific timeframe (e.g., *Price drops 5% in 1 hour*).
* **Period Extremum Alarm:** Monitors for breakout signals by triggering when the price exceeds the highest or lowest value of a user-defined period (e.g., *New 30-day High*).
* **Desktop Notifications:** Powered by `notify-py`, alerts are delivered directly to the user's desktop environment.
Alarm strategies are tracked at the background using `threading`, while user is continuing his/her operations.

### 2. 📑 Automated Financial Reporting
Generates detailed `.xlsx` reports using `xlsxwriter` for in-depth post-market analysis.
* **Summary Sheet:** Provides a snapshot of performance including Start/End Prices, Total Return, Volatility, and Min/Max values over the selected period.
* **Raw Data Sheet:** Archives historical OHLCV data alongside calculated technical indicators, formatted for easy integration with other analytical tools.

### 3. 🤖 ML-Powered Price Prediction
* **Trend Forecasting:** Utilizes `scikit-learn` and `multiprocessing` to train gradient boosting-based model on historical data.
* **Advanced Modeling:** Incorporates `LightGBM`, a gradient boosting framework, to enhance prediction accuracy and handle complex financial patterns.
* **Predictive Analysis:** Forecases short-term price movements to support "Buy/Hold/Sell" decision-making processes.

### 4. 📊 Advanced Technical Analysis
* **Indicator Engine:** Powered by `pandas-ta`, the system calculates key metrics (RSI, SMA50 and SMA200; HV-21, HV-63 and HV-252) automatically.
* **Visualization:** Integrated `matplotlib` and `mplfinance` libraries allow for the generation of static charts and trend visualizations directly from the CLI.

### 5. 🔒 Security & Data Integrity
* **Secure Authentication:** User credentials and sensitive configurations are hashed and secured using `bcrypt`.
* **Data Handling:** Robust data manipulation using `pandas` and `numpy` ensures accuracy in financial calculations.

## 🛠️ Tech Stack

This project is built using a modern Python ecosystem tailored for Data Science and Finance:

| Category | Libraries                                        |
|----------|--------------------------------------------------|
| **Core & Data** | `Python 3.x`, `pandas`, `numpy`                  |
| **Financial Data** | `yfinance` (Yahoo Finance API)                   |
| **Technical Analysis** | `pandas-ta`                                      |
| **Machine Learning** | `scikit-learn`, `lightgbm`                       |
| **Visualization** | `matplotlib`, `mplfinance`                       |
| **Reporting** | `xlsxwriter`                                     |
| **System & Alerts** | `notify-py` (Notifications), `bcrypt` (Security) |

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
The ML model (LightGBM) requires the `libomp` library to run. If it is not installed, install it via the terminal:
`brew install libomp`

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
