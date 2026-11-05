"""
Диалог ввода ФИО, группы и IP сервера.
С сохранением последних значений.
"""
import os
import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK,
    COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    BTN_PRIMARY_STYLE, BTN_SECONDARY_STYLE
)


def _config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "RRSTrainer")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _settings_path():
    return os.path.join(_config_dir(), "settings.json")


def load_settings():
    path = _settings_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    path = _settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class StudentFormDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Регистрация на контроль знаний")
        self.setMinimumSize(520, 520)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        self.fio = ""
        self.group = ""
        self.manual_ip = ""

        settings = load_settings()
        last_ip = settings.get("last_ip", "")
        last_fio = settings.get("last_fio", "")
        last_group = settings.get("last_group", "")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Карточка формы
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

        # Заголовок
        title = QLabel("Идентификация обучающегося")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 20px; font-weight: 700; border: none;")
        card_layout.addWidget(title)

        hint = QLabel("Данные будут переданы на сервер преподавателя для ведения протокола.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; border: none;")
        card_layout.addWidget(hint)

        card_layout.addSpacing(6)

        # Поле ФИО
        fio_label = QLabel("ФИО обучающегося:")
        fio_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 600; border: none;")
        card_layout.addWidget(fio_label)

        self.fio_input = QLineEdit()
        self.fio_input.setPlaceholderText("Иванов Иван Иванович")
        self.fio_input.setText(last_fio)
        self.fio_input.setMinimumHeight(42)
        card_layout.addWidget(self.fio_input)

        # Поле Группа
        group_label = QLabel("Учебная группа:")
        group_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: 600; border: none;")
        card_layout.addWidget(group_label)

        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Например: 21-Б или 302")
        self.group_input.setText(last_group)
        self.group_input.setMinimumHeight(42)
        card_layout.addWidget(self.group_input)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLOR_BORDER}; border: none; height: 1px; background-color: {COLOR_BORDER};")
        card_layout.addWidget(sep)

        # IP сервера
        ip_label = QLabel("IP-адрес сервера (опционально):")
        ip_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600; border: none;")
        card_layout.addWidget(ip_label)

        sub_hint = QLabel("Оставьте пустым для автоматического поиска в локальной сети.")
        sub_hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; border: none;")
        card_layout.addWidget(sub_hint)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Например: 192.168.1.50")
        self.ip_input.setText(last_ip)
        self.ip_input.setMinimumHeight(40)
        card_layout.addWidget(self.ip_input)

        layout.addWidget(card)

        # Кнопки диалога
        btns = QHBoxLayout()
        btns.setSpacing(12)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn, 1)

        ok_btn = QPushButton("Подключиться →")
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setMinimumHeight(44)
        ok_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        ok_btn.clicked.connect(self.on_ok)
        btns.addWidget(ok_btn, 2)

        layout.addLayout(btns)

        self.fio_input.returnPressed.connect(self.group_input.setFocus)
        self.group_input.returnPressed.connect(self.ip_input.setFocus)
        self.ip_input.returnPressed.connect(self.on_ok)

    def on_ok(self):
        fio = self.fio_input.text().strip()
        group = self.group_input.text().strip()
        ip = self.ip_input.text().strip()

        if not fio or len(fio) < 3:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите ФИО обучающегося полностью.")
            self.fio_input.setFocus()
            return
        if not group or len(group) < 1:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, укажите номер учебной группы.")
            self.group_input.setFocus()
            return

        self.fio = fio
        self.group = group
        self.manual_ip = ip

        save_settings({
            "last_ip": ip,
            "last_fio": fio,
            "last_group": group,
        })

        self.accept()
