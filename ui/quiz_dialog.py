from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QGridLayout, QWidget
)
from PyQt5.QtCore import Qt
from logic.scoring import check_answer, get_key_specs, get_quiz_specs


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

        # ==== ГЛАВНЫЙ LAYOUT ====
        main_layout = QVBoxLayout(self)

        title = QLabel(f"<h3>{station['name']}</h3>")
        main_layout.addWidget(title)

        if is_control:
            main_layout.addWidget(QLabel("Ответьте на вопросы (3 ключевых + 4 дополнительных):"))
        else:
            main_layout.addWidget(QLabel("Заполните характеристики:"))

        # ==== СЕТКА ВОПРОСОВ ====
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        # Фиксированные ширины колонок
        LABEL_WIDTH = 280
        UNIT_WIDTH = 90
        RESULT_WIDTH = 30

        # Заголовки колонок (опционально)
        # grid.addWidget(QLabel("<b>Характеристика</b>"), 0, 0)
        # grid.addWidget(QLabel("<b>Ответ</b>"), 0, 1)
        # grid.addWidget(QLabel("<b>Ед.</b>"), 0, 2)
        # grid.addWidget(QLabel("<b></b>"), 0, 3)

        for row_idx, spec in enumerate(self.specs):
            # ==== Колонка 1: название ====
            label = QLabel(f"{spec['name']}:")
            label.setWordWrap(True)
            label.setFixedWidth(LABEL_WIDTH)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(label, row_idx, 0)

            # ==== Колонка 2: поле ввода ====
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

            # ==== Колонка 3: единица измерения ====
            unit_text = spec.get("unit", "")
            unit_label = QLabel(unit_text if unit_text else "")
            unit_label.setFixedWidth(UNIT_WIDTH)
            unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(unit_label, row_idx, 2)

            # ==== Колонка 4: индикатор ✔/✘ ====
            result_lbl = QLabel("")
            result_lbl.setFixedWidth(RESULT_WIDTH)
            result_lbl.setAlignment(Qt.AlignCenter)
            self.result_labels[spec["name"]] = result_lbl
            grid.addWidget(result_lbl, row_idx, 3)

        # Пропорции колонок: поле ввода — тянется, остальные фиксированные
        grid.setColumnStretch(0, 0)   # название — фиксировано
        grid.setColumnStretch(1, 1)   # поле ввода — растягивается
        grid.setColumnStretch(2, 0)   # единица — фиксирована
        grid.setColumnStretch(3, 0)   # индикатор — фиксирован

        main_layout.addLayout(grid)
        main_layout.addStretch()

        # ==== КНОПКИ ====
        btns = QHBoxLayout()
        self.check_btn = QPushButton("Проверить")
        self.check_btn.clicked.connect(self.check)
        cancel_btn = QPushButton("Закрыть")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.check_btn)
        btns.addWidget(cancel_btn)
        main_layout.addLayout(btns)

    def check(self):
        all_correct = True

        for spec in self.specs:
            widget = self.inputs[spec["name"]]
            result_lbl = self.result_labels[spec["name"]]

            if isinstance(widget, QComboBox):
                user_answer = widget.currentText()
            else:
                user_answer = widget.text().strip()

            is_ok = check_answer(spec, user_answer)

            if is_ok:
                result_lbl.setText("✔")
                result_lbl.setStyleSheet(
                    "color: green; font-size: 20px; font-weight: bold;"
                )
            else:
                result_lbl.setText("✘")
                result_lbl.setStyleSheet(
                    "color: red; font-size: 20px; font-weight: bold;"
                )
                all_correct = False

        if self.is_control:
            self.show_control_result()
        else:
            if all_correct:
                QMessageBox.information(
                    self, "Отлично!",
                    "Все ответы верны! Станция засчитана как изученная."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Есть ошибки",
                    "Проверьте ответы с красным крестом ✘ и исправьте их.\n"
                    "Затем нажмите «Проверить» ещё раз."
                )

    def show_control_result(self):
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
