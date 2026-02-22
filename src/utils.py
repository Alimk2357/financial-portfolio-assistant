import os
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_currency(currency):
    currency_symbols = {
        "TRY": "₺",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "XAU": "Ons",
    }
    return currency_symbols.get(currency, currency)

def correct_input_format(input_str):
    corrected_str = ""
    for ch in input_str:
        if ch.isalpha():
            corrected_str += ch.lower()
    return corrected_str

def correct_choice_format(choice):
    choice = choice.replace(" ", "")
    if choice == "":
        return "-27"
    elif choice in ["[1]", "[2]", "[3]", "[4]", "[5]", "[6]", "[7]", "[8]", "[9]"]:
        return choice[1]
    else:
        s = ""
        for i in range(0,len(choice)):
            if choice[i].isdigit() or (choice[i] == '.' and choice[i-1].isdigit() and choice[i+1].isdigit()) or choice[i] == "-":
                s += choice[i]
        return s


def find_empty_key(strategies):
    i = 1
    while f"{i}" in strategies:
        i += 1
    return f"{i}"

def is_valid_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False
