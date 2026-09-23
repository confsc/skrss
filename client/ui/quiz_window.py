from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import random
from logic.data_loader import load_stations
from ui.quiz_dialog import QuizDialog


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"

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


class StationListTab(QWidget):

    def __init__(self, quiz_window):
        super().__init__()
        self.quiz_window = quiz_window
        self.stations = load_stations()
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Список станций")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(title)

        info = QLabel(
            "Нажмите на станцию, чтобы начать летучку по ней.\n"
            "Сервер выдаст вопросы и примет результат."
        )
        info.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")
        layout.addWidget(info)

        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                font-size: 16px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                padding: 8px;
                color: {TEXT_COLOR};
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid #E0E0E0;
                outline: none;
            }}
            QListWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
                font-weight: bold;
                border-radius: 5px;
                border: none;
                outline: none;
            }}
            QListWidget::item:hover {{
                background-color: #E8F5E9;
            }}
            {SCROLLBAR_STYLE}
        """)
        self.list_widget.itemClicked.connect(self.start_control)

        radio = [s for s in self.stations if s["category"] == "radio"]
        satellite = [s for s in self.stations if s["category"] == "satellite"]

        f = QFont()
        f.setBold(True)
        f.setPointSize(13)

        header_radio = QListWidgetItem("── РАДИОРЕЛЕЙНЫЕ СТАНЦИИ ──")
        header_radio.setFlags(Qt.NoItemFlags)
        header_radio.setForeground(Qt.darkGreen)
        header_radio.setFont(f)
        self.list_widget.addItem(header_radio)

        for s in radio:
            item = QListWidgetItem("  " + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

        header_sat = QListWidgetItem("── СПУТНИКОВЫЕ СТАНЦИИ ──")
        header_sat.setFlags(Qt.NoItemFlags)
        header_sat.setForeground(Qt.darkBlue)
        header_sat.setFont(f)
        self.list_widget.addItem(header_sat)

        for s in satellite:
            item = QListWidgetItem("  " + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

    def start_control(self, item):
        QMessageBox.information(
            self, "Внимание",
            "В режиме летучки станцию выдаёт сервер.\n"
            "Сейчас будет запущена летучка по этой станции,\n"
            "если сервер её назначил."
        )


class QuizWindow(QMainWindow):

    def __init__(self, back_callback, api_client, fio, group_name):
        super().__init__()
        self.back_callback = back_callback
        self.api_client = api_client
        self.fio = fio
        self.group_name = group_name

        self.setWindowTitle(f"Режим контроля — {fio} ({group_name})")
        self.resize(1100, 800)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад")
        back_btn.setMinimumHeight(45)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 15px; background-color: {ACCENT_HOVER};
                color: white; border-radius: 8px;
                padding: 8px 20px; border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_COLOR}; }}
        """)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()

        user_info = QLabel(f"Курсант: <b>{fio}</b>  |  Группа: <b>{group_name}</b>")
        user_info.setStyleSheet(f"color: {HEADER_COLOR}; font-size: 14px;")
        top.addWidget(user_info)
        layout.addLayout(top)

        info_frame = QLabel(
            "⏳  Сейчас активна летучка от преподавателя.\n"
            "Станция и вопросы приходят от сервера."
        )
        info_frame.setAlignment(Qt.AlignCenter)
        info_frame.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 15px; font-weight: bold; "
            f"background-color: #E8F5E9; padding: 15px; border-radius: 10px;"
        )
        layout.addWidget(info_frame)

        self.start_btn = QPushButton("🚀  Начать летучку")
        self.start_btn.setMinimumHeight(60)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 18px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 10px; border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        self.start_btn.clicked.connect(self.start_quiz)
        layout.addWidget(self.start_btn)

        self.station_label = QLabel("")
        self.station_label.setAlignment(Qt.AlignCenter)
        self.station_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 16px; padding: 10px;"
        )
        layout.addWidget(self.station_label)

        layout.addStretch()

    def start_quiz(self):
        status, data = self.api_client.start_quiz(self.fio, self.group_name)

        if status == 409:
            QMessageBox.warning(
                self, "Вы уже сдали",
                data.get("message", "Вы уже сдали летучку.")
            )
            return

        if status != 200 or data.get("status") != "ok":
            QMessageBox.warning(
                self, "Ошибка",
                data.get("message", "Не удалось начать летучку.")
            )
            return

        self.station_label.setText(
            f"Станция: <b>{data.get('station_name', '—')}</b>  |  "
            f"Вопросов: <b>{data.get('question_count', 0)}</b>  |  "
            f"Время: <b>{data.get('time_limit', 0)} сек</b>"
        )

        dialog = QuizDialog(
            station_id=data.get("station_id"),
            station_name=data.get("station_name"),
            specs=data.get("specs", []),
            time_limit=data.get("time_limit", 60),
            student_id=data.get("student_id"),
            api_client=self.api_client,
            parent=self,
            is_control=True,
            is_server_mode=True,
        )
        dialog.exec_()

        self.go_back()

    def go_back(self):
        self.back_callback()
        self.close()