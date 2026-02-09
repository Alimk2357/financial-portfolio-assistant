import sys
import src.alarms as alarms
import src.portfolio as portfolio
import src.analysis as analysis
import src.storage as storage
import src.auth as auth
import src.ui as ui
import src.utils as utils

def main():
    try:
        data = storage.load_data()
    except FileNotFoundError:
        print("data.json file cannot be opened.")
        data = {"users": {}}

    while True:
        utils.clear_screen()
        ui.print_title()
        ui.entrance(data)

        num = int(input("Enter your choice: "))
        while data.get("users") and (num > 4 or num < 1):
            print("Invalid choice, please try again.")
            num = int(input("Enter your choice (1-5): "))

        while not data.get("users") and (num > 2 or num < 1):
            print("Invalid choice, please try again.")
            num = int(input("Enter your choice (1-3): "))

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

        while logged_user != "":
            utils.clear_screen()
            ui.main_menu(logged_user, data)
            choice = int(input("Enter your choice (1-7): "))
            while choice > 7 or choice < 1:
                print("Invalid choice, please try again.")
                choice = int(input("Enter your choice (1-7): "))

            operation = ""
            while operation != "B":
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
                    ui.setting_menu(data, logged_user)
                elif choice == 6:
                    logged_user = ""
                    break
                elif choice == 7:
                    sys.exit(0)

                financial_assets = ui.transaction_management_menu(data, logged_user, which_asset)
                if financial_assets:
                    operation = input("Enter your operation (A or B or D or R) : ").upper()
                else:
                    operation = input("Enter your operation (A or B) : ").upper()

                while financial_assets and operation not in ["A", "[A]", "B", "[B]", "D", "[D]", "R", "[R]"]:
                    print("Invalid choice, please try again.")
                    operation = input("Enter your operation (A or B or D or R): ")

                while not financial_assets and operation not in ["A", "[A]", "B", "[B]"]:
                    print("Invalid choice, please try again.")
                    operation = input("Enter your operation (A or B): ")

                if operation == "B":
                    break

                code = ""
                if len(financial_assets) > 0 and operation in ["D", "[D]", "R", "[R]"]:
                    code = input("Enter the Ticker (code) of the financial asset you want to operate: ").upper()
                    while code not in financial_assets:
                        if code == "-1":
                            break
                        print(f"{code} is not in the portfolio of {logged_user}, please try again.")
                        code = input("Enter the Ticker (code) of the financial asset you want to operate: ").upper()
                    if code == "-1":
                        continue

                if operation in ["A", "[A]"]:
                    portfolio.add_financial_asset(data, which_asset, logged_user)
                elif operation in ["D", "[D]"]:
                    choice_detail = 0
                    while choice_detail != 7:
                        utils.clear_screen()
                        ui.detail_menu(financial_assets[code], code)
                        choice_detail = input("Enter your choice (1-7): ")
                        choice_detail = int(utils.correct_choice_format(choice_detail))
                        while choice_detail > 7 or choice_detail < 1:
                            print("Invalid choice, please try again.")
                            choice_detail = input("Enter your choice (1-7): ")
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
                            alarms.deactivate_all_alarms(data, code, which_asset, logged_user)
                        elif choice_detail == 6:
                            alarms.edit_quantity(data, code, which_asset, logged_user)
                elif operation in ["R", "[R]"]:
                   portfolio.remove_financial_asset(data, which_asset, logged_user, code)

if __name__ == "__main__":
    main()