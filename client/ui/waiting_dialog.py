"""
Окно ожидания контроля.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer


HEADER_COLOR = "#1B4332"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"
TEXT_COLOR = "#1B1B1B"
WARN_COLOR = "#B45309"

HEARTBEAT_INTERVAL = 30
SERVER_CHECK_INTERVAL = 5


class WaitingDialog(QDialog):

    def __init__(self, api_client, fio, group_name, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.fio = fio
        self.group_name = group_name
        self.result = None
        self.fail_count = 0

        self.setWindowTitle("Ожидание контроля")
        self.setFixedSize(700, 680)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)

        title = QLabel("⏳  Ожидайте")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 28px; font-weight: bold;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Преподаватель скоро запустит контроль")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 15px;")
        layout.addWidget(subtitle)

        info_frame = QLabel(
            f"<b>Курсант:</b> {fio} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Группа:</b> {group_name}"
        )
        info_frame.setAlignment(Qt.AlignCenter)
        info_frame.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 14px; "
            f"background-color: #E8F5E9; padding: 10px; border-radius: 8px;"
        )
        layout.addWidget(info_frame)

        self.status_label = QLabel("✅ Вы подключены к серверу")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 13px;")
        layout.addWidget(self.status_label)

        hints_title = QLabel("📋  Как правильно записывать ответы")
        hints_title.setStyleSheet(
            f"color: {WARN_COLOR}; font-size: 15px; font-weight: bold; "
            f"padding: 6px;"
        )
        layout.addWidget(hints_title)

        hints = QLabel(
            "• <b>Диапазон</b> — через дефис, без пробелов: <b>390-645</b><br>"
            "• <b>Дробное число</b> — через точку: <b>2.5</b> (а не 2,5)<br>"
            "• <b>Мощность</b> — только число, единицу выбрать из списка: "
            "<b>22</b> + <b>Вт</b><br>"
            "• <b>Частота</b> — только число, единицу выбрать из списка: "
            "<b>100</b> + <b>кГц</b><br>"
            "• <b>Скорость</b> — только число: <b>2048</b> + <b>кбит/с</b><br>"
            "• <b>Несколько значений</b> — через запятую: "
            "<b>QPSK, 8PSK</b><br>"
            "• <b>Без единицы</b> — оставьте поле единицы пустым<br>"
        )
        hints.setTextFormat(Qt.RichText)
        hints.setWordWrap(True)
        hints.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 13px; line-height: 1.6; "
            f"background-color: white; padding: 14px; "
            f"border: 2px solid {LIGHT_ACCENT}; border-radius: 8px;"
        )
        layout.addWidget(hints)

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

        self.api_client.register(self.fio, self.group_name)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_quiz)
        self.timer.start(2000)

        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(HEARTBEAT_INTERVAL * 1000)

        self.server_check_timer = QTimer()
        self.server_check_timer.timeout.connect(self.check_server)
        self.server_check_timer.start(SERVER_CHECK_INTERVAL * 1000)

        self.check_quiz()

    def send_heartbeat(self):
        self.api_client.heartbeat(fio=self.fio, group_name=self.group_name)

    def check_quiz(self):
        info = self.api_client.quiz_info()
        if info.get("active"):
            self.result = info
            self.stop_all()
            self.accept()

    def check_server(self):
        if self.api_client.ping():
            self.fail_count = 0
            self.status_label.setText("✅ Вы подключены к серверу")
            self.status_label.setStyleSheet(
                f"color: {ACCENT_COLOR}; font-size: 13px;"
            )
        else:
            self.fail_count += 1
            self.status_label.setText(
                "⚠ Связь с сервером потеряна. Проверьте соединение."
            )
            self.status_label.setStyleSheet(
                f"color: {WARN_COLOR}; font-size: 13px; font-weight: bold;"
            )
            if self.fail_count >= 3:
                QMessageBox.warning(
                    self,
                    "Сервер недоступен",
                    "Связь с сервером потеряна.\n\n"
                    "Программа будет закрыта."
                )
                self.stop_all()
                self.reject()

    def stop_all(self):
        for name in ["timer", "heartbeat_timer", "server_check_timer"]:
            t = getattr(self, name, None)
            if t is not None:
                try:
                    t.stop()
                except Exception:
                    pass

    def closeEvent(self, event):
        try:
            self.api_client.disconnect(self.fio, self.group_name)
        except Exception:
            pass
        self.stop_all()
        super().closeEvent(event)

    def reject(self):
        try:
            self.api_client.disconnect(self.fio, self.group_name)
        except Exception:
            pass
        self.stop_all()
        super().reject()
