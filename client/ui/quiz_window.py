"""
Окно запуска назначенного преподавателем контроля (QuizWindow).
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor

from ui.quiz_dialog import QuizDialog
from ui.photo_quiz_dialog import PhotoQuizDialog

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_SUCCESS_BG, BTN_PRIMARY_STYLE,
    BTN_SECONDARY_STYLE, make_badge_html
)


class QuizWindow(QMainWindow):

    def __init__(self, back_callback, api_client, fio, group_name):
        super().__init__()
        self.back_callback = back_callback
        self.api_client = api_client
        self.fio = fio
        self.group_name = group_name

        self.setWindowTitle(f"Режим контроля — {fio} ({group_name})")
        self.resize(950, 700)
        self.setMinimumSize(800, 550)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        # Верхняя панель навигации
        top = QHBoxLayout()
        back_btn = QPushButton("← На главный экран")
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setMinimumHeight(40)
        back_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)

        top.addStretch()

        user_badge = QLabel(f"<b>Обучающийся:</b> {fio} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Группа:</b> {group_name}")
        user_badge.setStyleSheet(f"""
            background-color: {COLOR_PRIMARY_PALE};
            color: {COLOR_PRIMARY_DARK};
            font-size: 13px;
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid #B7E4C7;
        """)
        top.addWidget(user_badge)
        layout.addLayout(top)

        # Центральная карточка старта теста
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
        card_layout.setContentsMargins(32, 30, 32, 30)
        card_layout.setSpacing(16)

        title = QLabel("Готовность к аттестации")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 24px; font-weight: 700; border: none;")
        card_layout.addWidget(title)

        status_pill = QLabel(make_badge_html("Контроль активен на сервере", COLOR_SUCCESS_BG, COLOR_SUCCESS, "13px"))
        status_pill.setAlignment(Qt.AlignCenter)
        status_pill.setStyleSheet("border: none;")
        card_layout.addWidget(status_pill)

        desc = QLabel(
            "Сервер преподавателя сформировал экзаменационный билет.\n"
            "После нажатия кнопки «Начать выполнение» будет запущен обратный отсчет времени,\n"
            "и вам будут представлены назначенные вопросы по ТТХ или фотоматериалам."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px; line-height: 1.6; border: none;")
        card_layout.addWidget(desc)

        card_layout.addSpacing(10)

        self.start_btn = QPushButton("Начать выполнение билета →")
        self.start_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_btn.setMinimumHeight(54)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: {COLOR_TEXT_LIGHT};
                font-size: 17px;
                font-weight: 700;
                border-radius: 10px;
                border: none;
                padding: 12px 30px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_HOVER};
            }}
        """)
        self.start_btn.clicked.connect(self.start_quiz)
        card_layout.addWidget(self.start_btn)

        self.station_label = QLabel("")
        self.station_label.setAlignment(Qt.AlignCenter)
        self.station_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; border: none;")
        card_layout.addWidget(self.station_label)

        layout.addWidget(card)
        layout.addStretch()

    def start_quiz(self):
        status, data = self.api_client.start_quiz(self.fio, self.group_name)

        if status == 409:
            QMessageBox.warning(
                self, "Контроль уже сдан",
                data.get("message", "Вы уже завершили прохождение данного контроля.")
            )
            return

        if status != 200 or data.get("status") != "ok":
            QMessageBox.warning(
                self, "Ошибка сервера",
                data.get("message", "Не удалось начать контроль. Обратитесь к преподавателю.")
            )
            return

        mode = data.get("mode", "quiz")

        if mode == "photo":
            self._start_photo_quiz(data)
        else:
            self._start_normal_quiz(data)

        self.go_back()

    def _start_normal_quiz(self, data):
        dialog = QuizDialog(
            station_id=data.get("station_id"),
            station_name=data.get("station_name"),
            specs=data.get("specs", []),
            time_limit=data.get("time_limit", 60),
            student_id=data.get("student_id"),
            api_client=self.api_client,
            fio=self.fio,
            group_name=self.group_name,
            parent=self,
            is_control=True,
            is_server_mode=True,
        )
        dialog.exec_()

    def _start_photo_quiz(self, data):
        dialog = PhotoQuizDialog(
            station_name=data.get("station_name", "Фото-контроль"),
            photo_specs=data.get("photo_specs", []),
            time_limit=data.get("time_limit", 60),
            student_id=data.get("student_id"),
            api_client=self.api_client,
            fio=self.fio,
            group_name=self.group_name,
            parent=self,
        )
        dialog.exec_()

    def go_back(self):
        self.close()

    def closeEvent(self, event):
        try:
            self.api_client.disconnect(self.fio, self.group_name)
        except Exception:
            pass
        if self.back_callback:
            self.back_callback()
            self.back_callback = None
        super().closeEvent(event)
