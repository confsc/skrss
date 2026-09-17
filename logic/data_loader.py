import json
import os
import sys


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_stations():
    path = resource_path(os.path.join("data", "stations.json"))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
