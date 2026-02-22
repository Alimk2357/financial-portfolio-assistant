import yfinance as yf
from plyer import notification
from datetime import datetime, timedelta
import src.utils as utils
import src.storage as storage
import time
import threading

DATA_LOCK = threading.Lock()
STOP_EVENT = threading.Event()
strategy_cache = {'stocks': {}, 'crypto':{},'forex':{}, 'commodities':{}}

def add_to_cache(asset_type,asset, strategy, strategy_key):
    ticker = yf.Ticker(asset)
    today_date = datetime.today().date()
    yesterday_date = today_date - timedelta(days=1)
    hist_df = ticker.history(interval="1d", start=strategy["start_date"], end=yesterday_date)
    hist_extremum = None
    if not hist_df.empty:
        if strategy["target"] == "min":
            hist_extremum = hist_df["Low"].min()
        else:
            hist_extremum = hist_df["High"].max()
    strategy_cache[asset_type][asset][strategy_key] = {"start_date": strategy["start_date"], "hist_extremum": hist_extremum}
    time.sleep(1)

def load_cache(data,username):
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
                        add_to_cache(asset_type,asset, shortcut, strategy)

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
                        elif strategy_cache[asset_type][asset].get(strategy):
                            to_add[asset_type][asset] = {strategy: {"start_date": shortcut['start_date'], "target": shortcut['target']}}
                        elif strategy['start_date'] != strategy_cache[asset_type][asset][strategy].get('start_date'):
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
    if data["users"][username]["notifications"]["desktop_notification"]:
        notification.notify(
            title=title,
            message=message,
            app_name= data["users"][username]["notifications"]["app_name"],
            timeout= data["users"][username]["notifications"]["timeout"]
        )

def check_alarm(data,username,asset_type, code, strategy):
    is_alarm_triggered = False
    ticker = yf.Ticker(code)
    currency = data["users"][username][asset_type][code]["currency"]
    currency_symbol = utils.get_currency(currency)
    shortcut = data["users"][username][asset_type][code]["strategies"][strategy]
    title = f"{username}: {code} {shortcut['type'].replace('_', ' ').title()} Alarm"
    if shortcut["type"] == "fixed_price":
        last_price = ticker.fast_info['lastPrice']
        title += f"(Current Price: {last_price})"
        if shortcut["condition"] == "lower_than":
            if last_price <= shortcut["value"]:
                message = f"Fallen below {shortcut['value']} {currency_symbol}"
                send_notification(data, username, title, message)
                is_alarm_triggered = True
        elif shortcut["condition"] == "greater_than":
            if last_price >= shortcut["value"]:
                message = f"{shortcut['value']} {currency_symbol} has been exceeded"
                send_notification(data, username, title, message)
                is_alarm_triggered = True
    elif shortcut["type"] == "period_extremum":
        hist_extremum = strategy_cache[asset_type][code][strategy]["hist_extremum"]
        today_df = ticker.history(interval="1d", period = "1d")
        time.sleep(0.1)
        last_price = ticker.fast_info['lastPrice']
        title += f"(Current Price: {last_price})"
        if hist_extremum:
            if shortcut["target"] == "min":
                today_extremum = today_df["Low"].min()
            else:
                today_extremum = today_df["High"].max()
            extremum = hist_extremum if hist_extremum >= today_extremum else today_extremum
        else:
            extremum = today_df["Low"].min() if shortcut["target"] == "min" else today_df["High"].max()

        if last_price > extremum and shortcut["target"] == "max":
            message = f"The maximum price ({extremum} {currency_symbol}) of the period starting from {shortcut['start_date']} has been exceeded."
            send_notification(data, username, title, message)
            is_alarm_triggered = True
        elif last_price < extremum and shortcut["target"] == "min":
            message = f"Fallen below the minimum price ({extremum} {currency_symbol}) of the period starting from {shortcut['start_date']}."
            send_notification(data, username, title, message)
            is_alarm_triggered = True
    elif shortcut["type"] == "percentage_change":
        if shortcut["direction"] == "rise":
            target_price = shortcut['base_price'] * (100 + shortcut['value'])
        else:
            target_price = shortcut['base_price'] * (100 - shortcut['value'])
        last_price = ticker.fast_info['lastPrice']
        title += f"(Current Price: {last_price})"
        if last_price >= target_price and shortcut["direction"] == "rise":
            message = f"Has increased by {shortcut['value']}% (reached {target_price} {currency_symbol}) compared to {shortcut['base_price']} {currency_symbol}"
            send_notification(data, username, title, message)
            is_alarm_triggered = True
        elif last_price <= target_price and shortcut["direction"] == "drop":
            message = f"Has decreased by {shortcut['value']}% (dropped to {target_price} {currency_symbol}) compared to {shortcut['base_price']} {currency_symbol}"
            send_notification(data, username, title, message)
            is_alarm_triggered = True
    return is_alarm_triggered

def update_last_checked(data, username):
    now = datetime.now()
    with DATA_LOCK:
        data["users"][username]["last_checked"] = now.strftime("%Y-%m-%d %H:%M:%S")
    storage.save_temp(data)

def alarm_tracking(data,username):
    load_cache(data,username)
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
                            active_alarms.append({'asset_type': asset_type, 'asset': asset, 'strategy': strategy})

        for alarm in active_alarms:
            is_alarm_triggered = is_alarm_triggered or check_alarm(data, username, alarm['asset_type'], alarm['asset'], alarm['strategy'])

        if (counter == 5 and not is_alarm_triggered) or is_alarm_triggered:
            update_last_checked(data,username)
            counter = 0
        counter += 1
        check_cache(data,username)
        STOP_EVENT.wait(45)