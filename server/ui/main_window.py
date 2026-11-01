import os
import sys
import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QSizePolicy, QSplitter, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QCursor


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

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_SUCCESS_BG, COLOR_WARNING, COLOR_WARNING_BG,
    COLOR_DANGER, COLOR_DANGER_BG, BTN_PRIMARY_STYLE, BTN_SECONDARY_STYLE,
    BTN_DANGER_STYLE, make_badge_html
)

STATUS_LABELS = {
    "waiting": "Ожидает",
    "in_progress": "В процессе",
    "finished": "Завершил",
    "interrupted": "Прервано",
}

STATUS_COLORS = {
    "waiting": COLOR_TEXT_MUTED,
    "in_progress": COLOR_WARNING,
    "finished": COLOR_SUCCESS,
    "interrupted": COLOR_DANGER,
}

STATUS_BGS = {
    "waiting": "#F1F5F9",
    "in_progress": COLOR_WARNING_BG,
    "finished": COLOR_SUCCESS_BG,
    "interrupted": COLOR_DANGER_BG,
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
        return COLOR_SUCCESS
    if grade == 4:
        return "#15803D"
    if grade == 3:
        return COLOR_WARNING
    return COLOR_DANGER


def _fmt_time(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


class KpiCard(QFrame):
    """Информационная карточка метрики для преподавателя."""

    def __init__(self, title, initial_value="0", bg_color="#FFFFFF", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_SECONDARY}; text-transform: uppercase; border: none;")
        layout.addWidget(self.title_lbl)

        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLOR_PRIMARY_DARK}; border: none;")
        layout.addWidget(self.value_lbl)

    def set_value(self, val):
        self.value_lbl.setText(str(val))


class StartQuizDialog(QDialog):

    SIZE_MULTI = (640, 740)
    SIZE_SMALL = (520, 380)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка и запуск контроля знаний")
        self.setFixedSize(*self.SIZE_SMALL)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        title = QLabel("Параметры нового билета")
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        topic_lbl = QLabel("Тематика контроля:")
        topic_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(topic_lbl)

        self.topic_combo = QComboBox()
        self.topic_combo.addItem("Несколько станций (случайно)", "multi")
        self.topic_combo.addItem("Все радиорелейные станции", "radio")
        self.topic_combo.addItem("Все спутниковые станции", "satellite")
        self.topic_combo.addItem("Все станции комплекса", "all")
        self.topic_combo.addItem("📷 Фото — все станции", "photo_all")
        self.topic_combo.addItem("📷 Фото — радиорелейные", "photo_radio")
        self.topic_combo.addItem("📷 Фото — спутниковые", "photo_satellite")
        self.topic_combo.setMinimumHeight(42)
        self.topic_combo.currentIndexChanged.connect(self._on_topic_changed)
        layout.addWidget(self.topic_combo)

        self.multi_widget = QWidget()
        multi_layout = QVBoxLayout(self.multi_widget)
        multi_layout.setContentsMargins(0, 0, 0, 0)
        multi_layout.setSpacing(8)

        self.stations_label = QLabel("Выберите станции для случайной выборки:")
        self.stations_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
        multi_layout.addWidget(self.stations_label)

        self.select_all_btn = QPushButton("Выбрать все / Снять все")
        self.select_all_btn.setMinimumHeight(34)
        self.select_all_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        self.select_all_btn.clicked.connect(self._toggle_all)
        multi_layout.addWidget(self.select_all_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ border: 1.5px solid {COLOR_BORDER}; border-radius: 8px; background-color: {COLOR_CARD_BG}; }}")

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"QListWidget {{ border: none; padding: 4px; }}")

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
        multi_layout.addWidget(self.scroll, 1)

        self.hint = QLabel("Каждому подключенному курсанту будет назначен случайный вариант из выбранных.")
        self.hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.hint.setWordWrap(True)
        multi_layout.addWidget(self.hint)

        layout.addWidget(self.multi_widget, 1)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(12)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        ok_btn = QPushButton("Начать контроль →")
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setMinimumHeight(42)
        ok_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        ok_btn.clicked.connect(self.accept)
        btns.addWidget(ok_btn)

        layout.addLayout(btns)
        self._on_topic_changed()

    def _on_topic_changed(self):
        topic = self.topic_combo.currentData()
        is_multi = (topic == "multi")
        self.multi_widget.setVisible(is_multi)
        if is_multi:
            self.setFixedSize(*self.SIZE_MULTI)
        else:
            self.setFixedSize(*self.SIZE_SMALL)

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

    def get_choice(self):
        topic = self.topic_combo.currentData()
        if topic == "multi":
            selected_ids = []
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    selected_ids.append(item.data(Qt.UserRole))
            return {"topic": topic, "station_ids": selected_ids}
        return {"topic": topic, "station_ids": []}


class HistoryDialog(QDialog):

    def __init__(self, fio, group_name, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"История попыток: {fio}")
        self.resize(800, 520)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QLabel(f"Протокол попыток — {fio} (Группа: {group_name})")
        header.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 18px; font-weight: 700;")
        layout.addWidget(header)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "#", "Дата и время", "Станция", "Баллы", "Оценка", "Время"
        ])
        table.setRowCount(len(history))
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)

        for i, attempt in enumerate(history):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem(attempt.get("finished_at", "")))
            table.setItem(i, 2, QTableWidgetItem(attempt.get("station_name", "")))
            table.setItem(
                i, 3,
                QTableWidgetItem(f"{attempt.get('correct_count', 0)} / {attempt.get('question_count', 0)}")
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
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(140)
        close_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)


class ServerWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Рабочее место преподавателя — Сервер контроля skrss")
        self.resize(1380, 880)
        self.setMinimumSize(1050, 650)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

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
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Верхняя плашка сервера
        top_bar = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Панель управления аттестацией")
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 22px; font-weight: 800;")
        title_box.addWidget(title)

        sub = QLabel("Мониторинг подключенных терминалов и проведение контроля в реальном времени")
        sub.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px;")
        title_box.addWidget(sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.ip_pill = QLabel(f"🌐 IP: <b>{self.server_ip}</b> &nbsp;|&nbsp; Порт: <b>{self.server_port}</b> &nbsp;|&nbsp; Broadcast: <b>5001</b>")
        self.ip_pill.setStyleSheet(f"""
            background-color: {COLOR_PRIMARY_PALE};
            color: {COLOR_PRIMARY_DARK};
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #B7E4C7;
        """)
        top_bar.addWidget(self.ip_pill)
        layout.addLayout(top_bar)

        # KPI Карточки статистики
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        self.kpi_connected = KpiCard("Подключено курсантов", "0", COLOR_CARD_BG, self)
        self.kpi_in_progress = KpiCard("Сдают сейчас", "0", COLOR_CARD_BG, self)
        self.kpi_finished = KpiCard("Завершили контроль", "0", COLOR_CARD_BG, self)
        self.kpi_avg = KpiCard("Успеваемость (сдано)", "0%", COLOR_CARD_BG, self)

        kpi_row.addWidget(self.kpi_connected)
        kpi_row.addWidget(self.kpi_in_progress)
        kpi_row.addWidget(self.kpi_finished)
        kpi_row.addWidget(self.kpi_avg)
        layout.addLayout(kpi_row)

        # Панель управления контролем
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 10px 14px;
            }}
        """)
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(12)

        self.start_btn = QPushButton("🚀 Начать контроль...")
        self.start_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setMinimumWidth(200)
        self.start_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.start_btn.clicked.connect(self.start_quiz)
        ctrl_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🛑 Остановить контроль")
        self.stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setMinimumWidth(200)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(BTN_DANGER_STYLE)
        self.stop_btn.clicked.connect(self.stop_quiz)
        ctrl_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🧹 Очистить список подключений")
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_btn.setMinimumHeight(44)
        self.clear_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        self.clear_btn.clicked.connect(self.clear_connections)
        ctrl_layout.addWidget(self.clear_btn)

        ctrl_layout.addStretch()

        self.quiz_status_badge = QLabel(make_badge_html("Контроль не запущен", "#F1F5F9", COLOR_TEXT_MUTED))
        self.quiz_status_badge.setStyleSheet("border: none;")
        ctrl_layout.addWidget(self.quiz_status_badge)

        layout.addWidget(ctrl_card)

        # Строка быстрого поиска
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 Поиск курсанта по ФИО или учебной группе...")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.setMinimumHeight(38)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.filter_input, 1)

        reset_filter_btn = QPushButton("Сброс")
        reset_filter_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reset_filter_btn.setMinimumHeight(38)
        reset_filter_btn.setMinimumWidth(100)
        reset_filter_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        reset_filter_btn.clicked.connect(self._reset_filter)
        filter_row.addWidget(reset_filter_btn)

        layout.addLayout(filter_row)

        # Разделитель с таблицами: Подключенные и Результаты
        splitter = QSplitter(Qt.Vertical)

        # Верхняя таблица: Подключенные курсанты
        connected_widget = QWidget()
        connected_layout = QVBoxLayout(connected_widget)
        connected_layout.setContentsMargins(0, 0, 0, 0)
        connected_layout.setSpacing(8)

        self.connected_title = QLabel("Подключенные терминалы (в ожидании билета): 0")
        self.connected_title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 15px; font-weight: 700;")
        connected_layout.addWidget(self.connected_title)

        self.connected_table = QTableWidget()
        self.connected_table.setColumnCount(4)
        self.connected_table.setHorizontalHeaderLabels([
            "#", "ФИО курсанта", "Учебная группа", "Время входа"
        ])
        self.connected_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connected_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connected_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connected_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.connected_table.verticalHeader().setVisible(False)
        connected_layout.addWidget(self.connected_table)
        splitter.addWidget(connected_widget)

        # Нижняя таблица: Студенты на контроле и их результаты
        quiz_widget = QWidget()
        quiz_layout = QVBoxLayout(quiz_widget)
        quiz_layout.setContentsMargins(0, 0, 0, 0)
        quiz_layout.setSpacing(8)

        self.quiz_title = QLabel("Протокол текущего контроля (двойной клик — история попыток)")
        self.quiz_title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 15px; font-weight: 700;")
        quiz_layout.addWidget(self.quiz_title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "ФИО курсанта", "Группа", "Назначенная станция", "Осталось", "Оценка", "Статус", "Затрачено"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        quiz_layout.addWidget(self.table)

        splitter.addWidget(quiz_widget)
        splitter.setSizes([260, 480])

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
            QMessageBox.warning(self, "Внимание", "Контроль уже идёт. Сначала остановите текущую сессию.")
            return

        dialog = StartQuizDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return

        choice = dialog.get_choice()
        topic = choice["topic"]
        station_ids = choice.get("station_ids", [])

        if topic == "multi" and not station_ids:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну станцию из списка.")
            return

        if topic == "multi":
            stations = _load_stations()
            total_specs = 0
            for sid in station_ids:
                st = next((s for s in stations if s["id"] == sid), None)
                if st:
                    total_specs += len(st["specs"])
            q_count = _calculate_question_count(total_specs // max(1, len(station_ids)))
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
            "multi": f"Случайные ({len(station_ids)} ст.)",
            "radio": "Радиорелейные",
            "satellite": "Спутниковые",
            "all": "Все станции",
            "photo_all": "📷 Фото (все)",
            "photo_radio": "📷 Фото (радио)",
            "photo_satellite": "📷 Фото (спутник)",
        }.get(topic, topic)

        self.quiz_status_badge.setText(make_badge_html(f"Активен: {topic_text}", COLOR_SUCCESS_BG, COLOR_SUCCESS))
        self.refresh_all()

    def stop_quiz(self):
        active = self.db.get_active_quiz()
        if not active:
            return
        if QMessageBox.question(
            self, "Остановить контроль",
            "Все обучающиеся, не успевшие сдать ответы, будут помечены как «Прервано». Завершить сессию?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.db.stop_quiz(active["id"])
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.quiz_status_badge.setText(make_badge_html("Контроль не запущен", "#F1F5F9", COLOR_TEXT_MUTED))
        self.refresh_all()

    def clear_connections(self):
        if QMessageBox.question(
            self, "Очистить список",
            "Удалить всех подключенных обучающихся из таблицы ожидания?",
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

        self.connected_title.setText(f"Подключенные терминалы (в ожидании билета): {len(students)}")
        self.kpi_connected.set_value(len(students))
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
            self.kpi_in_progress.set_value(0)
            self.kpi_finished.set_value(0)
            self.kpi_avg.set_value("0%")
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
        total_finished_grades = []

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
                total_finished_grades.append(grade)
                grade_item = QTableWidgetItem(f"{grade}  ({percent:.0f}%)")
                f2 = QFont()
                f2.setBold(True)
                grade_item.setFont(f2)
                grade_item.setForeground(QColor(_grade_color(grade)))
            else:
                grade_item = QTableWidgetItem("—")
            self.table.setItem(i, 5, grade_item)

            # Статус
            status_item = QTableWidgetItem(STATUS_LABELS.get(status, status))
            f3 = QFont()
            f3.setBold(True)
            status_item.setFont(f3)
            status_item.setForeground(QColor(STATUS_COLORS.get(status, COLOR_TEXT_PRIMARY)))
            self.table.setItem(i, 6, status_item)

            duration_text = "—" if duration <= 0 else _fmt_time(duration)
            self.table.setItem(i, 7, QTableWidgetItem(duration_text))

            # Подсветка строки при тревоге по времени
            if status in ("in_progress", "waiting") and remaining_sec is not None:
                if remaining_sec <= 10:
                    for col in range(self.table.columnCount()):
                        cell = self.table.item(i, col)
                        if cell:
                            cell.setBackground(QColor(COLOR_DANGER_BG))
                elif remaining_sec <= 30:
                    for col in range(self.table.columnCount()):
                        cell = self.table.item(i, col)
                        if cell:
                            cell.setBackground(QColor(COLOR_WARNING_BG))

        # Обновление KPI
        self.kpi_in_progress.set_value(counter["in_progress"] + counter["waiting"])
        self.kpi_finished.set_value(counter["finished"])
        if total_finished_grades:
            avg_grade = sum(total_finished_grades) / len(total_finished_grades)
            self.kpi_avg.set_value(f"{avg_grade:.1f}")
        else:
            self.kpi_avg.set_value("—")

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
                f"У курсанта {fio} пока нет завершённых попыток."
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
