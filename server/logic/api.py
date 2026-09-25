import os
import sys
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify


def _setup_paths():
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        if base not in sys.path:
            sys.path.insert(0, base)
        data_path = os.path.join(base, "data")
        shared = base
    else:
        current = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(current, "..", ".."))
        shared = os.path.join(root, "shared")
        data_path = os.path.join(root, "client", "data")
        if current not in sys.path:
            sys.path.insert(0, current)
        if shared not in sys.path:
            sys.path.insert(0, shared)

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
