"""
Flask API для клиентов.
"""
import os
import sys
import time
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify


def _setup_paths():
    if hasattr(sys, "_MEIPASS"):
        shared = os.path.join(sys._MEIPASS, "shared")
        server_logic = os.path.join(sys._MEIPASS, "server", "logic")
        data_path = os.path.join(sys._MEIPASS, "data")
        if not os.path.exists(server_logic):
            server_logic = os.path.join(sys._MEIPASS, "logic")
    else:
        current = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(current, "..", ".."))
        shared = os.path.join(root, "shared")
        server_logic = os.path.join(root, "server", "logic")
        data_path = os.path.join(root, "client", "data")

    for p in [shared, server_logic]:
        if p not in sys.path:
            sys.path.insert(0, p)

    return data_path


DATA_PATH = _setup_paths()

from config import (  # noqa: E402
    API_START, API_FINISH, API_HEARTBEAT,
    API_RESULTS, API_STUDENTS, API_PING,
    API_QUIZ_INFO, API_STOP_QUIZ,
    STUDENT_TIMEOUT, QUIZ_MIN_QUESTIONS, QUIZ_MAX_QUESTIONS,
    QUIZ_PERCENT, SCORE_PER_QUESTION,
)
from database import Database  # noqa: E402


def _load_stations():
    path = os.path.join(DATA_PATH, "stations.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _calculate_question_count(total):
    calc = round(QUIZ_PERCENT * total)
    count = max(QUIZ_MIN_QUESTIONS, min(QUIZ_MAX_QUESTIONS, calc))
    if count > total:
        count = total
    return count


def create_app():
    app = Flask(__name__)
    db = Database()

    @app.route(API_PING, methods=["GET"])
    def ping():
        return jsonify({"status": "ok", "server": "RRS_TRAINER"})

    @app.route(API_QUIZ_INFO, methods=["GET"])
    def quiz_info():
        quiz = db.get_active_quiz()
        if not quiz:
            return jsonify({"active": False})
        return jsonify({
            "active": True,
            "quiz_id": quiz["id"],
            "topic": quiz["topic"],
            "station_id": quiz["station_id"],
            "station_name": quiz["station_name"],
            "question_count": quiz["question_count"],
        })

    @app.route(API_START, methods=["POST"])
    def start_quiz():
        data = request.get_json(force=True, silent=True) or {}
        fio = (data.get("fio") or "").strip()
        group_name = (data.get("group") or "").strip()

        if not fio or not group_name:
            return jsonify({"status": "error", "message": "ФИО и группа обязательны"}), 400

        quiz = db.get_active_quiz()
        if not quiz:
            return jsonify({"status": "error", "message": "Летучка не запущена"}), 400

        existing = db.find_student(quiz["id"], fio, group_name)
        if existing and existing["status"] == "finished":
            return jsonify({
                "status": "error",
                "message": "Вы уже сдали",
            }), 409

        stations = _load_stations()
        topic = quiz["topic"]

        if topic == "single":
            station = next((s for s in stations if s["id"] == quiz["station_id"]), None)
            if not station:
                return jsonify({"status": "error", "message": "Станция не найдена"}), 400
        elif topic == "radio":
            pool = [s for s in stations if s["category"] == "radio"]
            station = random.choice(pool)
        elif topic == "satellite":
            pool = [s for s in stations if s["category"] == "satellite"]
            station = random.choice(pool)
        else:
            station = random.choice(stations)

        total_specs = len(station["specs"])
        question_count = _calculate_question_count(total_specs)
        time_limit = question_count * SCORE_PER_QUESTION

        specs_pool = list(station["specs"])
        random.shuffle(specs_pool)
        selected_specs = specs_pool[:question_count]

        prepared_specs = []
        for spec in selected_specs:
            item = {
                "name": spec["name"],
                "type": spec.get("type", "text"),
                "answer": spec["answer"],
            }
            if spec.get("unit"):
                item["unit"] = spec["unit"]
            if spec.get("options"):
                item["options"] = spec["options"]
            if spec.get("tolerance"):
                item["tolerance"] = spec["tolerance"]
            if spec.get("weight"):
                item["weight"] = spec["weight"]
            prepared_specs.append(item)

        if existing and existing["status"] in ("waiting", "in_progress"):
            student_id = existing["id"]
        else:
            student_id = db.add_student(quiz["id"], fio, group_name)

        db.update_student_start(
            student_id,
            station["id"],
            station["name"],
            question_count,
        )

        return jsonify({
            "status": "ok",
            "student_id": student_id,
            "quiz_id": quiz["id"],
            "station_id": station["id"],
            "station_name": station["name"],
            "time_limit": time_limit,
            "question_count": question_count,
            "specs": prepared_specs,
        })

    @app.route(API_FINISH, methods=["POST"])
    def finish_quiz():
        data = request.get_json(force=True, silent=True) or {}
        student_id = data.get("student_id")
        correct_count = int(data.get("correct_count", 0))
        score = float(data.get("score", 0))
        percent = float(data.get("percent", 0))
        duration = int(data.get("duration", 0))

        if not student_id:
            return jsonify({"status": "error", "message": "student_id обязателен"}), 400

        cur = db.conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"status": "error", "message": "Студент не найден"}), 404

        student = dict(row)

        db.update_student_finish(
            student_id,
            correct_count,
            score,
            percent,
            duration,
        )
        db.save_attempt(
            student["fio"],
            student["group_name"],
            student["station_id"],
            student["station_name"],
            score,
            percent,
            correct_count,
            student["question_count"],
            duration,
        )

        return jsonify({"status": "ok"})

    @app.route(API_HEARTBEAT, methods=["POST"])
    def heartbeat():
        data = request.get_json(force=True, silent=True) or {}
        student_id = data.get("student_id")
        if not student_id:
            return jsonify({"status": "error"}), 400
        db.update_heartbeat(student_id)
        return jsonify({"status": "ok"})

    @app.route(API_STUDENTS, methods=["GET"])
    def students():
        quiz = db.get_active_quiz()
        if not quiz:
            return jsonify({"students": [], "active": False})
        db.check_timeouts(quiz["id"], STUDENT_TIMEOUT)
        return jsonify({
            "active": True,
            "quiz": quiz,
            "students": db.get_all_students(quiz["id"]),
        })

    @app.route(API_RESULTS, methods=["GET"])
    def results():
        return jsonify({"attempts": db.get_all_attempts()})

    @app.route(API_STOP_QUIZ, methods=["POST"])
    def stop_quiz():
        quiz = db.get_active_quiz()
        if not quiz:
            return jsonify({"status": "error", "message": "Нет активной летучки"}), 400
        db.stop_quiz(quiz["id"])
        return jsonify({"status": "ok"})

    return app, db


if __name__ == "__main__":
    app, _ = create_app()
    print("Запуск API...")
    app.run(host="0.0.0.0", port=5000, debug=False)