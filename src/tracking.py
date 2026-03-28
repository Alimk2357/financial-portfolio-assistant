import os
import yfinance as yf
from notifypy import Notify
from datetime import datetime, timedelta
import src.utils as utils
import src.storage as storage
import time
import src.model as model
import glob
import joblib
from src.shared import DATA_LOCK, STOP_EVENT
import pandas as pd

strategy_cache = {'stocks': {}, 'crypto':{},'forex':{}, 'commodities':{}}

MODELS = {}

def load_models(username):
    all_files = glob.glob(f"models/{username}_*_model.joblib")
    for file in all_files:
        file_name = os.path.basename(file)
        code = file_name.split("_")[1]
        last_modified_time = os.path.getmtime(file)
        if file in MODELS and last_modified_time == MODELS[code].get('mtime'):
            continue
        packet = joblib.load(file)
        MODELS[code] = {
            'model_data': packet,
            'mtime': last_modified_time
        }

def predict_direction(code, current_price):
    if code not in MODELS:
        return -1

    packet = MODELS[code]['model_data']
    ml_model = packet["model"]
    scaler = packet["scaler"]

    ticker = yf.Ticker(code)
    try:
        df = ticker.history(period="60d", interval="1h")
    except Exception:
        return None

    df.iloc[-1, df.columns.get_loc('Close')] = current_price

    df = df.ffill(inplace=True)

    df = model.add_indicators(df, ticker,code)

    df.drop(columns=['Low','High','Open''Dividends', 'Stock Splits'], inplace=True, errors='ignore')

    # using features list guarantees our columns that will be send to model
    # hence, the model is not affected by the API changes
    features = [
        'Close','Volume', # open, high, low is almost the same in an hour
        'RSI','SMA_50','SMA_200',
        'Returns','HV_21','HV_63','HV_252',
        'MACD_12_26_9', 'MACDs_12_26_9', 'MACDh_12_26_9',
        'ATRr_14',
        'BBL_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0', 'BBM_20_2.0',
        'OBV'
    ]
    last_row = df.iloc[[-1]][features]

    # scaler.feature_names_in reorder the features as the order the model trained
    last_row = last_row[scaler.feature_names_in_]

    last_row_scaled = scaler.transform(last_row)

    last_row_scaled_df = pd.DataFrame(last_row_scaled, columns=scaler.feature_names_in_)

    prediction = ml_model.predict(last_row_scaled_df)

    return prediction[0]

def add_to_cache(asset_type,asset, strategy, strategy_key):
    ticker = yf.Ticker(asset)
    today_date = datetime.today().date()
    yesterday_date = today_date - timedelta(days=1)
    try:
        hist_df = ticker.history(interval="1d", start=strategy["start_date"], end=yesterday_date)
    except Exception:
        return

    hist_extremum = None
    if not hist_df.empty:
        if strategy["target"] == "min":
            hist_extremum = hist_df["Low"].min()
        else:
            hist_extremum = hist_df["High"].max()
    strategy_cache[asset_type][asset][strategy_key] = {"start_date": strategy["start_date"], "hist_extremum": hist_extremum}
    time.sleep(1)

def load_cache(data,username):
    # in DATA_LOCK we must not make an API call in order not to lock the program
    # therefore, add_to_cache will be called in an extra non-DATA_LOCK loop
    items_to_cache = []
    with DATA_LOCK:
        for asset_type in data["users"][username]:
            if asset_type not in ['stocks', 'crypto','forex', 'commodities']:
                continue
            for asset in data["users"][username][asset_type]:
                if not data["users"][username][asset_type][asset]['is_active']:
                    continue
                strategy_cache[asset_type][asset] = {}
                for strategy in data["users"][username][asset_type][asset]["strategies"]:
                    shortcut = data["users"][username][asset_type][asset]["strategies"][strategy]
                    if shortcut["type"] == "period_extremum" and shortcut['status'] == 'active':
                        items_to_cache.append((asset_type, asset, shortcut, strategy))
                        # add_to_cache(asset_type,asset, shortcut, strategy)

    for item in items_to_cache:
        add_to_cache(item[0], item[1], item[2], item[3])

def check_cache(data,username):
    to_add = {'stocks': {}, 'crypto':{},'forex':{}, 'commodities':{}}
    with DATA_LOCK:
        for asset_type in data["users"][username]:
            if asset_type not in ['stocks', 'crypto','forex', 'commodities']:
                continue
            for asset in data["users"][username][asset_type]:
                if not data["users"][username][asset_type][asset]['is_active']:
                    continue
                for strategy in data["users"][username][asset_type][asset]["strategies"]:
                    shortcut = data["users"][username][asset_type][asset]["strategies"][strategy]
                    if shortcut["type"] == "period_extremum" and shortcut['status'] == 'active':
                        if not strategy_cache[asset_type].get(asset):
                            strategy_cache[asset_type][asset] = {}
                            to_add[asset_type][asset] = {strategy:{"start_date": shortcut['start_date'], "target": shortcut['target']}}
                        elif not strategy_cache[asset_type][asset].get(strategy):
                            to_add[asset_type][asset] = {strategy: {"start_date": shortcut['start_date'], "target": shortcut['target']}}
                        elif shortcut['start_date'] != strategy_cache[asset_type][asset][strategy].get('start_date'):
                            to_add[asset_type][asset] = {strategy: {"start_date": shortcut['start_date'], "target": shortcut['target']}}

    for asset_type in to_add:
        for asset in to_add[asset_type]:
            for strategy in to_add[asset_type][asset]:
                add_to_cache(asset_type,asset, to_add[asset_type][asset][strategy], strategy)

    # We get RuntimeError: dictionary changed size during iteration
    # if we try to delete an entity from the dict while iterating on it
    to_delete = {'stocks': {}, 'crypto': {}, 'forex': {}, 'commodities': {}}
    with DATA_LOCK:
        for asset_type in strategy_cache:
            for asset in strategy_cache[asset_type]:
                if asset not in data["users"][username][asset_type]:
                    to_delete[asset_type][asset] = {}
                    continue
                for strategy in strategy_cache[asset_type][asset]:
                    if strategy not in data["users"][username][asset_type][asset]["strategies"]:
                        to_delete[asset_type][asset][strategy] = {}

    for asset_type in to_delete:
        for asset in to_delete[asset_type]:
            if not to_delete[asset_type].get(asset):
                del strategy_cache[asset_type][asset]
            for strategy in to_delete[asset_type][asset]:
                if not to_delete[asset_type][asset].get(strategy):
                    del strategy_cache[asset_type][asset][strategy]

def send_notification(data,username, title, message):
    with DATA_LOCK:
        desktop_notifications = data["users"][username]["notifications"]["desktop_notifications"]
        app_name = data["users"][username]["notifications"]["app_name"]
    if desktop_notifications:
        notification = Notify()
        notification.title = title
        notification.message = message
        notification.application_name = app_name
        notification.send()

def check_alarm(data,username,asset_type, code, strategy):
    is_alarm_triggered = False
    ticker = yf.Ticker(code)
    with DATA_LOCK:
        currency = data["users"][username][asset_type][code]["currency"]
        shortcut = data["users"][username][asset_type][code]["strategies"][strategy]
        alarm_type = shortcut["type"]
        financial_recommendations = data["users"][username]["notifications"]["financial_recommendations"]
        asset_financial_recommendation = data["users"][username][asset_type][code]['financial_recommendation']
    currency_symbol = utils.get_currency(currency)
    try:
        last_price = round(ticker.fast_info['lastPrice'], 2)
    except Exception:
        return [False, "", "", ""]

    title = f"{username}: {code} {alarm_type.replace('_', ' ').title()} Alarm"
    message = f"(Current Price: {last_price:.2f} {currency_symbol})"
    if alarm_type == "fixed_price":
        with DATA_LOCK:
            condition = shortcut["condition"]
            value = shortcut["value"]
        if condition == "lower_than":
            if last_price <= value:
                message += f" Fallen below {value} {currency_symbol}."
                if financial_recommendations and asset_financial_recommendation:
                    prediction = predict_direction(code, last_price)
                    if prediction == 1:
                        message += " Rise is expected, it is recommended to buy."
                    elif prediction == 0:
                        message += " Fall is expected, it is recommended to wait to buy."
                is_alarm_triggered = True
        elif condition == "greater_than":
            if last_price >= value:
                message += f" {value} {currency_symbol} has been exceeded."
                if financial_recommendations and asset_financial_recommendation:
                    prediction = predict_direction(code, last_price)
                    if prediction == 1:
                        message += " Rise is expected, it is recommended to wait to sell."
                    elif prediction == 0:
                        message += " Fall is expected, it is recommended to sell."
                is_alarm_triggered = True
    elif alarm_type == "period_extremum":
        if strategy_cache[asset_type].get(code):
            if strategy_cache[asset_type][code].get(strategy):
                hist_extremum = strategy_cache[asset_type][code][strategy]["hist_extremum"]
            else:
                return [False, "","",""]
        else:
            return [False, "","",""]
        try:
            today_df = ticker.history(interval="1d", period = "1d")
        except Exception:
            return None
        time.sleep(0.1)
        with DATA_LOCK:
            target = shortcut["target"]
            start_date = shortcut["start_date"]
        if hist_extremum:
            if target == "min":
                today_extremum = today_df["Low"].min()
            else:
                today_extremum = today_df["High"].max()
            extremum = hist_extremum if hist_extremum >= today_extremum else today_extremum
        else:
            extremum = today_df["Low"].min() if target == "min" else today_df["High"].max()
        if last_price > extremum and target == "max":
            message += f" The maximum price ({extremum} {currency_symbol}) of the period starting from {start_date} has been exceeded."
            if financial_recommendations and asset_financial_recommendation:
                prediction = predict_direction(code, last_price)
                if prediction == 1:
                    message += " Rise is expected, it is recommended to wait to sell."
                elif prediction == 0:
                    message += " Fall is expected, it is recommended to sell."
            is_alarm_triggered = True
        elif last_price < extremum and target == "min":
            message += f" Fallen below the minimum price ({extremum} {currency_symbol}) of the period starting from {start_date}."
            if financial_recommendations and asset_financial_recommendation:
                prediction = predict_direction(code, last_price)
                if prediction == 1:
                    message += " Rise is expected, it is recommended to buy."
                elif prediction == 0:
                    message += " Fall is expected, it is recommended to wait to buy."
            is_alarm_triggered = True
    elif alarm_type == "percentage_change":
        with DATA_LOCK:
            direction = shortcut["direction"]
            base_price = shortcut["base_price"]
            value = shortcut["value"]
        if direction == "rise":
            target_price = base_price * (100 + value)
        else:
            target_price = base_price * (100 - value)
        if last_price >= target_price and direction == "rise":
            message += f" Has increased by {value}% (reached {target_price} {currency_symbol}) compared to {base_price} {currency_symbol}"
            if financial_recommendations and asset_financial_recommendation:
                prediction = predict_direction(code, last_price)
                if prediction == 1:
                    message += " Rise is expected, it is recommended to wait to sell."
                elif prediction == 0:
                    message += " Fall is expected, it is recommended to sell."
            is_alarm_triggered = True
        elif last_price <= target_price and direction == "drop":
            message += f" Has decreased by {value}% (dropped to {target_price} {currency_symbol}) compared to {base_price} {currency_symbol}"
            if financial_recommendations and asset_financial_recommendation:
                prediction = predict_direction(code, last_price)
                if prediction == 1:
                    message += " Rise is expected, it is recommended to buy."
                elif prediction == 0:
                    message += " Fall is expected, it is recommended to wait to buy."
            is_alarm_triggered = True

    if is_alarm_triggered:
        send_notification(data, username, title, message)
    return [is_alarm_triggered, code, strategy, alarm_type]

def update_last_checked(data, username):
    now = datetime.now()
    with DATA_LOCK:
        data["users"][username]["last_checked"] = now.strftime("%Y-%m-%d %H:%M:%S")
    storage.save_temp(data)

def alarm_tracking(data,username):
    load_cache(data,username)
    load_models(username)
    counter = 5
    while not STOP_EVENT.is_set():
        active_alarms = []
        is_alarm_triggered = False
        with DATA_LOCK:
            for asset_type in data["users"][username]:
                if asset_type not in ["stocks", "crypto", "forex", "commodities"]:
                    continue
                for asset in data["users"][username][asset_type]:
                    if data["users"][username][asset_type][asset]["is_active"]:
                        for strategy in data["users"][username][asset_type][asset]["strategies"]:
                            if data["users"][username][asset_type][asset]["strategies"][strategy].get("status"):
                                active_alarms.append({'asset_type': asset_type, 'asset': asset, 'strategy': strategy})

        for alarm in active_alarms:
            # The `strategy` parameter in `check_alarm` refers to the alarm's index (key)
            # The `strategy` in `add_to_cache` refers to the alarm itself (which contains the type, value, etc.)
            check_alarm_tuple = check_alarm(data, username, alarm['asset_type'], alarm['asset'], alarm['strategy'])
            if check_alarm_tuple[0] and check_alarm_tuple[3] == "period_extremum":
                # if alarm is triggerred and alarm type is period_extremum,
                # hist_extremum must be updated
                with DATA_LOCK:
                    alarm_strategy = data["users"][username][alarm['asset_type']][alarm['asset']][alarm['strategy']]
                add_to_cache(alarm['asset_type'], alarm['asset'], alarm_strategy, alarm['strategy'])
            is_alarm_triggered = is_alarm_triggered or check_alarm_tuple[0]

        if (counter == 5 and not is_alarm_triggered) or is_alarm_triggered:
            update_last_checked(data,username)
            counter = 0
        counter += 1
        check_cache(data,username)
        load_models(username)
        STOP_EVENT.wait(45)