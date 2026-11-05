import json
import os
import sys

_stations_cache = None


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def load_stations():
    """Загружает список станций из JSON. Результат кэшируется."""
    global _stations_cache
    if _stations_cache is not None:
        return _stations_cache
    path = resource_path(os.path.join("data", "stations.json"))
    with open(path, "r", encoding="utf-8") as f:
        _stations_cache = json.load(f)
    return _stations_cache
