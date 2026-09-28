import os
import sys
import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QSizePolicy, QSplitter, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea,
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
    STUDENT_TIMEOUT, CONNECTION_TIMEOUT,
    QUIZ_MIN_QUESTIONS, QUIZ_MAX_QUESTIONS, QUIZ_PERCENT,
    SCORE_PER_QUESTION,
    GRADE_5, GRADE_4, GRADE_3,
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
GRAY_COLOR = "#6B7280"
YELLOW_BG = "#FFF9C4"
ORANGE_BG = "#FFE0B2"
RED_BG = "#FFCDD2"

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
    "waiting": GRAY_COLOR,
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


def _grade_color(grade):
    if grade == 5:
        return ACCENT_COLOR
    if grade == 4:
        return "#388E3C"
    if grade == 3:
        return WARN_COLOR
    return DANGER_COLOR


def _fmt_time(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


class StartQuizDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Начать контроль")
        self.setMinimumSize(620, 720)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        title = QLabel("Выберите тему контроля")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        layout.addWidget(QLabel("Тема:"))

        self.topic_combo = QComboBox()
        self.topic_combo.addItem("Несколько станций (случайно)", "multi")
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

        self.stations_label = QLabel("Выберите станции (галочками):")
        layout.addWidget(self.stations_label)

        self.select_all_btn = QPushButton("Выбрать все / Снять все")
        self.select_all_btn.setMinimumHeight(36)
        self.select_all_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 13px;
                background-color: #757575;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #616161; }}
        """)
        self.select_all_btn.clicked.connect(self._toggle_all)
        layout.addWidget(self.select_all_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                background-color: white;
            }}
            {SCROLLBAR_STYLE}
        """)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                font-size: 14px;
                background-color: white;
                border: none;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
            }}
        """)

        try:
            self.stations = _load_stations()
        except Exception:
            self.stations = []

        for s in self.stations:
            item = QListWidgetItem(s["name"])
            item.setData(Qt.UserRole, s["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll, 1)

        self.hint = QLabel(
            "Каждому курсанту будет выдана случайная станция из выбранных."
        )
        self.hint.setStyleSheet(
            f"color: {GRAY_COLOR}; font-size: 12px; padding: 4px;"
        )
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

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

        self._on_topic_changed()

    def _on_topic_changed(self):
        topic = self.topic_combo.currentData()
        is_multi = (topic == "multi")
        self.stations_label.setVisible(is_multi)
        self.select_all_btn.setVisible(is_multi)
        self.scroll.setVisible(is_multi)
        self.hint.setVisible(is_multi)

    def _toggle_all(self):
        any_unchecked = False
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Unchecked:
                any_unchecked = True
                break

        new_state = Qt.Checked if any_unchecked else Qt.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(new_state)

    def _get_selected_ids(self):
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                result.append(item.data(Qt.UserRole))
        return result

    def get_choice(self):
        topic = self.topic_combo.currentData()
        station_ids = []
        if topic == "multi":
            station_ids = self._get_selected_ids()
        return {
            "topic": topic,
            "station_id": None,
            "station_name": None,
            "station_ids": station_ids,
        }


class HistoryDialog(QDialog):

    def __init__(self, fio, group_name, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"История: {fio} ({group_name})")
        self.resize(800, 500)
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
            grade = attempt.get("grade", 0)
            grade_item = QTableWidgetItem(str(grade) if grade else "—")
            f = QFont()
            f.setBold(True)
            grade_item.setFont(f)
            grade_item.setForeground(QColor(_grade_color(grade)))
            table.setItem(i, 4, grade_item)

            duration = attempt.get("duration", 0)
            table.setItem(i, 5, QTableWidgetItem(_fmt_time(duration)))

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
        self.resize(1400, 900)
        self.setMinimumSize(1100, 650)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.db = Database()
        self.broadcaster = Broadcaster()
        self.broadcaster.start()

        info = self.broadcaster.get_info()
        self.server_ip = info["ip"]
        self.server_port = info["port"]

        self.filter_text = ""

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(1000)

        self.refresh_all()

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

        self.start_btn = QPushButton("🚀  Начать контроль")
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

        self.stop_btn = QPushButton("🛑  Остановить контроль")
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
            QPushButton:disabled {{ background-color: #CCCCCC; color: #777777; }}
        """)
        self.stop_btn.clicked.connect(self.stop_quiz)
        controls.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🧹  Очистить подключённых")
        self.clear_btn.setMinimumHeight(52)
        self.clear_btn.setMinimumWidth(220)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 15px;
                background-color: #757575;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #616161; }}
        """)
        self.clear_btn.clicked.connect(self.clear_connections)
        controls.addWidget(self.clear_btn)

        controls.addStretch()

        self.quiz_label = QLabel("Контроль не запущен")
        self.quiz_label.setStyleSheet(
            f"color: {GRAY_COLOR}; font-size: 15px; font-weight: bold;"
        )
        controls.addWidget(self.quiz_label)

        layout.addLayout(controls)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_lbl = QLabel("🔍 Поиск:")
        filter_lbl.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 14px; font-weight: bold;"
        )
        filter_row.addWidget(filter_lbl)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(
            "Введите ФИО или группу для фильтрации..."
        )
        self.filter_input.setMinimumHeight(40)
        self.filter_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 14px;
                padding: 5px 12px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                background-color: white;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{ border-color: {ACCENT_HOVER}; }}
        """)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.filter_input, 1)

        reset_filter_btn = QPushButton("Сбросить")
        reset_filter_btn.setMinimumHeight(40)
        reset_filter_btn.setMinimumWidth(120)
        reset_filter_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 14px;
                background-color: #757575;
                color: white;
                border-radius: 8px;
                padding: 5px 15px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #616161; }}
        """)
        reset_filter_btn.clicked.connect(self._reset_filter)
        filter_row.addWidget(reset_filter_btn)

        layout.addLayout(filter_row)

        splitter = QSplitter(Qt.Vertical)

        connected_widget = QWidget()
        connected_layout = QVBoxLayout(connected_widget)
        connected_layout.setContentsMargins(0, 0, 0, 0)
        connected_layout.setSpacing(8)

        self.connected_title = QLabel("Подключены к серверу: 0")
        self.connected_title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 17px; font-weight: bold; padding: 5px;"
        )
        connected_layout.addWidget(self.connected_title)

        self.connected_table = QTableWidget()
        self.connected_table.setColumnCount(4)
        self.connected_table.setHorizontalHeaderLabels([
            "#", "ФИО", "Группа", "Подключился"
        ])
        self.connected_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connected_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connected_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 14px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                gridline-color: #E0E0E0;
            }}
            QTableWidget::item {{ padding: 8px; }}
            QTableWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
            }}
            QHeaderView::section {{
                background-color: {HEADER_COLOR};
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }}
            {SCROLLBAR_STYLE}
        """)
        self.connected_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connected_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.connected_table.verticalHeader().setVisible(False)
        connected_layout.addWidget(self.connected_table)

        splitter.addWidget(connected_widget)

        quiz_widget = QWidget()
        quiz_layout = QVBoxLayout(quiz_widget)
        quiz_layout.setContentsMargins(0, 0, 0, 0)
        quiz_layout.setSpacing(8)

        self.quiz_title = QLabel("Результаты контроля")
        self.quiz_title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 17px; font-weight: bold; padding: 5px;"
        )
        quiz_layout.addWidget(self.quiz_title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "ФИО", "Группа", "Станция", "Осталось", "Оценка",
            "Статус", "Время"
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
            QTableWidget::item {{ padding: 10px; }}
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
        self.table.setSortingEnabled(False)
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        quiz_layout.addWidget(self.table)

        self.stats_label = QLabel("Всего: 0   ✅ 0   🟡 0   ⛔ 0")
        self.stats_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 14px; font-weight: bold; padding: 5px;"
        )
        quiz_layout.addWidget(self.stats_label)

        splitter.addWidget(quiz_widget)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

    def _on_filter_changed(self, text):
        self.filter_text = text.strip().lower()
        self.refresh_students()

    def _reset_filter(self):
        self.filter_input.setText("")
        self.filter_text = ""
        self.refresh_students()

    def start_quiz(self):
        active = self.db.get_active_quiz()
        if active:
            QMessageBox.warning(
                self, "Контроль уже идёт",
                "Сначала остановите текущий контроль."
            )
            return

        dialog = StartQuizDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        choice = dialog.get_choice()
        topic = choice["topic"]
        station_ids = choice.get("station_ids", [])

        if topic == "multi" and not station_ids:
            QMessageBox.warning(
                self, "Ошибка",
                "Выберите хотя бы одну станцию."
            )
            return

        if topic == "multi":
            stations = _load_stations()
            total_specs = 0
            for sid in station_ids:
                st = next((s for s in stations if s["id"] == sid), None)
                if st:
                    total_specs += len(st["specs"])
            q_count = _calculate_question_count(
                total_specs // max(1, len(station_ids))
            )
        else:
            q_count = QUIZ_MIN_QUESTIONS

        self.db.create_quiz(
            topic,
            station_id=None,
            station_name=None,
            question_count=q_count,
            station_ids=station_ids,
        )

        self.stop_btn.setEnabled(True)
        self.start_btn.setEnabled(False)

        topic_text = {
            "multi": f"Несколько станций ({len(station_ids)} шт.)",
            "radio": "Все радиорелейные",
            "satellite": "Все спутниковые",
            "all": "Все станции",
        }.get(topic, topic)

        self.quiz_label.setText(f"Контроль: {topic_text}")
        self.quiz_label.setStyleSheet(
            f"color: {ACCENT_COLOR}; font-size: 15px; font-weight: bold;"
        )

        self.refresh_all()

    def stop_quiz(self):
        active = self.db.get_active_quiz()
        if not active:
            return
        if QMessageBox.question(
            self, "Остановить контроль",
            "Все, кто не сдал, будут помечены как «Прервано». Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.db.stop_quiz(active["id"])
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.quiz_label.setText("Контроль не запущен")
        self.quiz_label.setStyleSheet(
            f"color: {GRAY_COLOR}; font-size: 15px; font-weight: bold;"
        )
        self.refresh_all()

    def clear_connections(self):
        if QMessageBox.question(
            self, "Очистить подключённых",
            "Удалить всех подключённых из списка?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.db.clear_connections()
        self.refresh_all()

    def refresh_all(self):
        self.refresh_connected()
        self.refresh_students()

    def refresh_connected(self):
        self.db.cleanup_connections(CONNECTION_TIMEOUT)
        students = self.db.get_connected_students()

        self.connected_title.setText(f"Подключены к серверу: {len(students)}")
        self.connected_table.setRowCount(len(students))

        for i, s in enumerate(students):
            self.connected_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.connected_table.setItem(i, 1, QTableWidgetItem(s.get("fio", "")))
            self.connected_table.setItem(i, 2, QTableWidgetItem(s.get("group_name", "")))
            self.connected_table.setItem(i, 3, QTableWidgetItem(s.get("connected_at", "")))

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

        if self.filter_text:
            students = [
                s for s in students
                if self.filter_text in (s.get("fio", "").lower())
                or self.filter_text in (s.get("group_name", "").lower())
            ]

        self.table.setRowCount(len(students))

        counter = {"finished": 0, "in_progress": 0, "interrupted": 0, "waiting": 0}

        for i, s in enumerate(students):
            status = s.get("status", "waiting")
            counter[status] = counter.get(status, 0) + 1

            duration = s.get("duration", 0)
            time_limit = s.get("question_count", 0) * SCORE_PER_QUESTION

            if status == "finished" or status == "interrupted":
                remaining_text = "—"
                remaining_sec = None
            else:
                elapsed = self._calc_elapsed(s)
                remaining_sec = max(0, time_limit - elapsed)
                remaining_text = _fmt_time(remaining_sec)

            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("fio", "")))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("group_name", "")))
            self.table.setItem(i, 3, QTableWidgetItem(s.get("station_name", "—")))

            remaining_item = QTableWidgetItem(remaining_text)
            f = QFont()
            f.setBold(True)
            remaining_item.setFont(f)
            self.table.setItem(i, 4, remaining_item)

            grade = s.get("grade", 0)
            percent = s.get("percent", 0)
            if status == "finished" and grade:
                grade_item = QTableWidgetItem(f"{grade}  ({percent:.0f}%)")
                f2 = QFont()
                f2.setBold(True)
                grade_item.setFont(f2)
                grade_item.setForeground(QColor(_grade_color(grade)))
            else:
                grade_item = QTableWidgetItem("—")
            self.table.setItem(i, 5, grade_item)

            status_item = QTableWidgetItem(STATUS_LABELS.get(status, status))
            f3 = QFont()
            f3.setBold(True)
            status_item.setFont(f3)
            status_item.setForeground(QColor(STATUS_COLORS.get(status, TEXT_COLOR)))
            self.table.setItem(i, 6, status_item)

            duration_text = "—" if duration <= 0 else _fmt_time(duration)
            self.table.setItem(i, 7, QTableWidgetItem(duration_text))

            row_color = None
            if status in ("in_progress", "waiting") and remaining_sec is not None:
                if remaining_sec <= 10:
                    row_color = RED_BG
                elif remaining_sec <= 30:
                    row_color = ORANGE_BG
                elif remaining_sec <= 60:
                    row_color = YELLOW_BG

            if row_color:
                for col in range(self.table.columnCount()):
                    cell = self.table.item(i, col)
                    if cell:
                        cell.setBackground(QColor(row_color))

        total = len(students)
        self.stats_label.setText(
            f"Всего: {total}   "
            f"✅ Завершили: {counter['finished']}   "
            f"🟡 В процессе: {counter['in_progress'] + counter['waiting']}   "
            f"⛔ Прервано: {counter['interrupted']}"
        )

    def _calc_elapsed(self, s):
        started_at = s.get("started_at")
        if not started_at:
            return 0
        try:
            dt = datetime.fromisoformat(started_at)
            return int((datetime.now() - dt).total_seconds())
        except Exception:
            return 0

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
