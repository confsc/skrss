from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox
)
from logic.scoring import check_answer, get_key_specs, get_quiz_specs


class QuizDialog(QDialog):
    """
    Диалог контроля.
    - В обучении: 5 случайных ТТХ, при успехе — Accepted.
    - В контроле: 7 ТТХ (3 ключевых + 4 случайных), всегда показываем результат.
    """

    def __init__(self, station, parent=None, count=5, is_control=False):
        super().__init__(parent)
        self.station = station
        self.is_control = is_control

        if is_control:
            self.specs = get_quiz_specs(station, total=count, key_count=3)
            self.setWindowTitle(f"Контроль: {station['name']}")
        else:
            self.specs = get_key_specs(station, count=count)
            self.setWindowTitle(f"Входной контроль: {station['name']}")

        self.inputs = {}
        self.resize(650, 600)

        layout = QVBoxLayout(self)

        title = QLabel(f"<h3>{station['name']}</h3>")
        layout.addWidget(title)

        if is_control:
            layout.addWidget(QLabel("Ответьте на вопросы (3 ключевых + 4 дополнительных):"))
        else:
            layout.addWidget(QLabel("Заполните характеристики:"))

        for spec in self.specs:
            row = QHBoxLayout()
            label = QLabel(f"{spec['name']}:")
            label.setMinimumWidth(280)
            label.setWordWrap(True)
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
        cancel_btn = QPushButton("Отмена" if not is_control else "Закрыть")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(check_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def check(self):
        total_score = 0.0
        max_score = 0.0
        errors = []

        for spec in self.specs:
            widget = self.inputs[spec["name"]]
            weight = spec.get("weight", 0.5)
            max_score += weight

            if isinstance(widget, QComboBox):
                user_answer = widget.currentText()
            else:
                user_answer = widget.text().strip()

            if check_answer(spec, user_answer):
                total_score += weight
            else:
                unit = f" {spec['unit']}" if spec.get("unit") else ""
                errors.append(
                    f"• {spec['name']}: «{user_answer or '—'}» "
                    f"вместо «{spec['answer']}{unit}»"
                )

        percent = (total_score / max_score * 100) if max_score > 0 else 0
        correct_count = len(self.specs) - len(errors)

        if self.is_control:
            # Режим контроля — всегда показываем результат и закрываем
            msg = (
                f"Правильных ответов: {correct_count} из {len(self.specs)}\n"
                f"Баллы: {total_score:.1f} из {max_score:.1f} ({percent:.1f}%)"
            )
            if errors:
                msg += "\n\nОшибки:\n" + "\n".join(errors)
            else:
                msg += "\n\n🎉 Все ответы верны!"
            QMessageBox.information(self, "Результат контроля", msg)
            self.accept()
        else:
            # Режим обучения — только при полном успехе
            if not errors:
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Контроль не пройден",
                    f"Правильных ответов: {correct_count} из {len(self.specs)}.\n\n"
                    "Ошибки:\n" + "\n".join(errors) +
                    "\n\nПовторите обучение и попробуйте снова."
                )
