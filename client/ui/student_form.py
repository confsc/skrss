"""
Диалог ввода ФИО, группы и (опционально) IP сервера.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt


HEADER_COLOR = "#1B4332"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"
TEXT_COLOR = "#1B1B1B"


class StudentFormDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в режим контроля")
        self.setMinimumSize(580, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.fio = ""
        self.group = ""
        self.manual_ip = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(15)

        title = QLabel("Введите свои данные")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(title)

        hint = QLabel(
            "ФИО и группа будут видны преподавателю\n"
            "во время прохождения летучки."
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 13px;")
        layout.addWidget(hint)

        layout.addSpacing(10)

        # ФИО
        fio_label = QLabel("ФИО:")
        fio_label.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(fio_label)

        self.fio_input = QLineEdit()
        self.fio_input.setPlaceholderText("Например: Иванов Иван Иванович")
        self.fio_input.setMinimumHeight(45)
        self.fio_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 15px; padding: 5px 12px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px; background-color: white;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{ border-color: {ACCENT_HOVER}; }}
        """)
        layout.addWidget(self.fio_input)

        # Группа
        group_label = QLabel("Группа:")
        group_label.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(group_label)

        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Например: 21-Б")
        self.group_input.setMinimumHeight(45)
        self.group_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 15px; padding: 5px 12px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px; background-color: white;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{ border-color: {ACCENT_HOVER}; }}
        """)
        layout.addWidget(self.group_input)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #DDDDDD;")
        layout.addWidget(line)

        # IP сервера (опционально)
        ip_hint = QLabel(
            "IP-адрес сервера (если не находит автоматически):"
        )
        ip_hint.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 13px; font-weight: bold;"
        )
        layout.addWidget(ip_hint)

        sub_hint = QLabel(
            "Оставьте пустым — программа попробует найти сервер сама."
        )
        sub_hint.setStyleSheet(f"color: #666666; font-size: 12px;")
        layout.addWidget(sub_hint)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Например: 192.168.1.100 (можно с портом)")
        self.ip_input.setMinimumHeight(45)
        self.ip_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 15px; padding: 5px 12px;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px; background-color: white;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{ border-color: {ACCENT_HOVER}; }}
        """)
        layout.addWidget(self.ip_input)

        layout.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()

        ok_btn = QPushButton("Продолжить")
        ok_btn.setMinimumHeight(48)
        ok_btn.setMinimumWidth(180)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 10px; border: none;
                padding: 8px 20px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        ok_btn.clicked.connect(self.on_ok)
        btns.addWidget(ok_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.setMinimumWidth(150)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px; background-color: #757575;
                color: white; border-radius: 10px; border: none;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        btns.addStretch()
        layout.addLayout(btns)

        self.fio_input.returnPressed.connect(self.group_input.setFocus)
        self.group_input.returnPressed.connect(self.ip_input.setFocus)
        self.ip_input.returnPressed.connect(self.on_ok)

    def on_ok(self):
        fio = self.fio_input.text().strip()
        group = self.group_input.text().strip()
        ip = self.ip_input.text().strip()

        if not fio or len(fio) < 3:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО полностью.")
            return
        if not group or len(group) < 2:
            QMessageBox.warning(self, "Ошибка", "Введите номер группы.")
            return

        self.fio = fio
        self.group = group
        self.manual_ip = ip
        self.accept()
