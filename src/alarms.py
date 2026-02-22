import yfinance as yf
import src.utils as utils
import src.storage as storage
import time
from src.tracking import DATA_LOCK

def active_alarms(username, data):
    alarms = {}
    with DATA_LOCK:
        for asset_type in data["users"][username]:
            if asset_type not in ['stocks', 'crypto', 'forex', 'commodities']:
                continue
            for asset in data["users"][username][asset_type]:
                if data["users"][username][asset_type][asset]["is_active"]:
                    for strategy in data["users"][username][asset_type][asset]["strategies"]:
                        if data["users"][username][asset_type][asset]["strategies"][strategy].get("status") == "active":
                            if not alarms.get(asset):
                                alarms[asset] = {'count': 0}
                            else:
                                alarms[asset]['count'] += 1
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


def status_change(alarm_properties):
    with DATA_LOCK:
        old_status = alarm_properties["status"]
        if alarm_properties["status"] == "active":
            alarm_properties["status"] = "inactive"
        elif alarm_properties["status"] == "inactive":
            alarm_properties["status"] = "active"
        print(f"Alarm status is changed from {old_status} to {alarm_properties['status']}.")

def add_alarm(data, code, which_asset, username):
    alarm_type = input("Enter the type of alarm (Fixed Price, Period Extremum or Percentage Change) you want to add (-1 to go back): ")
    if alarm_type == "-1":
        return
    alarm_type = utils.correct_input_format(alarm_type)
    while alarm_type not in ["fixedprice","fixed","price", "periodextremum", "period", "extremum", "percentagechange", "percentage", "change", "%", "%change", "change%"]:
        print("Alarm type must be fixed price, period extremum or percentage change.")
        alarm_type = input("Enter the type of alarm (Fixed Price, Period Extremum or Percentage Change) you want to add (-1 to go back): ")
        if alarm_type == "-1":
            return
        alarm_type = utils.correct_input_format(alarm_type)

    with DATA_LOCK:
        key = utils.find_empty_key(data["users"][username][which_asset][code]["strategies"])

    if alarm_type in ["fixedprice", "fixed", "price"]:
        alarm_type = "fixed_price"
        with DATA_LOCK:
            currency = data["users"][username][which_asset][code]["currency"]
        currency_symbol = utils.get_currency(currency)
        value = input(f"Enter the fixed price in {currency_symbol} ({currency}) that will trigger the alarm (-1 to go back): ")
        value = float(utils.correct_choice_format(value))
        while value < 0:
            if value == -1:
                return
            print("Fixed price cannot be negative, please try again.")
            value = input(f"Enter the fixed price in {currency_symbol} ({currency}) that will trigger the alarm (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
        ticker = yf.Ticker(code)
        latest_price = ticker.fast_info['lastPrice']
        if latest_price > value:
            # when latest_price <= value
            # alarm will be triggered
            condition = "lower_than"
        else:
            # when latest_price >= value
            # alarm will be triggered
            condition = "greater_than"
        status = alarm_status_decider()
        with DATA_LOCK:
            data["users"][username][which_asset][code]["strategies"][key] = {
                "type": alarm_type,
                "condition": condition,
                "value": value,
                "status": status
            }
    elif alarm_type in ["periodextremum", "period", "extremum"]:
        alarm_type = "period_extremum"
        target = input("Enter the periodic target (minimum or maximum) that will trigger the alarm (-1 to go back): ")
        if target == "-1":
            return
        target = utils.correct_input_format(target)
        while target not in ["minimum", "maximum", "max", "min"]:
            print("Invalid target, please try again.")
            target = input("Enter the periodic target (minimum or maximum) that will trigger the alarm (-1 to go back): ")
            if target == "-1":
                return
            target = utils.correct_input_format(target)
        start_date = input("Enter the start date (YYYY-MM-DD) of the period (-1 to go back): ")
        while not utils.is_valid_date(start_date):
            if start_date == "-1":
                return
            print("Invalid date or format, please try again.")
            start_date = input("Enter the start date (YYYY-MM-DD) of the period (-1 to go back): ")
        status = alarm_status_decider()
        with DATA_LOCK:
            data["users"][username][which_asset][code]["strategies"][key] = {
                "type": alarm_type,
                "target": target,
                "start_date": start_date,
                "status": status
            }
    elif alarm_type in ["percentagechange", "percentage", "change", "%", "%change", "change%"]:
        alarm_type = "percentage_change"
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
        status = alarm_status_decider()
        ticker = yf.Ticker(code)
        base_price = ticker.fast_info["lastPrice"]
        with DATA_LOCK:
            data["users"][username][which_asset][code]["strategies"][key] = {
                "type": alarm_type,
                "direction": direction,
                "value": value,
                "base_price": base_price,
                "status": status
            }
    storage.save_temp(data)
    print("Alarm is successfully added.")
    time.sleep(2)

def key_input(data, which_asset, code, username, which_function):
    key = input(f"Enter the number in the table corresponding to the alarm you want to {which_function} (-1 to go back): ")
    with DATA_LOCK:
        length = len(data["users"][username][which_asset][code]["strategies"])
    while int(key) < 1 or int(key) > length:
        if key == "-1":
            return ""
        print("Invalid alarm number, please try again.")
        key = input(f"Enter the number in the table corresponding to the alarm you want to {which_function} (-1 to go back): ")
    return key

def print_alarm_properties(alarm_properties):
    print()
    for key in alarm_properties:
        if key == "condition":
            continue
        s = key.replace("_", " ")
        print(f"{s.title():<20}", end="")
    if alarm_properties["type"] == "percentage_change":
        print("\n" + "-" * 90)
    elif alarm_properties["type"] == "period_extremum":
        print("\n" + "-" * 72)
    elif alarm_properties["type"] == "fixed_price":
        print("\n" + "-" * 54)
    for val in alarm_properties.values():
        if val == "lower_than" or val == "greater_than":
            continue
        if isinstance(val, str):
            val = val.replace("_", " ")
            print(f"{val.title():<20}", end="")
        else:
            print(f"{val:<20.2f}", end="")
    print("\n")
    i = 1
    for key in alarm_properties:
        if key == "type" or key == "condition":
            continue
        s = key.replace("_", " ")
        print(f"[{i}] {s.title()}")
        i += 1
    print(f"[{i}] Back")
    return i

def edit_alarm(data, code, which_asset, username):
    the_key = key_input(data, which_asset, code, username, "edit")
    if the_key == "":
        return
    with DATA_LOCK:
        alarm_properties = data["users"][username][which_asset][code]["strategies"][the_key]
        alarm_type = alarm_properties["type"]
        length = print_alarm_properties(alarm_properties)

    choice = input(f"\nEnter the option (1-{length}) corresponding the setting you want to change: ")
    choice = int(utils.correct_choice_format(choice))
    if choice == length:
        return
    while choice > length or choice < 1:
        print("Invalid choice, please try again.")
        choice = input(f"Enter the option (1-{length}) corresponding the setting you want to change: ")
        choice = int(utils.correct_choice_format(choice))

    if alarm_type == "fixed_price":
        if choice == 1:
            value = input("Enter the new trigger value for the alarm (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("Value cannot be negative, please try again.")
                value = input("Enter the new trigger value for the alarm (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            with DATA_LOCK:
                old_value = alarm_properties["value"]
                alarm_properties["value"] = value
            ticker = yf.Ticker(code)
            last_price = ticker.fast_info['lastPrice']
            with DATA_LOCK:
                if last_price > value:
                    alarm_properties["condition"] = "lower_than"
                else:
                    alarm_properties["condition"] = "greater_than"
            if old_value != value:
                print(f"Trigger value of alarm is changed from {old_value} to {value}.")
            else:
                print(f"Trigger value is already set to {value}, nothing is changed.")
        elif choice == 2:
            status_change(alarm_properties)
    elif alarm_type == "period_extremum":
        if choice == 1:
            s1 = ""
            s2 = ""
            with DATA_LOCK:
                if alarm_properties["target"] == "max":
                    alarm_properties["target"] = "min"
                    s1 = "maximum"
                    s2 = "minimum"
                elif alarm_properties["target"] == "min":
                    alarm_properties["target"] = "max"
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
            with DATA_LOCK:
                old_date = alarm_properties["start_date"]
                alarm_properties["start_date"] = start_date
            if old_date != start_date:
                print(f"Start date is changed from {old_date} to {start_date}.")
            else:
                print(f"Start date is already set to {start_date}, nothing is changed.")
        elif choice == 3:
            status_change(alarm_properties)
    elif alarm_type == "percentage_change":
        if choice == 1:
            with DATA_LOCK:
                old_direction = alarm_properties["direction"]
                if alarm_properties["direction"] == "drop":
                    alarm_properties["direction"] = "rise"
                elif alarm_properties["direction"] == "rise":
                    alarm_properties["direction"] = "drop"
                print(f"Percentage change direction is changed from '{old_direction}' to '{alarm_properties['direction']}'.")
        elif choice == 2:
            value = input("Enter the new value of percentage change trigger (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("The value of percentage change trigger cannot be negative, please try again.")
                value = input("Enter the new value of percentage change trigger (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            with DATA_LOCK:
                old_value = alarm_properties["value"]
                alarm_properties["value"] = value
            if old_value != value:
                print(f"Value of percentage change trigger is changed from {old_value} to {value}.")
            else:
                print(f"Value of percentage change trigger is already set to {value}, nothing is changed.")
        elif choice == 3:
            value = input("Enter the new base price (reference point) for percentage change trigger (-1 to go back): ")
            value = float(utils.correct_choice_format(value))
            while value < 0:
                if value == -1:
                    return
                print("The value of base price cannot be negative, please try again.")
                value = input("Enter the new base price (reference point) for percentage change trigger (-1 to go back): ")
                value = float(utils.correct_choice_format(value))
            with DATA_LOCK:
                old_value = alarm_properties["value"]
                alarm_properties["base_price"] = value
            if old_value != value:
                print(f"Base price for percentage change trigger is changed from {old_value} to {value}.")
            else:
                print(f"Base price for percentage change trigger is already set to {value}, nothing is changed.")
        elif choice == 4:
            status_change(alarm_properties)
    storage.save_temp(data)
    print(f"Alarm {the_key} is edited successfully.")
    time.sleep(3)

def deactivate_all_alarms(data, code, which_asset, username):
    with DATA_LOCK:
        data["users"][username][which_asset][code]["is_active"] = False
        shortcut = data["users"][username][which_asset][code]["strategies"]
        for strategy in shortcut:
            shortcut[strategy]["status"] = "inactive"
    storage.save_temp(data)
    print(f"All alarms are deactivated.")
    time.sleep(2)

def delete_alarm(data, code, which_asset, username):
    key = key_input(data, which_asset, code, username,"delete")
    with DATA_LOCK:
        del data["users"][username][which_asset][code]["strategies"][key]
    storage.save_temp(data)
    print(f"Alarm {key} is deleted.")
    time.sleep(2)

def find_unit_price(info):
    unit_price = input("Enter the unit price (if you do not enter any price, the current price will be used) (-1 to go back): ")
    while unit_price != "" and float(unit_price) < 0:
        if unit_price == "-1":
            return 0
        print("Invalid unit price, please try again.")
        unit_price = input("Enter unit price (if you do not enter any price, the current price will be used) (-1 to go back): ")
    if unit_price == "":
        unit_price = info["lastPrice"]
    else:
        unit_price = float(unit_price)
    return unit_price

def edit_quantity(data, code, which_asset, username):
    with DATA_LOCK:
        quantity = data["users"][username][which_asset][code]["quantity"]
        total_cost = data["users"][username][which_asset][code]["total_cost"]
        currency = data["users"][username][which_asset][code]["currency"]
    currency_symbol = utils.get_currency(currency)
    print(f"\n--- Quantity: {quantity} | Total Cost: {total_cost} {currency_symbol}---\n")
    print(f"[1] Add (increase quantity)  new buy to {code}")
    print(f"[2] Sell (decrease quantity) from {code}")
    print(f"[3] Reset (re-enter quantity) of {code}")
    print("[4] Back")
    choice = input("\nEnter your choice (1-4): ")
    choice = int(utils.correct_choice_format(choice))
    while choice > 4 or choice < 1:
        print("Invalid choice, please try again.")
        choice = input("Enter your choice (1-4): ")
        choice = int(utils.correct_choice_format(choice))

    # immediate return to avoid copies and API requests
    if choice == 4:
        return

    ticker = yf.Ticker(code)
    info = ticker.fast_info
    if choice == 1:
        add_quantity = input(f"Enter how many {code} you purchased (-1 to go back): ")
        add_quantity = float(utils.correct_choice_format(add_quantity))
        while add_quantity < 0:
            if add_quantity == -1:
                return
            print("Amount of purchase cannot be negative, please try again.")
            add_quantity = input(f"Enter how many {code} you purchased (-1 to go back): ")
            add_quantity = float(utils.correct_choice_format(add_quantity))
        unit_price = find_unit_price(info)
        with DATA_LOCK:
            data["users"][username][which_asset][code]["total_cost"] += unit_price * add_quantity
            data["users"][username][which_asset][code]["quantity"] += add_quantity
    elif choice == 2:
        while True:
            sell_quantity = input(f"Enter how many {code} you sold (-1 to go back): ")
            sell_quantity = float(utils.correct_choice_format(sell_quantity))
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
        with DATA_LOCK:
            data["users"][username][which_asset][code]["total_cost"] -= avg_price * sell_quantity
            data["users"][username][which_asset][code]["quantity"] -= sell_quantity
        unit_price = find_unit_price(info)
        gain = (unit_price - avg_price) * sell_quantity
        if gain < 0:
            print(f"Loss from this sale is {gain:.2f} {currency_symbol}.")
        elif gain > 0:
            print(f"Profit from this sale is {gain:.2f} {currency_symbol}.")
        else:
            print("There is no gain or loss from this sale.")
    elif choice == 3:
        new_quantity = input(f"Enter the quantity of the {code} (-1 to go back): ")
        new_quantity = float(utils.correct_choice_format(new_quantity))
        while new_quantity < 0:
            if new_quantity == -1:
                return
            print("Quantity cannot be negative, please try again.")
            new_quantity = input(f"Enter the quantity of the {code} (-1 to go back): ")
            new_quantity = float(utils.correct_choice_format(new_quantity))
        if new_quantity > 0:
            new_total_cost = input(f"Enter the total cost of {new_quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): ")
            new_total_cost = float(utils.correct_choice_format(new_total_cost))
            while new_total_cost < 0:
                if new_total_cost == -1:
                    return
                print("Total cost cannot be negative, please try again.")
                new_total_cost = input(f"Enter the total cost of {new_quantity} {code} to you in {currency_symbol} ({currency}) (-1 to go back): ")
                new_total_cost = float(utils.correct_choice_format(new_total_cost))
        else:
            new_total_cost = 0
        with DATA_LOCK:
            data["users"][username][which_asset][code]["total_cost"] = new_total_cost
            data["users"][username][which_asset][code]["quantity"] = new_quantity
    storage.save_temp(data)
    with DATA_LOCK:
        print(f"Quantity is changed from {quantity} to {data['users'][username][which_asset][code]['quantity']}.")
        print(f"Total cost is changed from {total_cost} to {data['users'][username][which_asset][code]['total_cost']}")
    time.sleep(3)

def activate_all_alarms(data,code, which_asset, logged_user):
    with DATA_LOCK:
        data["users"][logged_user][which_asset][code]["is_active"] = True
        shortcut = data["users"][logged_user][which_asset][code]["strategies"]
        for strategy in shortcut:
            shortcut[strategy]["status"] = "active"
    storage.save_temp(data)
    print("All alarms is activated.")
    time.sleep(2)