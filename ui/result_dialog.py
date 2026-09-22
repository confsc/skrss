from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"


class ResultDialog(QDialog):

    def __init__(self, station_name, correct, total, percent, errors, is_control=False):
        super().__init__()
        self.setWindowTitle("Результат")
        self.setFixedSize(580, 560)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.errors = errors

        if percent >= 85:
            grade = "ОТЛИЧНО"
            grade_icon = "✔"
            grade_color = "#1B4332"
            grade_bg = "#95D5B2"
        elif percent >= 70:
            grade = "ХОРОШО"
            grade_icon = "✔"
            grade_color = "#2D6A4F"
            grade_bg = "#B7E4C7"
        elif percent >= 60:
            grade = "УДОВЛЕТВОРИТЕЛЬНО"
            grade_icon = "!"
            grade_color = "#B45309"
            grade_bg = "#FDE68A"
        else:
            grade = "НЕУДОВЛЕТВОРИТЕЛЬНО"
            grade_icon = "✘"
            grade_color = "#991B1B"
            grade_bg = "#FECACA"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(15)

        if is_control:
            header = QLabel("РЕЖИМ КОНТРОЛЯ")
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet(
                f"color: {ACCENT_COLOR}; font-size: 14px; "
                f"letter-spacing: 3px; font-weight: bold;"
            )
            layout.addWidget(header)

        station_label = QLabel(station_name)
        station_label.setAlignment(Qt.AlignCenter)
        station_label.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 20px; font-weight: bold; padding: 5px;"
        )
        layout.addWidget(station_label)

        grade_label = QLabel(f"{grade_icon}  {grade}")
        grade_label.setAlignment(Qt.AlignCenter)
        grade_label.setStyleSheet(
            f"color: {grade_color}; background-color: {grade_bg}; "
            f"font-size: 26px; font-weight: bold; padding: 15px; border-radius: 12px;"
        )
        layout.addWidget(grade_label)

        count_label = QLabel(f"Правильных ответов: <b>{correct}</b> из <b>{total}</b>")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet(f"font-size: 18px; color: {TEXT_COLOR}; padding: 5px;")
        layout.addWidget(count_label)

        percent_label = QLabel(f"{percent:.1f}%")
        percent_label.setAlignment(Qt.AlignCenter)
        percent_label.setFixedHeight(90)
        percent_label.setStyleSheet(
            f"background-color: {grade_color}; color: white; "
            f"font-size: 42px; font-weight: bold; border-radius: 15px;"
        )
        layout.addWidget(percent_label)

        layout.addStretch()

        if not errors:
            msg = QLabel("🎉 Все ответы верны!")
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet(
                f"font-size: 17px; color: {grade_color}; font-weight: bold;"
            )
            layout.addWidget(msg)
        else:
            msg = QLabel(f"Ошибок: {len(errors)}")
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet(
                "font-size: 17px; color: #991B1B; font-weight: bold;"
            )
            layout.addWidget(msg)

        btns = QHBoxLayout()
        btns.addStretch()

        if errors:
            err_btn = QPushButton("Показать ошибки")
            err_btn.setFixedHeight(48)
            err_btn.setMinimumWidth(200)
            err_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_COLOR};
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0 25px;
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background-color: {ACCENT_HOVER};
                }}
            """)
            err_btn.clicked.connect(self.show_errors)
            btns.addWidget(err_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(48)
        close_btn.setMinimumWidth(160)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 16px;
                padding: 0 25px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)

        btns.addStretch()
        layout.addLayout(btns)

    def show_errors(self):
        ErrorsDialog(self.errors, parent=self).exec_()


class ErrorsDialog(QDialog):

    def __init__(self, errors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список ошибок")
        self.resize(750, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel(f"Найдено ошибок: {len(errors)}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 24px; font-weight: bold; padding: 5px;"
        )
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: 2px solid {LIGHT_ACCENT}; "
            f"border-radius: 8px; background-color: white; }}"
        )
        inner = QWidget()
        inner.setStyleSheet("background-color: white;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(15, 15, 15, 15)

        for i, err in enumerate(errors, 1):
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background-color: #FEF2F2; "
                "border-left: 5px solid #C62828; border-radius: 6px; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 12, 15, 12)
            card_layout.setSpacing(5)

            name_lbl = QLabel(f"{i}. {err['name']}")
            name_lbl.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {HEADER_COLOR};"
            )
            card_layout.addWidget(name_lbl)

            user_lbl = QLabel(
                f"Ваш ответ: <span style='color:#C62828; font-weight: bold;'>"
                f"{err['user'] or '—'}</span>"
            )
            user_lbl.setStyleSheet(f"font-size: 15px; color: {TEXT_COLOR};")
            card_layout.addWidget(user_lbl)

            correct_lbl = QLabel(
                f"Правильно: <span style='color:#2E7D32; font-weight: bold;'>"
                f"{err['correct']}</span>"
            )
            correct_lbl.setStyleSheet(f"font-size: 15px; color: {TEXT_COLOR};")
            card_layout.addWidget(correct_lbl)

            inner_layout.addWidget(card)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(48)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
