"""
Окно ожидания контроля.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QCursor

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_SUCCESS_BG, COLOR_WARNING, COLOR_WARNING_BG,
    BTN_SECONDARY_STYLE, make_badge_html
)

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

        self.setWindowTitle("Ожидание запуска контроля знаний")
        self.setFixedSize(650, 640)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Главная карточка
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        title = QLabel("⏳ Ожидание начала контроля")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 22px; font-weight: 700; border: none;")
        card_layout.addWidget(title)

        subtitle = QLabel("Преподаватель формирует задания и запустит тест со своего терминала")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; border: none;")
        card_layout.addWidget(subtitle)

        # Плашка с данными студента
        info_pill = QLabel(f"<b>Обучающийся:</b> {fio} &nbsp;&nbsp;•&nbsp;&nbsp; <b>Группа:</b> {group_name}")
        info_pill.setAlignment(Qt.AlignCenter)
        info_pill.setStyleSheet(f"""
            background-color: {COLOR_PRIMARY_PALE};
            color: {COLOR_PRIMARY_DARK};
            font-size: 13px;
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid #B7E4C7;
        """)
        card_layout.addWidget(info_pill)

        # Статус соединения
        self.status_label = QLabel("● Сервер подключен и готов к передаче заданий")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 13px; font-weight: 600; border: none;")
        card_layout.addWidget(self.status_label)

        # Памятка по вводу ответов
        hints_box = QFrame()
        hints_box.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        hints_layout = QVBoxLayout(hints_box)
        hints_layout.setContentsMargins(14, 12, 14, 12)
        hints_layout.setSpacing(6)

        hints_title = QLabel("📋 Памятка по записи ответов на вопросы:")
        hints_title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 13px; font-weight: 700; border: none;")
        hints_layout.addWidget(hints_title)

        hints_text = QLabel(
            "• <b>Диапазон чисел</b> — через дефис без пробелов: <b>390-645</b><br>"
            "• <b>Дробные числа</b> — через точку: <b>2.5</b> (не через запятую)<br>"
            "• <b>Мощность / Частота / Скорость</b> — число в поле ввода, единица из списка<br>"
            "• <b>Несколько вариантов</b> — через запятую: <b>QPSK, 8PSK</b><br>"
            "• <b>Без размерности</b> — поле единицы измерения оставить пустым"
        )
        hints_text.setTextFormat(Qt.RichText)
        hints_text.setWordWrap(True)
        hints_text.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; line-height: 1.5; border: none;")
        hints_layout.addWidget(hints_text)

        card_layout.addWidget(hints_box)
        layout.addWidget(card)

        # Кнопка отмены
        cancel_btn = QPushButton("Отменить и вернуться")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

        # Сетевая логика (полностью сохранена)
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
            self.status_label.setText("● Сервер подключен и готов к передаче заданий")
            self.status_label.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 13px; font-weight: 600; border: none;")
        else:
            self.fail_count += 1
            self.status_label.setText("⚠ Связь с сервером потеряна. Попытка восстановить...")
            self.status_label.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 13px; font-weight: 700; border: none;")
            if self.fail_count >= 3:
                QMessageBox.warning(
                    self,
                    "Сервер недоступен",
                    "Связь с сервером преподавателя прервана.\n\nПроверьте локальную сеть и работу сервера."
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
