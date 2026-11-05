import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT_DIR = os.path.join(ROOT_DIR, "client")
SERVER_DIR = os.path.join(ROOT_DIR, "server")
SHARED_DIR = os.path.join(ROOT_DIR, "shared")

for p in [CLIENT_DIR, os.path.join(CLIENT_DIR, "ui"), os.path.join(CLIENT_DIR, "logic"), SHARED_DIR, SERVER_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from data_loader import load_stations, resource_path
from specs_formatter import build_specs_html


def test_stations_load_successfully():
    stations = load_stations()
    assert isinstance(stations, list)
    assert len(stations) > 0
    # Test caching: subsequent call returns identical in-memory instance
    stations_cached = load_stations()
    assert stations is stations_cached
    print(f"Loaded {len(stations)} stations.")


def test_stations_schema():
    stations = load_stations()
    categories = {"radio", "satellite"}
    for st in stations:
        assert "id" in st and isinstance(st["id"], str) and st["id"]
        assert "name" in st and isinstance(st["name"], str) and st["name"]
        assert "category" in st and st["category"] in categories
        assert "specs" in st and isinstance(st["specs"], list)
        assert len(st["specs"]) > 0

        for sp in st["specs"]:
            assert "name" in sp
            assert "type" in sp
            assert "answer" in sp
            assert sp["type"] in {"number", "range", "choice", "text"}


def test_build_specs_html_for_all_stations():
    stations = load_stations()
    for st in stations:
        html = build_specs_html(st)
        assert isinstance(html, str)
        assert "<table" in html
        assert st["name"] in html or "Тактико-технические" in html
