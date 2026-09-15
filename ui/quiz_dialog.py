from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox
)
from logic.scoring import check_answer, get_key_specs


class QuizDialog(QDialog):
    """Мини-контроль по одной станции — 5 ключевых ТТХ."""

    def __init__(self, station, parent=None):
        super().__init__(parent)
        self.station = station
        self.specs = get_key_specs(station, count=5)   # 5 ключевых
        self.inputs = {}

        self.setWindowTitle(f"Входной контроль: {station['name']}")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        title = QLabel(f"<h3>Входной контроль: {station['name']}</h3>")
        layout.addWidget(title)

        layout.addWidget(QLabel("Заполните ключевые ТТХ:"))

        for spec in self.specs:
            row = QHBoxLayout()
            label = QLabel(f"{spec['name']}:")
            label.setMinimumWidth(250)
            row.addWidget(label)

            if spec["type"] == "choice":
                widget = QComboBox()
                widget.addItem("")
                for opt in spec.get("options", []):
                    widget.addItem(opt)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("Введите значение...")

            self.inputs[spec["name"]] = widget
            row.addWidget(widget)

            if spec.get("unit"):
                row.addWidget(QLabel(spec["unit"]))

            layout.addLayout(row)

        layout.addStretch()

        btns = QHBoxLayout()
        check_btn = QPushButton("Проверить")
        check_btn.clicked.connect(self.check)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(check_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def check(self):
        errors = []
        total = len(self.specs)

        for spec in self.specs:
            widget = self.inputs[spec["name"]]
            if isinstance(widget, QComboBox):
                user_answer = widget.currentText()
            else:
                user_answer = widget.text().strip()

            if not check_answer(spec, user_answer):
                unit = f" {spec['unit']}" if spec.get("unit") else ""
                errors.append(
                    f"• {spec['name']}: вы ввели «{user_answer or '—'}», "
                    f"правильно «{spec['answer']}{unit}»"
                )

        if not errors:
            self.accept()
        else:
            correct = total - len(errors)
            QMessageBox.warning(
                self, "Контроль не пройден",
                f"Правильных ответов: {correct} из {total}.\n\n"
                f"Ошибки:\n" + "\n".join(errors) +
                "\n\nПовторите обучение и попробуйте снова."
            )
