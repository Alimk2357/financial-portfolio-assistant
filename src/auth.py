import bcrypt
import src.storage as storage
import time


def check_password(password, hashed_password):
    # both parameters are string, they must be converted into bytes
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def password_input(data,username):
    password = input("Enter password (-1 to go back): ")
    if password == "-1":
        return False

    hashed_password = data["users"][username]["password"]
    counter = 1

    while not check_password(password, hashed_password):
        if password == "-1":
            return False
        print("Invalid password, please try again.")
        if counter % 4 == 0:
            print("Too many failed attempts, wait 30 seconds")
            time.sleep(30)
        password = input("Enter password (-1 to go back): ")
        counter += 1
    return True

def login(data):
    username = input("Enter username (-1 to go back): ")
    while not data["users"].get(username):
        if username == "-1":
            return ""
        print(f"{username} does not exist. Please try again.")
        username = input("Enter username (-1 to go back): ")

    if password_input(data, username):
        print("Logged in!")
        time.sleep(1)
        return username
    else:
        return ""

def is_password_strong(password):
    # at least 6 characters
    # Uppercase >= 1
    # Lowercase >= 1
    # Number >= 1
    # special characters >= 1
    # no consecutive characters
    if len(password) < 6:
        return False

    """
    0: uppercase letters
    1: lowercase letters
    2: numbers
    3: special characters
    """

    freq = [0] * 4
    special_char = {'!', '~', '@', '#', '$', '%', '^', '&',
                    '*', '(', ')', '_', '-', '+', '=', '[', ']', '{', '}', ';', ':',
                    '\'', '"', ',', '.', '<', '>', '?', '/', '|', '\\'}

    for ch in password:
        if ch.isupper():
            freq[0] += 1
        elif ch.islower():
            freq[1] += 1
        elif ch.isdigit():
            freq[2] += 1
        elif ch in special_char:
            freq[3] += 1

    for i in range(0, len(password) - 2):
        condition1 = password[i] == password[i + 1] and password[i + 1] == password[i + 2]
        condition2 = ord(password[i]) + 1 == ord(password[i + 1]) and ord(password[i + 1]) + 1 == ord(password[i + 2])
        if condition1 or condition2:
            return False

    for i in range(0, 4):
        if freq[i] < 1:
            return False

    return True


def create_user(data):
    username = input("Enter username (-1 to go back): ")

    while username == "" or username == "-1":
        if username == "-1":
            return ""
        print("Username cannot be empty.")
        username = input("Enter username (-1 to go back): ")

    password = input("Enter password (-1 to go back): ")
    while not is_password_strong(password):
        if password == "-1":
            return ""
        print("Weak password. Password must contain at least")
        print("- 6 characters")
        print("- 1 uppercase letter")
        print("- 1 lowercase letter")
        print("- 1 number")
        print("- 1 special character")
        password = input("\nEnter password (-1 to go back): ")

    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    hashed_password_decoded = hashed_password.decode('utf-8')
    temp = data
    temp["users"][username] = {
        "stocks": {},
        "crypto": {},
        "forex": {},
        "commodities": {},
        "password": hashed_password_decoded,
        "language": "en",
        "default_currency": "USD"
    }
    storage.save_temp(temp)
    print(f"{username} successfully created.")
    time.sleep(1)
    return username


def delete_user(data):
    user = input("Enter username (-1 to go back): ")
    if user == "-1":
        return ""

    while not data["users"].get(user):
        if user == "-1":
            return ""
        print("User not found. Please try again.")
        user = input("Enter username (-1 to go back): ")

    if password_input(data, user):
        temp = data
        del temp["users"][user]
        storage.save_temp(temp)
        print(f"{user} successfully deleted.")
        time.sleep(1)
        return user
    else:
        return ""
