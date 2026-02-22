import sys
import src.alarms as alarms
import src.portfolio as portfolio
import src.analysis as analysis
import src.storage as storage
import src.auth as auth
import src.ui as ui
import src.utils as utils
import time
import src.tracking as tracking
import threading



def main():
    try:
        data = storage.load_data()
    except FileNotFoundError:
        print("data.json file cannot be opened.")
        data = {"users": {}}

    while True:
        tracking.STOP_EVENT.clear()
        utils.clear_screen()
        ui.print_title()
        ui.entrance(data)

        num = input("\nEnter your choice: ")
        num = int(utils.correct_choice_format(num))
        while data.get("users") and (num > 4 or num < 1):
            print("Invalid choice, please try again.")
            num = input("Enter your choice (1-5): ")
            num = int(utils.correct_choice_format(num))

        while not data.get("users") and (num > 2 or num < 1):
            print("Invalid choice, please try again.")
            num = input("Enter your choice (1-3): ")
            num = int(utils.correct_choice_format(num))

        logged_user = ""
        if data.get("users"):
            if num == 1:
                logged_user = auth.login(data)
            elif num == 2:
                auth.create_user(data)
            elif num == 3:
                auth.delete_user(data)
            elif num == 4:
                break
        else:
            if num == 1:
                auth.create_user(data)
            elif num == 2:
                break

        if logged_user != "":
            print("\nLogin Successful!\n")
            alarm_tracker = threading.Thread(
                target = tracking.alarm_tracking,
                args = (data, logged_user),
                name = "Alarm Tracker",
                daemon = True
            )
            alarm_tracker.start()

        while logged_user != "":
            utils.clear_screen()
            ui.main_menu(logged_user, data)
            choice = input("Enter your choice (1-7): ")
            choice = int(utils.correct_choice_format(choice))
            while choice > 7 or choice < 1:
                print("Invalid choice, please try again.")
                choice = input("Enter your choice (1-7): ")
                choice = int(utils.correct_choice_format(choice))

            which_asset = ""
            if choice == 1:
                which_asset = "stocks"
            elif choice == 2:
                which_asset = "crypto"
            elif choice == 3:
                which_asset = "forex"
            elif choice == 4:
                which_asset = "commodities"
            elif choice == 5:
                while True:
                    utils.clear_screen()
                    ui.setting_menu()
                    choice_settings = input("\nEnter your choice (1-3) (-1 to go back): ")
                    choice_settings = int(utils.correct_choice_format(choice_settings))
                    while choice_settings < 1 or choice_settings > 3:
                        if choice_settings == -1:
                            break
                        print("\nInvalid choice, please try again.")
                        choice_settings = input("Enter your choice (1-3) (-1 to go back): ")
                        choice_settings = int(utils.correct_choice_format(choice_settings))

                    if choice_settings == -1:
                        break
                    elif choice_settings == 1:
                        utils.clear_screen()
                        ui.account_settings_menu()
                        choice_account_settings = input("\nEnter your choice (1-2) (-1 to go back): ")
                        choice_account_settings = int(utils.correct_choice_format(choice_account_settings))
                        while choice_account_settings < 1 or choice_account_settings > 2:
                            if choice_account_settings == -1:
                                break
                            print("\nInvalid choice, please try again.")
                            choice_account_settings = input("Enter your choice (1-2) (-1 to go back): ")
                            choice_account_settings = int(utils.correct_choice_format(choice_account_settings))

                        if choice_account_settings == 1:
                            is_username_changed = auth.change_username(data, logged_user)
                            if is_username_changed:
                                logged_user = ""
                                break
                        elif choice_account_settings == 2:
                            auth.change_password(data, logged_user)
                    elif choice_settings == 2:
                        utils.clear_screen()
                        ui.notification_settings_menu(data, logged_user)
                        choice_notification_settings = input("\nEnter your choice (1-3) (-1 to go back): ")
                        choice_notification_settings = int(utils.correct_choice_format(choice_notification_settings))
                        while choice_notification_settings < 1 or choice_notification_settings > 3:
                            if choice_notification_settings == -1:
                                break
                            print("\nInvalid choice, please try again.")
                            choice_notification_settings = input("\nEnter your choice (1-3) (-1 to go back): ")
                            choice_notification_settings = int(utils.correct_choice_format(choice_notification_settings))
                        if choice_notification_settings == 1:
                            with tracking.DATA_LOCK:
                                if data["users"][logged_user]["notifications"]["desktop_notifications"]:
                                    data["users"][logged_user]["notifications"]["desktop_notifications"] = False
                                    print("Notifications turned off.")
                                else:
                                    data["users"][logged_user]["notifications"]["desktop_notifications"] = True
                                    print("Notifications turned on.")
                            storage.save_temp(data)
                            time.sleep(1.5)
                        elif choice_notification_settings == 2:
                            with tracking.DATA_LOCK:
                                old_name = data["users"][logged_user]["notifications"]["app_name"]
                            print(f"\nApp's current name is {old_name}.")
                            print("This name appears in the 'app name' section when a notification arrives.")
                            new_name = input("Enter the new name of the app (-1 to go back): ")
                            new_name = new_name.strip()
                            while new_name == "" or new_name == "-1":
                                if new_name == "-1":
                                    break
                                print("App name cannot be blank, please try again.")
                                new_name = input("Enter the new name of the app (-1 to go back): ")
                                new_name = new_name.strip()
                            if new_name == "-1":
                                continue
                            with tracking.DATA_LOCK:
                                data["users"][logged_user]["notifications"]["app_name"] = new_name
                            storage.save_temp(data)
                            print(f"App's name changed from '{old_name}' to '{new_name}'.")
                            time.sleep(2)
                        elif choice_notification_settings == 3:
                            with tracking.DATA_LOCK:
                                old_duration = data["users"][logged_user]["notifications"]["timeout"]
                            print(f"\nCurrent notification duration is {old_duration}s.")
                            new_duration = input("Enter the new duration of the notifications in seconds (-1 to go back): ")
                            new_duration = float(utils.correct_choice_format(new_duration))
                            while new_duration < 0:
                                if new_duration == -1:
                                    break
                                print("\nDuration cannot be negative, please try again.")
                                new_duration = input("Enter the new duration of the notifications in seconds (-1 to go back): ")
                                new_duration = float(utils.correct_choice_format(new_duration))
                            if new_duration == -1:
                                continue
                            with tracking.DATA_LOCK:
                                data["users"][logged_user]["notifications"]["timeout"] = new_duration
                            storage.save_temp(data)
                            if new_duration > old_duration:
                                print(f"Notification duration is increased from {old_duration}s to {new_duration}s.")
                            elif new_duration < old_duration:
                                print(f"Notification duration is decreased from {old_duration}s to {new_duration}s.")
                            else:
                                print("Notification duration is not changed.")
                            time.sleep(2)
                    elif choice_settings == 3:
                        with tracking.DATA_LOCK:
                            old_currency = data["users"][logged_user]["default_currency"]
                        print(f"\nCurrent portfolio currency is {old_currency}.")
                        ISO_4217_CURRENCIES = {
                            "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
                            "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BOV", "BRL", "BSD", "BTN",
                            "BWP", "BYN", "BZD",
                            "CAD", "CDF", "CHE", "CHF", "CHW", "CLF", "CLP", "CNY", "COP", "COU", "CRC", "CUC", "CUP",
                            "CVE", "CZK",
                            "DJF", "DKK", "DOP", "DZD",
                            "EGP", "ERN", "ETB", "EUR",
                            "FJD", "FKP",
                            "GBP", "GEL", "GHS", "GIP", "GMD", "GNF", "GTQ", "GYD",
                            "HKD", "HNL", "HRK", "HTG", "HUF",
                            "IDR", "ILS", "INR", "IQD", "IRR", "ISK",
                            "JMD", "JOD", "JPY",
                            "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD", "KYD", "KZT",
                            "LAK", "LBP", "LKR", "LRD", "LSL", "LYD",
                            "MAD", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRU", "MUR", "MVR", "MWK", "MXN", "MXV",
                            "MYR", "MZN",
                            "NAD", "NGN", "NIO", "NOK", "NPR", "NZD",
                            "OMR",
                            "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG",
                            "QAR",
                            "RON", "RSD", "RUB", "RWF",
                            "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SLE", "SLL", "SOS", "SRD", "SSP", "STN",
                            "SVC", "SYP", "SZL",
                            "THB", "TJS", "TMT", "TND", "TOP", "TRY", "TTD", "TWD", "TZS",
                            "UAH", "UGX", "USD", "USN", "UYI", "UYU", "UYW", "UZS",
                            "VED", "VES", "VND", "VUV",
                            "WST",
                            "XAF", "XAG", "XAU", "XBA", "XBB", "XBC", "XBD", "XCD", "XDR", "XOF", "XPD", "XPF", "XPT",
                            "XSU", "XTS", "XUA", "XXX",
                            "YER",
                            "ZAR", "ZMW", "ZWL"
                        }
                        while True:
                            new_currency = input("Enter new currency (e.g. USD, TRY) (-1 to go back): ").upper()
                            new_currency = new_currency.replace(" ", "")
                            if new_currency == "-1":
                                break
                            if new_currency == "":
                                print("Currency cannot be blank, please try again.")
                                continue
                            if new_currency not in ISO_4217_CURRENCIES:
                                print(f"Invalid currency, {new_currency} does not exist. Please try again.")
                                continue
                            break
                        if new_currency == "-1":
                            continue
                        with tracking.DATA_LOCK:
                            data["users"][logged_user]["default_currency"] = new_currency
                        storage.save_temp(data)
                        print(f"Portfolio currency is changed from {old_currency} to {new_currency}.")
                        time.sleep(2)
                continue
            elif choice == 6:
                print(f"Logging out!")
                time.sleep(1.5)
                tracking.STOP_EVENT.set()
                break
            elif choice == 7:
                sys.exit(0)

            while True:
                utils.clear_screen()
                financial_assets = ui.transaction_management_menu(data, logged_user, which_asset)
                with tracking.DATA_LOCK:
                    if financial_assets:
                        operation = input("\nEnter your operation (A or B or D or R) : ").upper()
                    else:
                        operation = input("\nEnter your operation (A or B) : ").upper()
                    length = len(financial_assets)
                operation = operation.replace(" ", "")
                while length != 0 and operation not in ["A", "[A]", "B", "[B]", "D", "[D]", "R", "[R]"]:
                    print("\nInvalid choice, please try again.")
                    operation = input("Enter your operation (A or B or D or R): ").upper()
                    operation = operation.replace(" ", "")

                while length == 0 and operation not in ["A", "[A]", "B", "[B]"]:
                    print("\nInvalid choice, please try again.")
                    operation = input("Enter your operation (A or B): ").upper()
                    operation = operation.replace(" ", "")

                if operation == "B":
                    break

                code = ""
                if length > 0 and operation in ["D", "[D]", "R", "[R]"]:
                    code = input("Enter the Ticker (code) of the financial asset you want to operate (-1 to go back): ").upper()
                    code = code.replace(" ", "")
                    with tracking.DATA_LOCK:
                        code_in_assets = code in financial_assets
                    while not code_in_assets:
                        if code == "-1":
                            break
                        print(f"\n{code} is not in the portfolio of {logged_user}, please try again.")
                        code = input("Enter the Ticker (code) of the financial asset you want to operate (-1 to go back): ").upper()
                        code = code.replace(" ", "")
                        with tracking.DATA_LOCK:
                            code_in_assets = code in financial_assets
                    if code == "-1":
                        continue

                if operation in ["A", "[A]"]:
                    portfolio.add_financial_asset(data, which_asset, logged_user)
                elif operation in ["D", "[D]"]:
                    choice_detail = 0
                    while choice_detail != 8:
                        utils.clear_screen()
                        with tracking.DATA_LOCK:
                            financial_asset = financial_assets[code]
                        ui.detail_menu(financial_asset, code)
                        choice_detail = input("\nEnter your choice (1-8): ")
                        choice_detail = int(utils.correct_choice_format(choice_detail))
                        while choice_detail > 8 or choice_detail < 1:
                            print("\nInvalid choice, please try again.")
                            choice_detail = input("Enter your choice (1-8): ")
                            choice_detail = int(utils.correct_choice_format(choice_detail))

                        if choice_detail == 1:
                            analysis.analysis_report(data, which_asset, logged_user, code)
                        elif choice_detail == 2:
                            alarms.add_alarm(data, code, which_asset, logged_user)
                        elif choice_detail == 3:
                            alarms.edit_alarm(data, code, which_asset, logged_user)
                        elif choice_detail == 4:
                            alarms.delete_alarm(data, code, which_asset, logged_user)
                        elif choice_detail == 5:
                            alarms.activate_all_alarms(data, code, which_asset, logged_user)
                        elif choice_detail == 6:
                            alarms.deactivate_all_alarms(data, code, which_asset, logged_user)
                        elif choice_detail == 7:
                            alarms.edit_quantity(data, code, which_asset, logged_user)
                elif operation in ["R", "[R]"]:
                   portfolio.remove_financial_asset(data, which_asset, logged_user, code)

if __name__ == "__main__":
    main()