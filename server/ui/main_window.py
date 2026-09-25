import os
import sys
import json

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor


def _setup_paths():
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        if base not in sys.path:
            sys.path.insert(0, base)
        data_path = os.path.join(base, "data")
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
    STUDENT_TIMEOUT, QUIZ_MIN_QUESTIONS, QUIZ_MAX_QUESTIONS,
    QUIZ_PERCENT, SCORE_PER_QUESTION,
    GRADE_EXCELLENT, GRADE_GOOD, GRADE_SATISFACTORY,
)
from database import Database  # noqa: E402
from broadcast import Broadcaster  # noqa: E402
