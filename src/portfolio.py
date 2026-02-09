import yfinance as yf
import src.utils as utils
import src.storage as storage
import logging

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

def add_financial_asset(data, which_asset, username):
    ticker = None
    while True:
        code = input(f"\nEnter the Ticker (symbol) of the financial asset you want to add to {which_asset} list (-1 to go back): ").upper()
        if code == "-1":
            return
        if code in data["users"][username][which_asset]:
            print(f"{code} is already exists in portfolio of {username}.")
            continue

        ticker = yf.Ticker(code)
        if ticker.history(period="1d", interval="1d").empty:
            print(f"{code} does not belong to a valid financial asset.")
            continue
        break

    quantity = float(input(f"Enter the quantity of the {code} (-1 to go back): "))
    while quantity < 0:
        if quantity == -1:
            return
        print("Quantity cannot be negative, please try again.")
        quantity = float(input(f"Enter the quantity of the {code} (-1 to go back): "))

    total_cost = 0
    info = ticker.info
    currency = info["currency"]
    currency_symbol = utils.get_currency(currency)
    if quantity > 0:
        total_cost = float(input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): "))
        while total_cost < 0:
            if total_cost == -1:
                return
            print("Total cost cannot be negative, please try again.")
            total_cost = float(input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): "))
    temp = data
    temp["users"][username][which_asset][code.upper()] = {
        "name": info["shortName"],
        "currency": currency,
        "quantity": quantity,
        "total_cost": total_cost,
        "last_checked": None,
        "is_active": False,
        "strategies": {}
    }
    storage.save_temp(temp)
    print(f"{quantity} {code} is added successfully to portfolio of {username}.")


def remove_financial_asset(data, which_asset, username, code):
    """
    while True:
        code = input(f"\nEnter the Ticker (symbol) of the financial asset you want to remove from {which_asset} list (-1 to go back): ")
        if code == "-1":
            return
        if code not in data["users"][username][which_asset]:
            print(f"{code} does not exists in portfolio of {username}.")
            continue

        ticker = yf.Ticker(code)
        if ticker.history(period="1d", interval="1d").empty:
            print(f"{code} does not belong to a valid financial asset.")
            continue
        break
    """
    temp = data
    del temp["users"][username][which_asset][code]
    storage.save_temp(temp)
    print(f"{code} is removed successfully from portfolio of {username}.")



