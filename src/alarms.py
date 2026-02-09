import yfinance as yf
import src.utils as utils
import src.storage as storage
from datetime import datetime
import threading
import time

def active_alarms(username, data):
    alarms = []
    for key in data["users"][username]["stocks"]:
        shortcut = data["users"][username]["stocks"][key]["strategies"]
        for strategy in shortcut:
            if shortcut.get(strategy) and shortcut[strategy].get("status") == "active":
                alarms.append(key)

    for key in data["users"][username]["crypto"]:
        shortcut = data["users"][username]["crypto"][key]["strategies"]
        for strategy in shortcut:
            if shortcut.get(strategy) and shortcut[strategy].get("status") == "active":
                alarms.append(key)

    for key in data["users"][username]["forex"]:
        shortcut = data["users"][username]["forex"][key]["strategies"]
        for strategy in shortcut:
            if shortcut.get(strategy) and shortcut[strategy].get("status") == "active":
                alarms.append(key)

    for key in data["users"][username]["commodities"]:
        shortcut = data["users"][username]["commodities"][key]["strategies"]
        for strategy in shortcut:
            if shortcut.get(strategy) and shortcut[strategy].get("status") == "active":
                alarms.append(key)

    return alarms

def alarm_status_decider():
    status = input("Do you want to activate the alarm (Y/N) (-1 to go back): ")
    if status == "-1":
        return ""
    status = utils.correct_input_format(status)
    while status not in ["y", "n", "yes", "no", "active", "inactive", "activate", "deactivate"]:
        print("Invalid status, please try again.")
        status = input("Do you want to activate the alarm (Y/N) (-1 to go back): ")
        if status == "-1":
            return ""
        status = utils.correct_input_format(status)
    if status in ["y", "yes", "active", "activate"]:
        status = "active"
    elif status in ["n", "no", "inactive", "deactivate"]:
        status = "inactive"
    return status


def status_change(shortcut, alarm_properties):
    if alarm_properties["status"] == "active":
        shortcut["status"] = "inactive"
    elif alarm_properties["status"] == "inactive":
        shortcut["status"] = "active"
    print(f"Alarm status is changed from {alarm_properties['status']} to {shortcut['status']}.")


def add_alarm(data, code, which_asset, username):
    alarm_type = input("Enter the type of alarm (Fixed Price, Period Extremum or Percentage Change) you want to add (-1 to go back): ")
    if alarm_type == "-1":
        return
    alarm_type = utils.correct_input_format(alarm_type)
    while alarm_type not in ["fixedprice", "periodextremum", "percentagechange"]:
        print("Alarm type must be fixed price, period extremum or percentage change.")
        alarm_type = input("Enter the type of alarm (Fixed Price, Period Extremum or Percentage Change) you want to add (-1 to go back): ")
        if alarm_type == "-1":
            return
        alarm_type = utils.correct_input_format(alarm_type)

    temp = data
    key = utils.find_empty_key(data["users"][username][which_asset][code]["strategies"])
    if alarm_type == "fixedprice":
        alarm_type = "fixed_price"
        currency = data["users"][username][which_asset][code]["currency"]
        currency_symbol = utils.get_currency(currency)
        value = float(input(f"Enter the fixed price in {currency_symbol} ({currency}) that will trigger the alarm (-1 to go back): "))
        while value < 0:
            if value == -1:
                return
            print("Fixed price cannot be negative, please try again.")
            value = float(input(f"Enter the fixed price in {currency_symbol} ({currency}) that will trigger the alarm (-1 to go back): "))
        condition = input(f"Enter the condition (lower or higher than {value}) that will trigger the alarm (-1 to go back): ")
        if condition == "-1":
            return
        condition = utils.correct_input_format(condition)
        while condition not in ["lower", "higher", "lowerthan", "higherthan", "lowerthanprice", "higherthanprice",
                                "lowerthanfixedprice", "higherthanfixedprice", "lowerthanfixedprice",
                                "higherthanfixedprice"]:
            print("Invalid condition, please try again.")
            condition = input(f"Enter the condition (lower or higher than {value}) that will trigger the alarm (-1 to go back): ")
            if condition == "-1":
                return
            condition = utils.correct_input_format(condition)
        if condition in ["lower", "lowerthan", "lowerthanprice", "lowerthanfixedprice"]:
            condition = "lower_than"
        elif condition in ["higher", "higherthan", "higherthanprice", "higherthanfixedprice"]:
            condition = "higher_than"
        status = alarm_status_decider()
        temp["users"][username][which_asset][code]["strategies"][key] = {
            "type": alarm_type,
            "condition": condition,
            "value": value,
            "status": status
        }
    elif alarm_type == "periodextremum":
        alarm_type = "period_extremum"
        status = alarm_status_decider()
        target = input("Enter the periodic target (minimum or maximum) that will trigger the alarm (-1 to go back): ")
        if target == "-1":
            return
        target = utils.correct_input_format(target)
        while target not in ["minimum", "maximum", "max", "min"]:
            print("Invalid target, please try again.")
            target = input(
                "Enter the periodic target (minimum or maximum) that will trigger the alarm (-1 to go back): ")
            if target == "-1":
                return
            target = utils.correct_input_format(target)
        start_date = input("Enter the start date (YYYY-MM-DD) of the period (-1 to go back): ")
        while not utils.is_valid_date(start_date):
            if start_date == "-1":
                return
            print("Invalid date or format, please try again.")
            start_date = input("Enter the start date (YYYY-MM-DD) of the period (-1 to go back): ")
        end_date = input("Enter the end date (YYYY-MM-DD) of the period (-1 to go back): ")
        while not utils.is_valid_date(end_date):
            if end_date == "-1":
                return
            print("Invalid date or date format, please try again.")
            end_date = input("Enter the end date (YYYY-MM-DD) of the period (-1 to go back): ")
        temp["users"][username][which_asset][code]["strategies"][key] = {
            "type": alarm_type,
            "target": target,
            "start_date": start_date,
            "end_date": end_date,
            "status": status
        }
    elif alarm_type == "percentagechange":
        alarm_type = "percentage_change"
        status = alarm_status_decider()
        direction = input("Enter the direction (drop or rise) of the alarm (-1 to go back): ")
        if direction == "-1":
            return
        direction = utils.correct_input_format(direction)
        while direction not in ["drop", "decrease", "reduce", "decline", "descent", "rise", "increase", "ascent",
                                "climb", "increment"]:
            print("Invalid direction, please try again.")
            direction = input("Enter the direction of the alarm (drop or rise): ")
            if direction == "-1":
                return
            direction = utils.correct_input_format(direction)
        if direction in ["drop", "decrease", "reduce", "decline", "descent"]:
            direction = "drop"
        elif direction in ["rise", "increase", "ascent", "climb", "increment"]:
            direction = "rise"
        value = input("Enter the percentage change amount that will trigger the alarm (-1 to go back): ")
        value = float(utils.correct_choice_format(value))
        while value < 0:
            if value == -1:
                return
            print("Invalid percentage change amount, please try again.")
            value = input("Enter the percentage change amount that will trigger the alarm (-1 to go back): ")
            value = float(utils.correct_choice_format(value))

        ticker = yf.Ticker(code)
        base_price = ticker.fast_info["lastPrice"]
        temp["users"][username][which_asset][code]["strategies"][key] = {
            "type": alarm_type,
            "direction": direction,
            "value": value,
            "base_price": base_price,
            "status": status
        }
    storage.save_temp(temp)
    print("Alarm is successfully added.")
    time.sleep(2)

def key_input(data, which_asset, code, username, which_function):
    key = input(f"Enter the number in the table corresponding to the alarm you want to {which_function} (-1 to go back): ")
    while int(key) < 1 or int(key) > len(data["users"][username][which_asset][code]["strategies"]):
        if key == "-1":
            return ""
        print("Invalid alarm number, please try again.")
        key = input(f"Enter the number in the table corresponding to the alarm you want to {which_function} (-1 to go back): ")
    return key



def edit_alarm(data, code, which_asset, username):
    the_key = key_input(data, which_asset, code, username, "edit")
    alarm_properties = data["users"][username][which_asset][code]["strategies"][the_key]
    for key in alarm_properties:
        s = key.replace("_", " ")
        print(f"{s.title():<15} |", end=" ")
    if alarm_properties["type"] == "fixed_price":
        print("_" * 55)
    else:
        print("_" * 70)
    for val in alarm_properties.values():
        val = val.replace("_", " ")
        print(f"{val.title():<15}", end="")
    print()
    i = 1
    for key in alarm_properties:
        if key == "type":
            continue
        s = key.replace("_", " ")
        print(f"[{i}] {s.title()}")
    length = len(alarm_properties)
    print(f"[{length}] Back")
    choice = input(f"Enter the option (1-{length}) corresponding the setting you want to change: ")
    choice = int(utils.correct_choice_format(choice))
    if choice == length:
        return
    while choice > length or choice < 1:
        print("Invalid choice, please try again.")
        choice = input(f"Enter the option (1-{length}) corresponding the setting you want to change: ")
        choice = int(utils.correct_choice_format(choice))
    temp = data
    shortcut = temp["users"][username][which_asset][code]["strategies"][the_key]
    if alarm_properties["type"] == "fixed_price":
        if choice == 1:
            if alarm_properties["condition"] == "lower_than":
                shortcut["condition"] = "higher_than"
            elif alarm_properties["condition"] == "higher_than":
                shortcut["condition"] = "lower_than"
            s1 = alarm_properties["condition"].replace("_", " ")
            s2 = shortcut["condition"].replace("_", " ")
            print(f"Trigger condition is changed from '{s1.title()}' to '{s2.title()}'.")
        elif choice == 2:
            value = input("Enter the new trigger value for the alarm (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("Value cannot be negative, please try again.")
                value = input("Enter the new trigger value for the alarm (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            shortcut["value"] = value
            old_value = alarm_properties["value"]
            print(f"Trigger value of alarm is changed from {old_value} to {value}.")
        elif choice == 3:
            status_change(shortcut, alarm_properties)
    elif alarm_properties["type"] == "period_extremum":
        if choice == 1:
            s1 = ""
            s2 = ""
            if alarm_properties["target"] == "max":
                shortcut["target"] = "min"
                s1 = "maximum"
                s2 = "minimum"
            elif alarm_properties["target"] == "min":
                shortcut["target"] = "max"
                s1 = "minimum"
                s2 = "maximum"
            print(f"Trigger target is changed from period '{s1}' to period '{s2}'.")
        elif choice == 2:
            start_date = input("Enter the start date (YYYY-MM-DD) for the alarm (-1 to go back): ")
            while not utils.is_valid_date(start_date):
                if start_date == "-1":
                    return
                print("Invalid date or date format, please try again.")
                start_date = input("Enter the start date (YYYY-MM-DD) for the alarm (-1 to go back): ")
            shortcut["start_date"] = start_date
            print(f"Start date is changed from {alarm_properties['start_date']} to {start_date}.")
        elif choice == 3:
            end_date = input("Enter the end date (YYYY-MM-DD) for the alarm (-1 to go back): ")
            while not utils.is_valid_date(end_date):
                if end_date == "-1":
                    return
                print("Invalid date or date format, please try again.")
                end_date = input("Enter the end date (YYYY-MM-DD) for the alarm (-1 to go back): ")
            shortcut["end_date"] = end_date
            s = alarm_properties["end_date"]
            print(f"End date is changed from {s} to {end_date}.")
        elif choice == 4:
            status_change(shortcut, alarm_properties)
    elif alarm_properties["type"] == "percentage_change":
        if choice == 1:
            if alarm_properties["direction"] == "drop":
                shortcut["direction"] = "rise"
            elif alarm_properties["direction"] == "rise":
                shortcut["direction"] = "drop"
            print(
                f"Percentage change direction is changed from '{alarm_properties['direction']}' to '{shortcut['direction']}'.")
        elif choice == 2:
            value = input("Enter the new value of percentage change trigger (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("The value of percentage change trigger cannot be negative, please try again.")
                value = input("Enter the new value of percentage change trigger (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            shortcut["value"] = value
            print(f"Value of percentage change trigger is changed from {alarm_properties['value']} to {value}.")
        elif choice == 3:
            value = input("Enter the new base price (reference point) for percentage change trigger (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("The value of base price cannot be negative, please try again.")
                value = input(
                    "Enter the new base price (reference point) for percentage change trigger (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            shortcut["base_price"] = value
            print(
                f"Base price for percentage change trigger is changed from {alarm_properties['base_price']} to {value}.")
        elif choice == 4:
            status_change(shortcut, alarm_properties)
    storage.save_temp(temp)
    print(f"Alarm {the_key} is edited successfully.")
    time.sleep(2)

def deactivate_all_alarms(data, code, which_asset, username):
    temp = data
    temp["users"][username][which_asset][code]["is_active"] = False
    storage.save_temp(temp)
    print(f"All alarms are deactivated.")
    time.sleep(2)

def delete_alarm(data, code, which_asset, username):
    key = key_input(data, which_asset, code, username,"delete")
    temp = data
    del temp["users"][username][which_asset][code]["strategies"][key]
    storage.save_temp(temp)
    print(f"Alarm {key} is deleted.")
    time.sleep(2)

def find_unit_price(info):
    unit_price = input(
        "Enter the unit price (if you do not enter any price, the current price will be used) (-1 to go back): ")
    while unit_price != "" and float(unit_price) < 0:
        if unit_price == "-1":
            return 0
        print("Invalid unit price, please try again.")
        unit_price = input(
            "Enter unit price (if you do not enter any price, the current price will be used) (-1 to go back): ")
    if unit_price == "":
        unit_price = info["lastPrice"]
    else:
        unit_price = float(unit_price)
    return unit_price

def edit_quantity(data, code, which_asset, username):
    quantity = data["users"][username][which_asset][code]["quantity"]
    total_cost = data["users"][username][which_asset][code]["total_cost"]
    currency = data["users"][username][which_asset][code]["currency"]
    currency_symbol = utils.get_currency(currency)
    print(f"--- Quantity: {quantity} | Total Cost: {total_cost} {currency_symbol}---\n")
    print(f"[1] Add (increase quantity)  new buy to {code}")
    print(f"[2] Sell (decrease quantity) from {code}")
    print(f"[3] Reset (re-enter quantity) of {code}")
    print("[4] Back")
    choice = input("Enter your choice (1-4): ")
    choice = int(utils.correct_choice_format(choice))
    while choice > 4 or choice < 1:
        print("Invalid choice, please try again.")
        choice = input("Enter your choice (1-4): ")
        choice = int(utils.correct_choice_format(choice))

    # immediate return to avoid copies and API requests
    if choice == 4:
        return

    temp = data
    ticker = yf.Ticker(code)
    info = ticker.fast_info
    if choice == 1:
        add_quantity = float(input(f"Enter how many {code} you purchased (-1 to go back): "))
        while add_quantity < 0:
            if add_quantity == "-1":
                return
            print("Amount of purchase cannot be negative, please try again.")
            add_quantity = float(input(f"Enter how many {code} you purchased (-1 to go back): "))
        unit_price = find_unit_price(info)
        temp["users"][username][which_asset][code]["total_cost"] += unit_price * add_quantity
        temp["users"][username][which_asset][code]["quantity"] += add_quantity
    elif choice == 2:
        while True:
            sell_quantity = float(input(f"Enter how many {code} you sold (-1 to go back): "))
            if sell_quantity == "-1":
                return
            if sell_quantity > quantity:
                print("You cannot sell more than what you have, please try again.")
                continue
            if sell_quantity < 0:
                print("Amount of sales cannot be negative, please try again.")
                continue
            break
        avg_price = total_cost / quantity
        temp["users"][username][which_asset][code]["total_cost"] -= avg_price * sell_quantity
        temp["users"][username][which_asset][code]["quantity"] -= sell_quantity
        unit_price = find_unit_price(info)
        gain = (unit_price - avg_price) * sell_quantity
        if gain < 0:
            print(f"Loss from this sale is {gain} {currency_symbol}.")
        elif gain > 0:
            print(f"Profit from this sale is {gain} {currency_symbol}.")
        else:
            print("There is no gain or loss from this sale.")
    elif choice == 3:
        quantity = float(input(f"Enter the quantity of the {code} (-1 to go back): "))
        while quantity < 0:
            if quantity == -1:
                return
            print("Quantity cannot be negative, please try again.")
            quantity = float(input(f"Enter the quantity of the {code} (-1 to go back): "))
        if quantity > 0:
            total_cost = float(input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): "))
            while total_cost < 0:
                if total_cost == -1:
                    return
                print("Total cost cannot be negative, please try again.")
                total_cost = float(input(f"Enter the total cost of {quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): "))
    storage.save_temp(temp)
    print(f"Quantity is changed from {quantity} to {temp['users'][username][which_asset][code]['quantity']}.")
    time.sleep(2)
