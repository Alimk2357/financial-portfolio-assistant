import src.utils as utils
from datetime import datetime
import yfinance as yf
import src.alarms as alarms_lib

def entrance(data):
    # "users" may not exist, in that case get() returns None
    # None is falsy in Python
    if data.get("users"):
        print("1- Login into account")
        print("2- Create new user")
        print("3- Delete user")
        print("4- Exit")
    else:
        print("1- Create new user")
        print("2- Exit")

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


def detail_menu(financial_asset, code):
    name = financial_asset.get("name")
    currency = financial_asset.get("currency")
    currency_symbol = utils.get_currency(currency)
    last_update = ""
    if financial_asset.get("last_checked"):
        last_update = datetime.strptime(financial_asset.get("last_checked"), "%Y-%m-%d %H:%M:%S")
    print(f"=== Detail: {name} ({code}) ===")
    sub_title = ""
    if last_update != "":
        sub_title = f"[Last Update]: {last_update.strftime('%Y-%m-%d %H:%M:%S')}"
    sub_title += f"\n[Currency]: {currency}"
    if currency != currency_symbol: sub_title += f" ({currency_symbol})"
    print(f"{sub_title}\n")
    print_all_alarms(financial_asset)
    print("[1] Financial Analysis Report (RSI, Trend, Volatility, Volume)")
    print("[2] Add a new alarm strategy")
    print("[3] Edit an existing alarm strategy")
    print("[4] Delete an alarm strategy")
    print("[5] Deactivate all alarms")
    print("[6] Edit the quantity and the total cost")
    print("[7] Back")

def period_extremum(strategy):
    alarm_range = strategy["target"].title()
    start_date = datetime.strptime(strategy.get("start_date"), "%Y-%m-%d")
    if strategy.get("end_date"):
        end_date = datetime.strptime(strategy.get("end_date"), "%Y-%m-%d")
        if start_date.year == end_date.year:
            # DD.MM - DD.MM
            alarm_range += f" ({start_date.day}.{start_date.month} - {end_date.day}.{end_date.month})"
        else:
            # MM.YY - MM.YY
            alarm_range += f" ({start_date.month}.{start_date.year} - {end_date.month}.{end_date.year})"
    else:
        # last X days
        end_date = datetime.now()
        day_count = end_date.day - start_date.day
        alarm_range = f" (Last {end_date.day - start_date.day} day"
        if day_count > 1:
            alarm_range += "s)"
        else:
            alarm_range += ")"

    return alarm_range


def print_all_alarms(financial_asset):
    for key in financial_asset["strategies"]:
        status = financial_asset["strategies"][key]["status"].title()
        alarm_type = financial_asset["strategies"][key]["type"]
        currency = utils.get_currency(financial_asset.get("currency"))
        alarm = ""
        if alarm_type == "fixed_price":
            condition = financial_asset["strategies"][key]["condition"]
            value = financial_asset["strategies"][key]["value"]
            if condition == "lower_than":
                alarm = f"<{value} {currency}"
            elif condition == "greater_than":
                alarm = f">{value} {currency}"
        elif alarm_type == "percentage_change":
            direction = financial_asset["strategies"][key]["direction"]
            value = financial_asset["strategies"][key]["value"]
            if direction == "rise":
                alarm = f"+%{value}"
            elif direction == "drop":
                alarm = f"-%{value}"
        elif alarm_type == "period_extremum":
            alarm = period_extremum(financial_asset["strategies"][key])
        row = f"{key}. {status:<15}{alarm:<24}"
        print(row)
    print()

def helper_calculate_total(data, username, asset_type):
    default_currency = data["users"][username]["default_currency"]
    total_cost = 0
    total_value = 0
    for key in data["users"][username][asset_type]:
        currency = data["users"][username]["stocks"][key]["currency"]
        quantity = data["users"][username]["stocks"][key]["quantity"]
        total_cost_currency = data["users"][username]["stocks"][key]["total_cost"]
        ticker = yf.Ticker(key)
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
    default_currency = data["users"][username]["default_currency"]
    for key in data["users"][username]:
        if key in ["password", "language", "default_currency"]:
            continue
        temp_list = helper_calculate_total(data, username, key)
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

def main_menu(username, data):
    print("\n" + "=" * 60)
    name = "Financial Tracking Assistant"
    print(f"{name:^60}")
    print("=" * 60)

    print(f"[user]: {username}")

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
    alarm_count = len(alarms)
    if alarm_count > 1:
        print(f"[Active Alarms]: {alarm_count} Alarms ", alarms)
    elif alarm_count == 1:
        print(f"[Active Alarms]: {alarm_count} Alarm ", alarms)
    else:
        print(f"[Active Alarms]: {alarm_count}")


    print("=" * 60 + "\n")

    print("MAIN MENU")
    print("=" * 12)
    print("1- Stock Management")
    print("2- Crypto Management")
    print("3- Forex Management")
    print("4- Commodity Management")
    print("5- Settings")
    print("6- Log out")
    print("7- Exit\n")

def transaction_management_menu(data, username, which_asset):
    if which_asset == "stocks":
        title = "Stock"
    elif which_asset == "commodities":
        title = "Commodity"
    else:
        title = which_asset

    print(f"\n=== {title.title()} Management ===\n")
    if data["users"][username].get(which_asset):
        table_headers()
        i = 1
        for key in data["users"][username][which_asset]:
            ticker = yf.Ticker(key)
            df = ticker.history(period="2d", interval="1m")
            current_price = df["Close"].iloc[-1]
            currency = data["users"][username][which_asset][key]["currency"]
            currency_symbol = utils.get_currency(currency)
            yesterday_close = ticker.history(period="2d", interval="1d")["Close"].iloc[0]
            change = (current_price - yesterday_close) / yesterday_close * 100
            if data["users"][username][which_asset][key]["is_active"]:
                status = "Active"
            else:
                status = "Inactive"
            count = len(data["users"][username][which_asset][key]["strategies"])
            alarm = ""
            if count > 0:
                alarm_type = data["users"][username][which_asset][key]["strategies"]["1"]["type"]
                currency = utils.get_currency(data["users"][username][which_asset][key].get("currency"))
                if alarm_type == "fixed_price":
                    condition = data["users"][username][which_asset][key]["strategies"]["1"]["condition"]
                    value = data["users"][username][which_asset][key]["strategies"]["1"]["value"]
                    if condition == "lower_than":
                        alarm = f"<{value} {currency}"
                    elif condition == "greater_than":
                        alarm = f">{value} {currency}"
                elif alarm_type == "percentage_change":
                    direction = data["users"][username][which_asset][key]["strategies"]["1"]["direction"]
                    value = data["users"][username][which_asset][key]["strategies"]["1"]["value"]
                    if direction == "rise":
                        alarm = f"+%{value}"
                    elif direction == "drop":
                        alarm = f"-%{value}"
                elif alarm_type == "period_extremum":
                    alarm = period_extremum(data["users"][username][which_asset][key]["strategies"]["1"])
            row = f"{i}. {key:<20}{current_price:<20.2f} {currency_symbol}{change:<12.2f}{status:<12}{alarm:<20}"
            i += 1
            if count > 1: row += f" (+{count - 1})"
            print(row)
        print("\nOPERATIONS")
        print("="*12)
        print("[A]dd : Add a new stock to the list")
        print("[R]emove : Remove the stock from the list")
        print("[D]etail : Go to the detail of the stock (Analysis & Alarm)")
        print("[B]ack : Back to main menu")
    else:
        print("\nOPERATIONS")
        print("[A]dd : Add a new stock to the list")
        print("[B]ack : Back to main menu")
    return data["users"][username][which_asset]


def setting_menu(data, logged_user):
    pass

