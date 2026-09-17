from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGridLayout
)
from PyQt5.QtCore import Qt
from logic.scoring import check_answer, get_key_specs, get_quiz_specs
from ui.result_dialog import ResultDialog


class QuizDialog(QDialog):
    """
    Диалог контроля.
    - В обучении: 5 случайных ТТХ, показываем ✔/✘ напротив каждой.
    - В контроле: 7 ТТХ (3 ключевых + 4 случайных), показываем итог.
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
        self.result_labels = {}
        self.resize(800, 650)

        main_layout = QVBoxLayout(self)

        title = QLabel(f"<h3>{station['name']}</h3>")
        main_layout.addWidget(title)

        if is_control:
            main_layout.addWidget(QLabel("Ответьте на вопросы (3 ключевых + 4 дополнительных):"))
        else:
            main_layout.addWidget(QLabel("Заполните характеристики:"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        LABEL_WIDTH = 280
        UNIT_WIDTH = 90
        RESULT_WIDTH = 30

        for row_idx, spec in enumerate(self.specs):
            label = QLabel(f"{spec['name']}:")
            label.setWordWrap(True)
            label.setFixedWidth(LABEL_WIDTH)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(label, row_idx, 0)

            if spec["type"] == "choice":
                widget = QComboBox()
                widget.addItem("")
                for opt in spec.get("options", []):
                    widget.addItem(opt)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("Введите значение...")

            self.inputs[spec["name"]] = widget
            grid.addWidget(widget, row_idx, 1)

            unit_text = spec.get("unit", "")
            unit_label = QLabel(unit_text if unit_text else "")
            unit_label.setFixedWidth(UNIT_WIDTH)
            unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(unit_label, row_idx, 2)

            result_lbl = QLabel("")
            result_lbl.setFixedWidth(RESULT_WIDTH)
            result_lbl.setAlignment(Qt.AlignCenter)
            self.result_labels[spec["name"]] = result_lbl
            grid.addWidget(result_lbl, row_idx, 3)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 0)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        btns = QHBoxLayout()
        self.check_btn = QPushButton("Проверить")
        self.check_btn.clicked.connect(self.check)
        cancel_btn = QPushButton("Закрыть")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.check_btn)
        btns.addWidget(cancel_btn)
        main_layout.addLayout(btns)

    def check(self):
        errors = []
        total_score = 0.0
        max_score = 0.0

        for spec in self.specs:
            widget = self.inputs[spec["name"]]
            result_lbl = self.result_labels[spec["name"]]
            weight = spec.get("weight", 0.5)
            max_score += weight

            if isinstance(widget, QComboBox):
                user_answer = widget.currentText()
            else:
                user_answer = widget.text().strip()

            if check_answer(spec, user_answer):
                total_score += weight
                result_lbl.setText("✔")
                result_lbl.setStyleSheet(
                    "color: green; font-size: 20px; font-weight: bold;"
                )
            else:
                unit = f" {spec['unit']}" if spec.get("unit") else ""
                errors.append({
                    "name": spec["name"],
                    "user": f"{user_answer}{unit}" if user_answer else "",
                    "correct": f"{spec['answer']}{unit}",
                })
                result_lbl.setText("✘")
                result_lbl.setStyleSheet(
                    "color: red; font-size: 20px; font-weight: bold;"
                )

        correct_count = len(self.specs) - len(errors)
        percent = (total_score / max_score * 100) if max_score > 0 else 0

        # ==== КРАСИВОЕ ОКНО РЕЗУЛЬТАТА ====
        dialog = ResultDialog(
            station_name=self.station["name"],
            correct=correct_count,
            total=len(self.specs),
            percent=percent,
            errors=errors,
            is_control=self.is_control,
        )
        dialog.exec_()

        # ==== ЛОГИКА ЗАКРЫТИЯ ====
        if self.is_control:
            self.accept()
        else:
            if not errors:
                self.accept()
