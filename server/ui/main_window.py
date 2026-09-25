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
    STUDENT_TIMEOUT,
    QUIZ_MIN_QUESTIONS, QUIZ_MAX_QUESTIONS, QUIZ_PERCENT,
    SCORE_PER_QUESTION,
    GRADE_EXCELLENT, GRADE_GOOD, GRADE_SATISFACTORY,
)
from database import Database  # noqa: E402
from broadcast import Broadcaster  # noqa: E402


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"
DANGER_COLOR = "#991B1B"
WARN_COLOR = "#B45309"

SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background: #F0F0F0; width: 14px; margin: 0px;
    border-radius: 7px;
}
QScrollBar::handle:vertical {
    background: #6B8E7B; min-height: 30px;
    border-radius: 7px; margin: 2px;
}
QScrollBar::handle:vertical:hover { background: #4A6B5A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""

STATUS_LABELS = {
    "waiting": "Ожидает",
    "in_progress": "В процессе",
    "finished": "Завершил",
    "interrupted": "Прервано",
}

STATUS_COLORS = {
    "waiting": "#6B7280",
    "in_progress": WARN_COLOR,
    "finished": ACCENT_COLOR,
    "interrupted": DANGER_COLOR,
}


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


class StartQuizDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Начать летучку")
        self.setFixedSize(520, 320)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Выберите тему летучки")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        layout.addWidget(QLabel("Тема:"))

        self.topic_combo = QComboBox()
        self.topic_combo.addItem("Одна станция", "single")
        self.topic_combo.addItem("Все радиорелейные", "radio")
        self.topic_combo.addItem("Все спутниковые", "satellite")
        self.topic_combo.addItem("Все станции", "all")
        self.topic_combo.setMinimumHeight(40)
        self.topic_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 15px; padding: 5px 10px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 6px; background-color: white;
            }}
        """)
        self.topic_combo.currentIndexChanged.connect(self._on_topic_changed)
        layout.addWidget(self.topic_combo)

        self.station_label = QLabel("Станция:")
        layout.addWidget(self.station_label)

        self.station_combo = QComboBox()
        self.station_combo.setMinimumHeight(40)
        self.station_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 15px; padding: 5px 10px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 6px; background-color: white;
            }}
        """)
        layout.addWidget(self.station_combo)

        try:
            self.stations = _load_stations()
        except Exception:
            self.stations = []

        for s in self.stations:
            self.station_combo.addItem(s["name"], s["id"])

        self._on_topic_changed()

        layout.addStretch()

        btns = QDialogButtonBox()
        ok_btn = btns.addButton("Начать", QDialogButtonBox.AcceptRole)
        cancel_btn = btns.addButton("Отмена", QDialogButtonBox.RejectRole)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 15px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 8px; padding: 8px 20px; border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px; background-color: #757575;
                color: white; border-radius: 8px;
                padding: 8px 20px; border: none;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_topic_changed(self):
        topic = self.topic_combo.currentData()
        is_single = (topic == "single")
        self.station_label.setVisible(is_single)
        self.station_combo.setVisible(is_single)

    def get_choice(self):
        topic = self.topic_combo.currentData()
        station_id = None
        station_name = None
        if topic == "single":
            station_id = self.station_combo.currentData()
            station_name = self.station_combo.currentText()
        return {
            "topic": topic,
            "station_id": station_id,
            "station_name": station_name,
        }


class HistoryDialog(QDialog):

    def __init__(self, fio, group_name, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"История: {fio} ({group_name})")
        self.resize(750, 500)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"История попыток: {fio}")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 18px; font-weight: bold;"
        )
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "#", "Дата", "Станция", "Правильных", "Оценка", "Время"
        ])
        table.setRowCount(len(history))
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 14px; background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px; gridline-color: #E0E0E0;
            }}
            QHeaderView::section {{
                background-color: {HEADER_COLOR}; color: white;
                padding: 8px; font-size: 14px;
                font-weight: bold; border: none;
            }}
            {SCROLLBAR_STYLE}
        """)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, attempt in enumerate(history):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem(attempt.get("finished_at", "")))
            table.setItem(i, 2, QTableWidgetItem(attempt.get("station_name", "")))
            table.setItem(
                i, 3,
                QTableWidgetItem(
                    f"{attempt.get('correct_count', 0)} / "
                    f"{attempt.get('question_count', 0)}"
                )
            )
            percent = attempt.get("percent", 0)
            grade_item = QTableWidgetItem(f"{percent:.1f}%")
            grade_item.setForeground(QColor(
                ACCENT_COLOR if percent >= GRADE_EXCELLENT
                else (WARN_COLOR if percent >= GRADE_SATISFACTORY else DANGER_COLOR)
            ))
            f = QFont()
            f.setBold(True)
            grade_item.setFont(f)
            table.setItem(i, 4, grade_item)

            duration = attempt.get("duration", 0)
            mins = duration // 60
            secs = duration % 60
            table.setItem(i, 5, QTableWidgetItem(f"{mins:02d}:{secs:02d}"))

        layout.addWidget(table)

        close_btn = QPushButton("Закрыть")
        close_btn.setMinimumHeight(42)
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px; background-color: #757575;
                color: white; border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class ServerWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервер тренажёра — Преподаватель")
        self.resize(1300, 850)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.db = Database()
        self.broadcaster = Broadcaster()
        self.broadcaster.start()

        info = self.broadcaster.get_info()
        self.server_ip = info["ip"]
        self.server_port = info["port"]

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_students)
        self.timer.start(2000)

        self.refresh_students()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top
