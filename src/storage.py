import json
import os
import stat
from pathlib import Path


def create_data():
    with open("data.json", "w", encoding="utf-8") as file:
        data = {"users": {}}
        json.dump(data, file, indent=4)
        os.chmod("data.json", stat.S_IREAD)
    return data


def load_data():
    data = {}
    if not os.path.exists("data.json") or os.path.getsize("data.json") == 0:
        data = create_data()
    else:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    return data


def save_temp(temp):
    with open("temp.json", "w", encoding="utf-8") as temp_file:
        json.dump(temp, temp_file, indent=4)
        # to guarantee atomic write
        temp_file.flush()
        os.fsync(temp_file.fileno())
        # to guarantee atomic write

    os.chmod("temp.json", stat.S_IREAD)

    try:
        os.replace("temp.json", "data.json")
    except OSError:
        print(f"Error: {OSError}")
        if os.path.exists("temp.json"):
            os.remove("temp.json")



"""
def load_config():
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    return config
"""
