import bcrypt
import src.storage as storage
import time
from src.tracking import DATA_LOCK

def check_password(password, hashed_password):
    # both parameters are string, they must be converted into bytes
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def password_input(data,username, message):
    password = input(f"Enter{message}password (-1 to go back): ")
    if password == "-1":
        return False

    with DATA_LOCK:
        hashed_password = data["users"][username]["password"]
    counter = 1

    while not check_password(password, hashed_password):
        if password == "-1":
            return False
        print("Wrong password, please try again.")
        if counter % 4 == 0:
            print("Too many failed attempts, wait 30 seconds")
            time.sleep(30)
        password = input(f"Enter {message} password (-1 to go back): ")
        counter += 1
    return True

def login(data):
    while True:
        username = input("Enter username (-1 to go back): ")
        username = username.strip()
        if username == "-1":
            return ""
        with DATA_LOCK:
            is_in_users = username in data["users"]
        if " " in username:
            print("\nA username cannot contain space, please try again.")
            continue
        if not is_in_users:
            print(f"\n{username} does not exist, please try again.")
            continue
        break

    if password_input(data, username, " "):
        print("\nLogged in!")
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
    while True:
        username = input("Enter username (-1 to go back): ")
        username = username.strip()
        if username == "-1":
            return False
        with DATA_LOCK:
            is_in_users = username in data["users"]
        if username == "":
            print("\nA username cannot be blank, please try again.")
            continue
        if " " in username:
            print("\nA username cannot contain space, please try again.")
            continue
        if is_in_users:
            print(f"\n{username} already exists, please try with a different username.")
            continue
        break

    password = input("Enter password (-1 to go back): ")
    while not is_password_strong(password):
        if password == "-1":
            return ""
        print("\nWeak password. Password must contain at least")
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
    with DATA_LOCK:
        data["users"][username] = {
            "stocks": {},
            "crypto": {},
            "forex": {},
            "commodities": {},
            "last_checked": None,
            "notifications": {
                "desktop_notifications": True,
                "app_name": "Financial Portfolio Assistant",
                "timeout": 10
            },
            "password": hashed_password_decoded,
            "language": "en",
            "default_currency": "USD"
        }
    storage.save_temp(data)
    print(f"{username} successfully created.")
    time.sleep(1.5)
    return username

def delete_user(data):
    while True:
        user = input("Enter username to be deleted (-1 to go back): ")
        user = user.strip()
        if user == "-1":
            return ""
        with DATA_LOCK:
            is_in_users = user in data["users"]
        if " " in user:
            print("\nA username cannot contain space, please try again.")
            continue
        if not is_in_users:
            print(f"\n{user} does not exist, please try again.")
            continue
        break

    if password_input(data, user, " "):
        with DATA_LOCK:
            del data["users"][user]
        storage.save_temp(data)
        print(f"{user} successfully deleted.")
        time.sleep(1)
        return user
    else:
        return ""

def change_username(data, username):
    if password_input(data, username, " "):
        while True:
            new_username = input("Enter new username (-1 to go back): ")
            new_username = new_username.strip()
            if new_username == "-1":
                return False
            if new_username == "":
                print("\nA username cannot be blank, please try again.")
                continue
            if " " in new_username:
                print("\nA username cannot contain space, please try again.")
                continue
            if new_username in data["users"]:
                print(f"\n{new_username} already exists, please try with a different username.")
                continue
            break
        with DATA_LOCK:
            data["users"][new_username] = data["users"].pop(username)
        storage.save_temp(data)
        print(f"\nUsername successfully changed from {username} to {new_username}.")
        print("For your security and to apply the changes, please log in again with your new username.")
        print("Therefore, logging out!")
        time.sleep(5)
        return True
    else:
        return False

def change_password(data, username):
    if password_input(data, username, " current "):
        new_password = input("Enter new password (-1 to go back): ")
        while not is_password_strong(new_password):
            if new_password == "-1":
                return
            print("Weak password. Password must contain at least")
            print("- 6 characters")
            print("- 1 uppercase letter")
            print("- 1 lowercase letter")
            print("- 1 number")
            print("- 1 special character")
            new_password = input("\nEnter password (-1 to go back): ")
        new_password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_new_password = bcrypt.hashpw(new_password_bytes, salt)
        hashed_new_password_decoded = hashed_new_password.decode('utf-8')
        with DATA_LOCK:
            data["users"][username]["password"] = hashed_new_password_decoded
        storage.save_temp(data)
        print(f"Password successfully changed.")
        time.sleep(1.5)