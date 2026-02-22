import yfinance as yf
import src.utils as utils
import src.storage as storage
import logging
from src.tracking import DATA_LOCK

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

def add_financial_asset(data, which_asset, username):
    ticker = None
    while True:
        code = input(f"\nEnter the Ticker (symbol) of the financial asset you want to add to {which_asset} list (-1 to go back): ").upper()
        if code == "-1":
            return

        with DATA_LOCK:
            if code in data["users"][username][which_asset]:
                print(f"{code} is already exists in portfolio of {username}.")
                continue

        ticker = yf.Ticker(code)
        if ticker.history(period="1d", interval="1d").empty:
            print(f"{code} does not belong to a valid financial asset.")
            continue
        break

    quantity = input(f"Enter the quantity of the {code} (-1 to go back): ")
    quantity = float(utils.correct_choice_format(quantity))
    while quantity < 0:
        if quantity == -1:
            return
        print("Quantity cannot be negative, please try again.")
        quantity = input(f"Enter the quantity of the {code} (-1 to go back): ")
        quantity = float(utils.correct_choice_format(quantity))

    total_cost = 0
    info = ticker.info
    currency = info["currency"]
    currency_symbol = utils.get_currency(currency)
    if quantity > 0:
        total_cost = input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): ")
        total_cost = float(utils.correct_choice_format(total_cost))
        while total_cost < 0:
            if total_cost == -1:
                return
            print("Total cost cannot be negative, please try again.")
            total_cost = input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): ")
            total_cost = float(utils.correct_choice_format(total_cost))
    with DATA_LOCK:
        data["users"][username][which_asset][code.upper()] = {
            "name": info["shortName"],
            "currency": currency,
            "quantity": quantity,
            "total_cost": total_cost,
            "is_active": False,
            "strategies": {}
        }
    storage.save_temp(data)
    print(f"{quantity} {code} is added successfully to portfolio of {username}.")


def remove_financial_asset(data, which_asset, username, code):
    with DATA_LOCK:
        del data["users"][username][which_asset][code]
    storage.save_temp(data)
    print(f"{code} is removed successfully from portfolio of {username}.")



