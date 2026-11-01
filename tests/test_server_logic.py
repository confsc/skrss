import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SERVER_DIR = os.path.join(ROOT_DIR, "server")
SHARED_DIR = os.path.join(ROOT_DIR, "shared")

for p in [SERVER_DIR, os.path.join(SERVER_DIR, "logic"), SHARED_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from database import Database
from server_api import create_app


def test_database_initialization_and_tables():
    db = Database(":memory:")
    cur = db.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    assert "quiz_sessions" in tables
    assert "students" in tables
    assert "attempts" in tables
    assert "connected_students" in tables


def test_database_student_connection_and_heartbeat():
    db = Database(":memory:")
    # Connect student
    db.register_connection("Иванов И.И.", "УВ-21", "192.168.1.10")
    students = db.get_connected_students()
    assert len(students) == 1
    assert students[0]["fio"] == "Иванов И.И."
    assert students[0]["group_name"] == "УВ-21"

    # Disconnect
    db.remove_connection("Иванов И.И.", "УВ-21")
    students_after = db.get_connected_students()
    assert len(students_after) == 0


def test_database_record_attempt():
    db = Database(":memory:")
    db.save_attempt(
        fio="Петров П.П.",
        group_name="УВ-22",
        station_id="r419mp02",
        station_name="Р-419МП-02",
        score=9.5,
        percent=95.0,
        correct_count=9,
        question_count=10,
        grade=5,
        duration=120
    )
    attempts = db.get_all_attempts()
    assert len(attempts) == 1
    assert attempts[0]["fio"] == "Петров П.П."
    assert attempts[0]["grade"] == 5
    assert attempts[0]["percent"] == 95.0


def test_server_api_ping_and_register():
    app, db = create_app()
    client = app.test_client()

    # Ping endpoint
    res = client.get("/api/ping")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["server"] == "RRS_TRAINER"

    # Register student endpoint
    res = client.post("/api/register", json={"fio": "Сидоров С.С.", "group": "УВ-23"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "connection_id" in data

    # Check connected students endpoint
    res = client.get("/api/connected")
    assert res.status_code == 200
    connected_list = res.get_json().get("students", [])
    assert any(s["fio"] == "Сидоров С.С." for s in connected_list)
