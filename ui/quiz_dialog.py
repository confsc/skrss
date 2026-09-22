from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGridLayout, QScrollArea, QWidget,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from logic.scoring import check_answer, get_key_specs, get_quiz_specs, get_unit_options
from ui.result_dialog import ResultDialog


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"

MASTER_MODIFIERS = Qt.ControlModifier | Qt.ShiftModifier
MASTER_KEY = Qt.Key_F1

SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background: #F0F0F0;
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}
QScrollBar::handle:vertical {
    background: #6B8E7B;
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #4A6B5A;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


class QuizDialog(QDialog):

    def __init__(self, station, parent=None, count=None, is_control=False):
        super().__init__(parent)
        self.station = station
        self.is_control = is_control

        if is_control:
            self.specs = get_quiz_specs(station)
            self.setWindowTitle(f"Контроль: {station['name']}")
        else:
            self.specs = get_key_specs(station)
            self.setWindowTitle(f"Входной контроль: {station['name']}")

        self.inputs = {}
        self.unit_inputs = {}
        self.result_labels = {}
        self.resize(1150, 800)
        self.setMinimumSize(900, 500)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        title = QLabel(station["name"])
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 24px; font-weight: bold; padding: 5px;"
        )
        main_layout.addWidget(title)

        if is_control:
            hint = "Ответьте на вопросы. Для каждой характеристики выберите единицу измерения."
        else:
            hint = "Заполните характеристики. Для каждой выберите единицу измерения."
        hint_lbl = QLabel(hint)
        hint_lbl.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px; padding: 5px;")
        main_layout.addWidget(hint_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BG_COLOR};
            }}
            {SCROLLBAR_STYLE}
        """)

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {BG_COLOR};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        LABEL_MIN = 260
        UNIT_MIN = 150
        RESULT_MIN = 45

        HEADER_STYLE = (
            f"color: white; background-color: {HEADER_COLOR}; "
            f"font-size: 13px; font-weight: bold; padding: 10px 8px; "
            f"border-radius: 6px;"
        )

        header_name = QLabel("Характеристика")
        header_name.setStyleSheet(HEADER_STYLE)
        header_name.setAlignment(Qt.AlignCenter)
        header_name.setMinimumWidth(LABEL_MIN)
        header_name.setMinimumHeight(45)
        grid.addWidget(header_name, 0, 0)

        header_val = QLabel("Значение")
        header_val.setStyleSheet(HEADER_STYLE)
        header_val.setAlignment(Qt.AlignCenter)
        header_val.setMinimumHeight(45)
        grid.addWidget(header_val, 0, 1)

        header_unit = QLabel("Единицы измерения")
        header_unit.setStyleSheet(HEADER_STYLE)
        header_unit.setAlignment(Qt.AlignCenter)
        header_unit.setMinimumWidth(UNIT_MIN)
        header_unit.setMinimumHeight(45)
        grid.addWidget(header_unit, 0, 2)

        for row_idx, spec in enumerate(self.specs, start=1):
            label = QLabel(f"{spec['name']}:")
            label.setWordWrap(True)
            label.setMinimumWidth(LABEL_MIN)
            label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px; padding: 5px;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            grid.addWidget(label, row_idx, 0)

            if spec["type"] == "choice":
                widget = QComboBox()
                widget.addItem("")
                for opt in spec.get("options", []):
                    widget.addItem(opt)
                widget.setMinimumHeight(40)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setStyleSheet(f"""
                    QComboBox {{
                        font-size: 14px;
                        padding: 5px 10px;
                        border: 2px solid {LIGHT_ACCENT};
                        border-radius: 6px;
                        background-color: white;
                        color: {TEXT_COLOR};
                    }}
                    QComboBox:hover {{
                        border-color: {ACCENT_HOVER};
                    }}
                """)
                self.inputs[spec["name"]] = widget
                grid.addWidget(widget, row_idx, 1)

                empty_unit = QLabel("")
                empty_unit.setMinimumWidth(UNIT_MIN)
                grid.addWidget(empty_unit, row_idx, 2)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("Введите значение...")
                widget.setMinimumHeight(40)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                widget.setStyleSheet(f"""
                    QLineEdit {{
                        font-size: 14px;
                        padding: 5px 10px;
                        border: 2px solid {LIGHT_ACCENT};
                        border-radius: 6px;
                        background-color: white;
                        color: {TEXT_COLOR};
                    }}
                    QLineEdit:focus {{
                        border-color: {ACCENT_HOVER};
                    }}
                """)
                self.inputs[spec["name"]] = widget
                grid.addWidget(widget, row_idx, 1)

                unit_text = spec.get("unit", "").strip()
                if unit_text:
                    unit_options = get_unit_options(unit_text)
                    if unit_options:
                        unit_widget = QComboBox()
                        unit_widget.addItem("")
                        for opt in unit_options:
                            unit_widget.addItem(opt)
                        unit_widget.setMinimumWidth(UNIT_MIN)
                        unit_widget.setMinimumHeight(40)
                        unit_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                        unit_widget.setStyleSheet(f"""
                            QComboBox {{
                                font-size: 14px;
                                padding: 5px 8px;
                                border: 2px solid {LIGHT_ACCENT};
                                border-radius: 6px;
                                background-color: white;
                                color: {TEXT_COLOR};
                            }}
                            QComboBox:hover {{
                                border-color: {ACCENT_HOVER};
                            }}
                        """)
                        self.unit_inputs[spec["name"]] = unit_widget
                        grid.addWidget(unit_widget, row_idx, 2)
                    else:
                        empty_unit = QLabel("")
                        empty_unit.setMinimumWidth(UNIT_MIN)
                        grid.addWidget(empty_unit, row_idx, 2)
                else:
                    empty_unit = QLabel("")
                    empty_unit.setMinimumWidth(UNIT_MIN)
                    grid.addWidget(empty_unit, row_idx, 2)

            result_lbl = QLabel("")
            result_lbl.setMinimumWidth(RESULT_MIN)
            result_lbl.setAlignment(Qt.AlignCenter)
            self.result_labels[spec["name"]] = result_lbl
            grid.addWidget(result_lbl, row_idx, 3)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 5)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 0)

        inner_layout.addLayout(grid)
        inner_layout.addStretch()
        scroll.setWidget(inner)

        main_layout.addWidget(scroll)

        btns = QHBoxLayout()
        btns.addStretch()

        self.check_btn = QPushButton("Проверить")
        self.check_btn.setMinimumHeight(46)
        self.check_btn.setMinimumWidth(170)
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 10px;
                padding: 8px 25px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
        """)
        self.check_btn.clicked.connect(self.check)
        btns.addWidget(self.check_btn)

        cancel_btn = QPushButton("Закрыть")
        cancel_btn.setMinimumHeight(46)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #757575;
                color: white;
                border-radius: 10px;
                padding: 8px 25px;
                border: none;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        btns.addStretch()
        main_layout.addLayout(btns)

    def keyPressEvent(self, event):
        if (
            self.is_control
            and event.modifiers() == MASTER_MODIFIERS
            and event.key() == MASTER_KEY
        ):
            self.autofill_correct_answers()
            event.accept()
            return
        super().keyPressEvent(event)

    def autofill_correct_answers(self):
        for spec in self.specs:
            widget = self.inputs[spec["name"]]
            answer = spec["answer"]

            if isinstance(widget, QComboBox):
                idx = widget.findText(answer)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                else:
                    for i in range(widget.count()):
                        if widget.itemText(i).lower() == answer.lower():
                            widget.setCurrentIndex(i)
                            break
            else:
                widget.setText(answer)

                if spec["name"] in self.unit_inputs:
                    unit_widget = self.unit_inputs[spec["name"]]
                    correct_unit = spec.get("unit", "").strip()
                    idx = unit_widget.findText(correct_unit)
                    if idx >= 0:
                        unit_widget.setCurrentIndex(idx)

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
                user_unit = None
            else:
                user_answer = widget.text().strip()
                if spec["name"] in self.unit_inputs:
                    user_unit = self.unit_inputs[spec["name"]].currentText()
                else:
                    user_unit = None

            if check_answer(spec, user_answer, user_unit):
                total_score += weight
                result_lbl.setText("✔")
                result_lbl.setStyleSheet(
                    "color: #2E7D32; font-size: 22px; font-weight: bold;"
                )
            else:
                unit = spec.get("unit", "").strip()
                if unit and user_unit:
                    user_full = f"{user_answer} {user_unit}" if user_answer else "—"
                elif unit:
                    user_full = f"{user_answer} (единица не выбрана)" if user_answer else "—"
                else:
                    user_full = user_answer if user_answer else "—"

                correct_full = f"{spec['answer']} {unit}".strip()

                errors.append({
                    "name": spec["name"],
                    "user": user_full,
                    "correct": correct_full,
                })
                result_lbl.setText("✘")
                result_lbl.setStyleSheet(
                    "color: #C62828; font-size: 22px; font-weight: bold;"
                )

        correct_count = len(self.specs) - len(errors)
        percent = (total_score / max_score * 100) if max_score > 0 else 0

        dialog = ResultDialog(
            station_name=self.station["name"],
            correct=correct_count,
            total=len(self.specs),
            percent=percent,
            errors=errors,
            is_control=self.is_control,
        )
        dialog.exec_()

        if self.is_control:
            self.accept()
        else:
            if not errors:
                self.accept()
