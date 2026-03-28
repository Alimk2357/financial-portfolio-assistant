import multiprocessing as mp
import yfinance as yf
import src.utils as utils
import src.storage as storage
import logging
from src.shared import DATA_LOCK
import src.model as model

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

def add_financial_asset(data, which_asset, username):
    ticker = None
    while True:
        code = input(f"\nEnter the Ticker (symbol) of the financial asset you want to add to {which_asset} list (-1 to go back): ").upper().strip()
        if code == "-1":
            return

        with DATA_LOCK:
            if code in data["users"][username][which_asset]:
                print(f"{code} is already exists in portfolio of {username}.")
                continue

        ticker = yf.Ticker(code)
        try:
            if ticker.history(period="1d", interval="1d").empty:
                print(f"{code} does not belong to a valid financial asset.")
                continue
        except Exception as e:
            print(f"[ERROR]: Data could not fetched for {code} (API Error). {code} could not be added. Please try again.")
            return
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
        recommendation = data["users"][username]["notifications"]["financial_recommendations"]
        data["users"][username][which_asset][code.upper()] = {
            "name": info["shortName"],
            "currency": currency,
            "quantity": quantity,
            "total_cost": total_cost,
            "is_active": False,
            "financial_recommendation": recommendation,
            "strategies": {}
        }
    storage.save_temp(data)
    print(f"{quantity} {code} is added successfully to portfolio of {username}.")
    model_trainer = mp.Process(
        target = model.train_model,
        args = (username, code)
    )
    model_trainer.start()

def remove_financial_asset(data, which_asset, username, code):
    with DATA_LOCK:
        del data["users"][username][which_asset][code]
    storage.save_temp(data)
    print(f"{code} is removed successfully from portfolio of {username}.")
    model.delete_model(username,code)


