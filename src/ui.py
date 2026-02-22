import src.utils as utils
from datetime import datetime
import yfinance as yf
import src.alarms as alarms_lib
from src.tracking import DATA_LOCK

def entrance(data):
    with DATA_LOCK:
        if data.get("users"):
            print("[1] Login into account")
            print("[2] Create new user")
            print("[3] Delete user")
            print("[4] Exit")
        else:
            print("[1] Create new user")
            print("[2] Exit")

def print_title():
    print("\n" + "=" * 60)
    name = "Financial Tracking Assistant"
    print(f"{name:^60}")
    print("=" * 60 + "\n")

def table_headers():
    a = "Code"
    b = "Latest Price"
    c = "Change(%)"
    d = "Status"
    e = "Alarm"
    print(f"   {a:<20}{b:<20}{c:<12}{d:<12}{e:<20}")
    print("-" * 90)

def detail_menu(financial_asset, code):
    with DATA_LOCK:
        name = financial_asset.get("name")
        currency = financial_asset.get("currency")
        quantity = financial_asset.get("quantity")
        total_cost = financial_asset.get("total_cost")
    currency_symbol = utils.get_currency(currency)
    print("="*12 + f"  {code}  " + "="*12 + "\n")
    ticker = yf.Ticker(code)
    last_price = ticker.fast_info['lastPrice']
    earning = (last_price * quantity - total_cost) / total_cost * 100
    earning_str = ""
    if earning > 0: earning_str += "+"
    earning_str += f"{earning:.2f}%"
    print(f"[Name]: {name}")
    print(f"[Price]: {last_price:.2f} {currency_symbol}")
    print(f"[Quantity]: {quantity}")
    print(f"[Total Value]: {(quantity * last_price):.2f} {currency_symbol} ({earning_str})\n")
    print("=" * 12 + "=" * (len(code) + 4) + "=" * 12 + "\n")
    print_all_alarms(financial_asset)
    print("[1] Financial Analysis Report (RSI, Trend, Volatility, Volume)")
    print("[2] Add a new alarm strategy")
    print("[3] Edit an existing alarm strategy")
    print("[4] Delete an alarm strategy")
    print("[5] Activate all alarms")
    print("[6] Deactivate all alarms")
    print("[7] Edit the quantity and the total cost")
    print("[8] Back")

def period_extremum(strategy):
    with DATA_LOCK:
        alarm_range = strategy["target"].title()
        start_date = datetime.strptime(strategy.get("start_date"), "%Y-%m-%d")
    alarm_range += f" (Start: "
    now = datetime.now()
    if start_date.year == now.year:
        if start_date.month == now.month:
            if start_date.day == now.day:
                alarm_range += "Today)"
            else:
                alarm_range += f"{start_date.strftime('%m-%d')})"
        else:
            alarm_range += f"{start_date.strftime('%m-%d')})"
    else:
        alarm_range += f"{start_date.strftime('%Y-%m-%d')})"
    return alarm_range

def print_all_alarms(financial_asset):
    print(f"    {'Alarm':<25}{'Status':<15}")
    print("-"*40)
    with DATA_LOCK:
        key_list = list(financial_asset["strategies"].keys())
    for key in key_list:
        with DATA_LOCK:
            status = financial_asset["strategies"][key]["status"].title()
            alarm_type = financial_asset["strategies"][key]["type"]
            currency = utils.get_currency(financial_asset.get("currency"))
        alarm = ""
        if alarm_type == "fixed_price":
            with DATA_LOCK:
                condition = financial_asset["strategies"][key]["condition"]
                value = financial_asset["strategies"][key]["value"]
            if condition == "lower_than":
                alarm = f"<={value} {currency}"
            elif condition == "greater_than":
                alarm = f">={value} {currency}"
        elif alarm_type == "percentage_change":
            with DATA_LOCK:
                direction = financial_asset["strategies"][key]["direction"]
                value = financial_asset["strategies"][key]["value"]
            if direction == "rise":
                alarm = f"+%{value}"
            elif direction == "drop":
                alarm = f"-%{value}"
        elif alarm_type == "period_extremum":
            with DATA_LOCK:
                strategy = financial_asset["strategies"][key]
            alarm = period_extremum(strategy)
        row = f"{key}.  {alarm:<25}{status:<15}"
        print(row)
    print()

def helper_calculate_total(data, username, asset_type, default_currency):
    with DATA_LOCK:
        asset_list = list(data["users"][username][asset_type].keys())
    total_cost = 0
    total_value = 0
    for asset in asset_list:
        with DATA_LOCK:
            currency = data["users"][username][asset_type][asset]["currency"]
            quantity = data["users"][username][asset_type][asset]["quantity"]
            total_cost_currency = data["users"][username][asset_type][asset]["total_cost"]
        ticker = yf.Ticker(asset)
        last_price_asset = ticker.fast_info["lastPrice"]
        if currency != default_currency:
            currency_ticker_code = currency + default_currency + "=X"
            currency_ticker = yf.Ticker(currency_ticker_code)
            last_price = currency_ticker.fast_info["lastPrice"]
            total_cost += total_cost_currency * last_price
            total_value += last_price_asset * last_price * quantity
        else:
            total_cost += total_cost_currency
            total_value += last_price_asset * quantity
    return [total_cost, total_value]

def calculate_total(data, username):
    total_cost = 0
    total_value = 0
    with DATA_LOCK:
        default_currency = data["users"][username]["default_currency"]
        key_list = list(data["users"][username].keys())
    for key in key_list:
        if key in ["password", "language", "default_currency", "last_checked", "notifications"]:
            continue
        temp_list = helper_calculate_total(data, username, key, default_currency)
        total_cost += temp_list[0]
        total_value += temp_list[1]

    if total_cost != 0:
        earning = (total_value - total_cost) / total_cost * 100
    else:
        earning = 0
    currency_symbol = utils.get_currency(default_currency)
    text = f"[Total Value]: {total_value:.2f} {currency_symbol}"
    if earning < 0:
        text += f" ({earning:.2f}%)"
    elif earning > 0:
        text += f" (+{earning:.2f}%)"
    return text

def print_alarms_main_menu(alarms):
    print("[", end = "")
    length = len(alarms)
    i = 1
    for asset in alarms:
        if i == length and alarms[asset]['count'] == 0:
            print(asset, end = "")
        else:
            print(asset, end = " ")
        if alarms[asset]['count'] > 0 and i != length:
            print(f"({alarms[asset]['count']+1})", end = ", ")
        elif alarms[asset]['count'] > 0 and i == length:
            print(f"({alarms[asset]['count']+1})", end = "")
        i += 1
    print("]")

def length_of_alarms(alarms):
    alarm_count = 0
    for asset in alarms:
        alarm_count += alarms[asset]['count'] + 1
    return alarm_count

def main_menu(username, data):
    print("\n" + "=" * 60)
    name = "Financial Tracking Assistant"
    print(f"{name:^60}")
    print("=" * 60)

    print(f"[user]: {username}")
    with DATA_LOCK:
        stock_count = len(data["users"][username]["stocks"])
        crypto_count = len(data["users"][username]["crypto"])
        forex_count = len(data["users"][username]["forex"])
        commodity_count = len(data["users"][username]["commodities"])
    portfolio = f"[Portfolio]: {stock_count} Stock"
    if stock_count > 1: portfolio += "s"
    portfolio += f" | {crypto_count} Crypto"
    if crypto_count > 1: portfolio += "s"
    portfolio += f" | {forex_count} Forex"
    if forex_count > 1: portfolio += "es"
    portfolio += f" | {commodity_count} Commodit"
    if commodity_count > 1: portfolio += "ies"
    else: portfolio += "y"
    print(portfolio)
    print(calculate_total(data, username))
    alarms = alarms_lib.active_alarms(username, data)
    alarm_count = length_of_alarms(alarms)
    if alarm_count > 1:
        print(f"[Active Alarms]: {alarm_count} Alarms", end = " ")
        print_alarms_main_menu(alarms)
    elif alarm_count == 1:
        print(f"[Active Alarms]: {alarm_count} Alarm", end = " ")
        print_alarms_main_menu(alarms)
    else:
        print(f"[Active Alarms]: {alarm_count}")
    with DATA_LOCK:
        last_update = data["users"][username].get("last_checked")
    if last_update:
        print(f"[Last Alarm Check]: {last_update}")

    print("=" * 60 + "\n")

    print("   MAIN MENU")
    print("=" * 15 + "\n")
    print("[1] Stock Management")
    print("[2] Crypto Management")
    print("[3] Forex Management")
    print("[4] Commodity Management")
    print("[5] Settings")
    print("[6] Log out")
    print("[7] Exit\n")

def transaction_management_menu(data, username, which_asset):
    if which_asset == "stocks":
        title = "Stock"
    elif which_asset == "commodities":
        title = "Commodity"
    else:
        title = which_asset

    print("\n" + "="*27 + f"  {title.title()} Management  " + "="*27 + "\n")
    with DATA_LOCK:
         is_not_empty = data["users"][username].get(which_asset)
    if is_not_empty:
        table_headers()
        i = 1
        with DATA_LOCK:
            asset_list = list(data["users"][username][which_asset].keys())
        for key in asset_list:
            ticker = yf.Ticker(key)
            df = ticker.history(period="2d", interval="1m")
            current_price = df["Close"].iloc[-1]
            yesterday_close = ticker.history(period="2d", interval="1d")["Close"].iloc[0]
            change = (current_price - yesterday_close) / yesterday_close * 100
            with DATA_LOCK:
                currency = data["users"][username][which_asset][key]["currency"]
                if data["users"][username][which_asset][key]["is_active"]:
                    status = "Active"
                else:
                    status = "Inactive"
                count = len(data["users"][username][which_asset][key]["strategies"])
                if count > 0:
                    alarm_type = data["users"][username][which_asset][key]["strategies"]["1"]["type"]
                else:
                    alarm_type = ""
            currency_symbol = utils.get_currency(currency)
            alarm = ""
            if alarm_type == "fixed_price":
                with DATA_LOCK:
                    condition = data["users"][username][which_asset][key]["strategies"]["1"]["condition"]
                    value = data["users"][username][which_asset][key]["strategies"]["1"]["value"]
                if condition == "lower_than":
                    alarm = f"<={value:.2f} {currency}"
                elif condition == "greater_than":
                    alarm = f">={value:.2f} {currency}"
            elif alarm_type == "percentage_change":
                with DATA_LOCK:
                    direction = data["users"][username][which_asset][key]["strategies"]["1"]["direction"]
                    value = data["users"][username][which_asset][key]["strategies"]["1"]["value"]
                if direction == "rise":
                    alarm = f"+%{value:.2f}"
                elif direction == "drop":
                    alarm = f"-%{value:.2f}"
            elif alarm_type == "period_extremum":
                with DATA_LOCK:
                    strategy = data["users"][username][which_asset][key]["strategies"]["1"]
                alarm = period_extremum(strategy)
            current_price_str = f"{current_price:.2f} ({currency_symbol})"
            change_str = ""
            if change > 0: change_str += "+"
            change_str += f"{change:.2f}%"
            if count > 1: alarm += f" (+{count - 1})"
            row = f"{i}. {key:<20}{current_price_str:<20}{change_str:<12}{status:<12}{alarm:<20}"
            i += 1
            print(row)
        print(f"\n{'OPERATIONS':^20}")
        print("="*20 + "\n")
        print("[A]dd : Add a new stock to the list")
        print("[R]emove : Remove the stock from the list")
        print("[D]etail : Go to the detail of the stock (Analysis & Alarm)")
        print("[B]ack : Back to main menu")
    else:
        print(f"\n{'OPERATIONS':^20}")
        print("=" * 20 + "\n")
        print("[A]dd : Add a new stock to the list")
        print("[B]ack : Back to main menu")
    with DATA_LOCK:
        return data["users"][username][which_asset]

def setting_menu():
    print("=" * 10 + " SETTINGS " + "=" * 10 + "\n")
    print("[1] Account Settings")
    print("[2] Notification Settings")
    print("[3] Change Portfolio Currency")

def account_settings_menu():
    print("\n" + "=" * 10 + " Account Settings " + "=" * 10 + "\n")
    print("[1] Change Username")
    print("[2] Change Password")

def notification_settings_menu(data, logged_user):
    print("\n" + "=" * 10 + " Notification Settings " + "=" * 10 + "\n")
    with DATA_LOCK:
        if data["users"][logged_user]["notifications"]["desktop_notifications"]:
            print("[1] Turn off the notifications")
        else:
            print("[1] Turn on the notifications")
    print("[2] Change the name of app")
    print("[3] Change the duration of the notifications")
