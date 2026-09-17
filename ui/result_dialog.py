from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt


class ResultDialog(QDialog):

    def __init__(self, station_name, correct, total, percent, errors, is_control=False):
        super().__init__()
        self.setWindowTitle("Результат")
        self.setFixedSize(520, 480)

        self.errors = errors

        if percent >= 90:
            grade = "ОТЛИЧНО"
            grade_icon = "✔"
            grade_color = "#2e7d32"
        elif percent >= 75:
            grade = "ХОРОШО"
            grade_icon = "✔"
            grade_color = "#388e3c"
        elif percent >= 60:
            grade = "УДОВЛЕТВОРИТЕЛЬНО"
            grade_icon = "!"
            grade_color = "#f57c00"
        else:
            grade = "НЕУДОВЛЕТВОРИТЕЛЬНО"
            grade_icon = "✘"
            grade_color = "#c62828"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        if is_control:
            header = QLabel("РЕЖИМ КОНТРОЛЯ")
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("color: #666; font-size: 12px; letter-spacing: 2px;")
            layout.addWidget(header)

        station_label = QLabel(station_name)
        station_label.setAlignment(Qt.AlignCenter)
        station_label.setStyleSheet("color: #333; font-size: 14px;")
        layout.addWidget(station_label)

        grade_label = QLabel(f"{grade_icon}  {grade}")
        grade_label.setAlignment(Qt.AlignCenter)
        grade_label.setStyleSheet(
            f"color: {grade_color}; font-size: 28px; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(grade_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        count_label = QLabel(f"Правильных ответов: <b>{correct}</b> из <b>{total}</b>")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(count_label)

        percent_label = QLabel(f"{percent:.1f}%")
        percent_label.setAlignment(Qt.AlignCenter)
        percent_label.setFixedHeight(80)
        percent_label.setStyleSheet(
            f"background-color: {grade_color}; color: white; "
            f"font-size: 36px; font-weight: bold; border-radius: 15px;"
        )
        layout.addWidget(percent_label)

        layout.addStretch()

        if not errors:
            msg = QLabel("🎉 Все ответы верны!")
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("font-size: 15px; color: #2e7d32;")
            layout.addWidget(msg)
        else:
            msg = QLabel(f"Ошибок: {len(errors)}")
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("font-size: 15px; color: #c62828;")
            layout.addWidget(msg)

        btns = QHBoxLayout()
        btns.addStretch()

        if errors:
            err_btn = QPushButton("Показать ошибки")
            err_btn.setFixedHeight(40)
            err_btn.setStyleSheet(
                "QPushButton { background-color: #2196F3; color: white; "
                "font-size: 14px; padding: 0 20px; border-radius: 8px; }"
                "QPushButton:hover { background-color: #1976D2; }"
            )
            err_btn.clicked.connect(self.show_errors)
            btns.addWidget(err_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #757575; color: white; "
            "font-size: 14px; padding: 0 20px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #616161; }"
        )
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
        self.resize(650, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"<h2>Найдено ошибок: {len(errors)}</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(12)

        for i, err in enumerate(errors, 1):
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background-color: #fafafa; "
                "border-left: 4px solid #c62828; border-radius: 6px; }"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)

            name_lbl = QLabel(f"<b>{i}. {err['name']}</b>")
            name_lbl.setStyleSheet("font-size: 14px; color: #333;")
            card_layout.addWidget(name_lbl)

            user_lbl = QLabel(f"Ваш ответ: <span style='color:#c62828;'>{err['user'] or '—'}</span>")
            user_lbl.setStyleSheet("font-size: 13px;")
            card_layout.addWidget(user_lbl)

            correct_lbl = QLabel(f"Правильно: <span style='color:#2e7d32;'>{err['correct']}</span>")
            correct_lbl.setStyleSheet("font-size: 13px;")
            card_layout.addWidget(correct_lbl)

            inner_layout.addWidget(card)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #757575; color: white; "
            "font-size: 14px; border-radius: 8px; }"
            "QPushButton:hover { background-color: #616161; }"
        )
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
