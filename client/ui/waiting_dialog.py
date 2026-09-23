"""
Окно ожидания летучки.
Показывается, пока преподаватель не запустит летучку.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


HEADER_COLOR = "#1B4332"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"
TEXT_COLOR = "#1B1B1B"


class WaitingDialog(QDialog):

    def __init__(self, api_client, fio, group_name, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.fio = fio
        self.group_name = group_name
        self.result = None

        self.setWindowTitle("Ожидание летучки")
        self.setFixedSize(600, 420)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("⏳  Ожидайте")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 30px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Преподаватель скоро запустит летучку")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 16px;")
        layout.addWidget(subtitle)

        layout.addSpacing(15)

        info_frame = QLabel(
            f"<b>Курсант:</b> {fio}<br>"
            f"<b>Группа:</b> {group_name}"
        )
        info_frame.setAlignment(Qt.AlignCenter)
        info_frame.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 15px; "
            f"background-color: #E8F5E9; padding: 15px; border-radius: 10px;"
        )
        layout.addWidget(info_frame)

        layout.addSpacing(15)

        self.status_label = QLabel("Соединение с сервером активно")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 13px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        cancel_btn = QPushButton("Отменить и выйти")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                background-color: #757575;
                color: white;
                border-radius: 10px;
                border: none;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_quiz)
        self.timer.start(2000)

        self.check_quiz()

    def check_quiz(self):
        info = self.api_client.quiz_info()
        if info.get("active"):
            self.result = info
            self.timer.stop()
            self.accept()