"""
UI сервера — окно преподавателя.
Показывает:
- статус сервера (IP, порт)
- кнопку «Начать летучку»
- таблицу студентов (ФИО, группа, станция, время, оценка, статус)
- историю попыток по клику
"""
import os
import sys
import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor


def _get_paths():
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, "..", ".."))
    shared = os.path.join(root, "shared")
    client_data = os.path.join(root, "data")
    return root, shared, client_data


ROOT, SHARED, CLIENT_DATA = _get_paths()
sys.path.insert(0, SHARED)
sys.path.insert(0, os.path.join(ROOT, "server", "logic"))

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
    background: #F0F0F0;
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}
QScrollBar::handle:vertical {
    background: #6B8E7B;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #4A6B5A;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
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
    path = os.path.join(CLIENT_DATA, "stations.json")
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
                font-size: 15px;
                padding: 5px 10px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 6px;
                background-color: white;
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
                font-size: 15px;
                padding: 5px 10px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 6px;
                background-color: white;
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
                font-size: 15px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                background-color: #757575;
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                border: none;
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
                font-size: 14px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                gridline-color: #E0E0E0;
            }}
            QHeaderView::section {{
                background-color: {HEADER_COLOR};
                color: white;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
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
                font-size: 15px;
                background-color: #757575;
                color: white;
                border-radius: 8px;
                border: none;
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

        top = QHBoxLayout()

        title = QLabel("Сервер тренажёра")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 24px; font-weight: bold;"
        )
        top.addWidget(title)
        top.addStretch()

        self.ip_label = QLabel(
            f"IP: {self.server_ip}  |  Порт: {self.server_port}  |  "
            f"Broadcast: 5001"
        )
        self.ip_label.setStyleSheet(
            f"color: {ACCENT_COLOR}; font-size: 14px; font-weight: bold; "
            f"background-color: #E8F5E9; padding: 10px 15px; border-radius: 8px;"
        )
        top.addWidget(self.ip_label)

        layout.addLayout(top)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.start_btn = QPushButton("🚀  Начать летучку")
        self.start_btn.setMinimumHeight(52)
        self.start_btn.setMinimumWidth(220)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        self.start_btn.clicked.connect(self.start_quiz)
        controls.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🛑  Остановить летучку")
        self.stop_btn.setMinimumHeight(52)
        self.stop_btn.setMinimumWidth(220)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                background-color: {DANGER_COLOR};
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #7F1D1D; }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #777777;
            }}
        """)
        self.stop_btn.clicked.connect(self.stop_quiz)
        controls.addWidget(self.stop_btn)

        controls.addStretch()

        self.quiz_label = QLabel("Летучка не запущена")
        self.quiz_label.setStyleSheet(
            f"color: #6B7280; font-size: 15px; font-weight: bold;"
        )
        controls.addWidget(self.quiz_label)

        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "ФИО", "Группа", "Станция", "Время", "Оценка", "Статус"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 15px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                gridline-color: #E0E0E0;
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
            }}
            QHeaderView::section {{
                background-color: {HEADER_COLOR};
                color: white;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
                border: none;
            }}
            {SCROLLBAR_STYLE}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        self.stats_label = QLabel("Всего: 0   ✅ 0   🟡 0   ⛔ 0")
        self.stats_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 14px; font-weight: bold; padding: 5px;"
        )
        layout.addWidget(self.stats_label)

    def start_quiz(self):
        active = self.db.get_active_quiz()
        if active:
            QMessageBox.warning(
                self, "Летучка уже идёт",
                "Сначала остановите текущую летучку."
            )
            return

        dialog = StartQuizDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        choice = dialog.get_choice()
        topic = choice["topic"]
        station_id = choice["station_id"]
        station_name = choice["station_name"]

        if topic == "single" and not station_id:
            QMessageBox.warning(self, "Ошибка", "Не выбрана станция.")
            return

        if topic == "single":
            stations = _load_stations()
            station = next((s for s in stations if s["id"] == station_id), None)
            if station:
                q_count = _calculate_question_count(len(station["specs"]))
            else:
                q_count = QUIZ_MIN_QUESTIONS
        else:
            q_count = QUIZ_MIN_QUESTIONS

        self.db.create_quiz(topic, station_id, station_name, q_count)
        self.stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)

        topic_text = {
            "single": f"Одна станция: {station_name}",
            "radio": "Все радиорелейные",
            "satellite": "Все спутниковые",
            "all": "Все станции",
        }.get(topic, topic)

        self.quiz_label.setText(f"Летучка: {topic_text}")
        self.quiz_label.setStyleSheet(
            f"color: {ACCENT_COLOR}; font-size: 15px; font-weight: bold;"
        )

        self.refresh_students()

    def stop_quiz(self):
        active = self.db.get_active_quiz()
        if not active:
            return
        if QMessageBox.question(
            self, "Остановить летучку",
            "Все, кто не сдал, будут помечены как «Прервано». Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.db.stop_quiz(active["id"])
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.quiz_label.setText("Летучка не запущена")
        self.quiz_label.setStyleSheet(
            f"color: #6B7280; font-size: 15px; font-weight: bold;"
        )
        self.refresh_students()

    def refresh_students(self):
        active = self.db.get_active_quiz()
        if not active:
            self.table.setRowCount(0)
            self.stats_label.setText("Всего: 0   ✅ 0   🟡 0   ⛔ 0")
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            return

        self.db.check_timeouts(active["id"], STUDENT_TIMEOUT)
        students = self.db.get_all_students(active["id"])

        self.table.setRowCount(len(students))

        counter = {"finished": 0, "in_progress": 0, "interrupted": 0, "waiting": 0}

        for i, s in enumerate(students):
            status = s.get("status", "waiting")
            counter[status] = counter.get(status, 0) + 1

            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("fio", "")))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("group_name", "")))
            self.table.setItem(i, 3, QTableWidgetItem(s.get("station_name", "—")))

            duration = s.get("duration", 0)
            if duration > 0:
                mins = duration // 60
                secs = duration % 60
                time_text = f"{mins:02d}:{secs:02d}"
            else:
                time_text = "—"
            self.table.setItem(i, 4, QTableWidgetItem(time_text))

            percent = s.get("percent", 0)
            if status == "finished":
                grade_item = QTableWidgetItem(f"{percent:.1f}%")
                f = QFont()
                f.setBold(True)
                grade_item.setFont(f)
                grade_item.setForeground(QColor(
                    ACCENT_COLOR if percent >= GRADE_EXCELLENT
                    else (WARN_COLOR if percent >= GRADE_SATISFACTORY else DANGER_COLOR)
                ))
            else:
                grade_item = QTableWidgetItem("—")
            self.table.setItem(i, 5, grade_item)

            status_item = QTableWidgetItem(STATUS_LABELS.get(status, status))
            f2 = QFont()
            f2.setBold(True)
            status_item.setFont(f2)
            status_item.setForeground(QColor(STATUS_COLORS.get(status, TEXT_COLOR)))
            self.table.setItem(i, 6, status_item)

        total = len(students)
        self.stats_label.setText(
            f"Всего: {total}   "
            f"✅ Завершили: {counter['finished']}   "
            f"🟡 В процессе: {counter['in_progress'] + counter['waiting']}   "
            f"⛔ Прервано: {counter['interrupted']}"
        )

    def on_row_double_clicked(self, index):
        row = index.row()
        fio_item = self.table.item(row, 1)
        group_item = self.table.item(row, 2)
        if not fio_item or not group_item:
            return
        fio = fio_item.text()
        group_name = group_item.text()
        history = self.db.get_student_history(fio, group_name)
        if not history:
            QMessageBox.information(
                self, "История",
                f"У {fio} пока нет завершённых попыток."
            )
            return
        dialog = HistoryDialog(fio, group_name, history, self)
        dialog.exec_()

    def closeEvent(self, event):
        try:
            self.broadcaster.stop()
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass
        event.accept()