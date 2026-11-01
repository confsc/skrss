"""
Диалог тестирования по характеристикам (ТТХ).
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGridLayout, QScrollArea, QWidget,
    QSizePolicy, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QCursor

from logic.scoring import check_answer, get_key_specs, get_quiz_specs, get_unit_options
from ui.result_dialog import ResultDialog

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
    BTN_PRIMARY_STYLE, BTN_SECONDARY_STYLE, make_badge_html
)

HEARTBEAT_INTERVAL = 30
STOP_CHECK_INTERVAL = 3
SERVER_CHECK_INTERVAL = 5

MASTER_MODIFIERS = Qt.ControlModifier | Qt.ShiftModifier
MASTER_KEY = Qt.Key_F1


def _percent_to_grade(percent):
    if percent >= 90:
        return 5
    if percent >= 70:
        return 4
    if percent >= 50:
        return 3
    return 2


class QuizDialog(QDialog):

    def __init__(self, station=None, parent=None,
                 station_id=None, station_name=None,
                 specs=None, time_limit=None, student_id=None,
                 api_client=None, fio=None, group_name=None,
                 is_control=False, is_server_mode=False):

        super().__init__(parent)

        self.is_control = is_control
        self.is_server_mode = is_server_mode
        self.api_client = api_client
        self.student_id = student_id
        self.fio = fio
        self.group_name = group_name

        self.result_data = None

        if is_server_mode:
            self.station = {"id": station_id, "name": station_name, "specs": specs}
            self.specs = specs
            self.setWindowTitle(f"Контроль: {station_name}")
        else:
            self.station = station
            if is_control:
                self.specs = get_quiz_specs(station)
                self.setWindowTitle(f"Контроль: {station['name']}")
            else:
                self.specs = get_key_specs(station)
                self.setWindowTitle(f"Входной контроль: {station['name']}")

        self.inputs = {}
        self.unit_inputs = {}
        self.result_labels = {}
        self.remaining = time_limit or 0
        self.time_limit = time_limit or 0
        self.finished = False
        self.forced_stop = False
        self.fail_count = 0

        self.resize(1150, 820)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(14)

        # Верхняя информационная панель (Заголовок, инфо и таймер)
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 12px;
                padding: 12px 18px;
            }}
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        mode_badge = "Сетевой контроль" if is_server_mode else ("Контроль знаний" if is_control else "Самопроверка")
        badge_lbl = QLabel(make_badge_html(mode_badge, COLOR_PRIMARY_PALE, COLOR_PRIMARY_DARK))
        badge_lbl.setStyleSheet("border: none;")
        title_col.addWidget(badge_lbl)

        st_title = self.station.get("name", "Тест")
        title = QLabel(f"Станция: {st_title}")
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 20px; font-weight: 700; border: none;")
        title_col.addWidget(title)

        h_layout.addLayout(title_col)
        h_layout.addStretch()

        if is_server_mode and self.time_limit > 0:
            self.timer_label = QLabel(f"⏱ {self._fmt_time(self.time_limit)}")
            self.timer_label.setStyleSheet(f"""
                color: #FFFFFF;
                background-color: {COLOR_PRIMARY};
                font-size: 18px;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            """)
            h_layout.addWidget(self.timer_label)

        main_layout.addWidget(header_card)

        # Подсказка
        hint_text = (
            "Заполните параметры станции. Для величин укажите числовое значение и выберите единицу измерения."
            if is_server_mode or is_control else
            "Самостоятельно проверьте знание основных тактико-технических характеристик (ТТХ)."
        )
        hint = QLabel(f"💡 {hint_text}")
        hint.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; padding-left: 4px;")
        main_layout.addWidget(hint)

        # Область прокрутки с карточками вопросов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1.5px solid {COLOR_BORDER}; border-radius: 12px; background-color: {COLOR_CARD_BG}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {COLOR_CARD_BG};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(18, 16, 18, 16)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)

        LABEL_MIN = 280
        UNIT_MIN = 160
        RESULT_MIN = 45

        HEADER_STYLE = f"""
            color: #FFFFFF;
            background-color: {COLOR_PRIMARY_DARK};
            font-size: 13px;
            font-weight: 600;
            padding: 8px 12px;
            border-radius: 6px;
        """

        header_name = QLabel("Характеристика / Вопрос")
        header_name.setStyleSheet(HEADER_STYLE)
        header_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_name.setMinimumWidth(LABEL_MIN)
        grid.addWidget(header_name, 0, 0)

        header_val = QLabel("Значение ответа")
        header_val.setStyleSheet(HEADER_STYLE)
        header_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(header_val, 0, 1)

        header_unit = QLabel("Единица измерения")
        header_unit.setStyleSheet(HEADER_STYLE)
        header_unit.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_unit.setMinimumWidth(UNIT_MIN)
        grid.addWidget(header_unit, 0, 2)

        header_res = QLabel("Статус")
        header_res.setStyleSheet(HEADER_STYLE)
        header_res.setAlignment(Qt.AlignCenter)
        header_res.setMinimumWidth(RESULT_MIN)
        grid.addWidget(header_res, 0, 3)

        for row_idx, spec in enumerate(self.specs, start=1):
            label = QLabel(f"{spec['name']}:")
            label.setWordWrap(True)
            label.setMinimumWidth(LABEL_MIN)
            label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(label, row_idx, 0)

            spec_type = spec.get("type", "text")

            if spec_type == "choice":
                widget = QComboBox()
                widget.addItem("")
                for opt in spec.get("options", []):
                    widget.addItem(opt)
                widget.setMinimumHeight(38)
                self.inputs[spec["name"]] = widget
                grid.addWidget(widget, row_idx, 1)

                empty_unit = QLabel("—")
                empty_unit.setAlignment(Qt.AlignCenter)
                empty_unit.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
                empty_unit.setMinimumWidth(UNIT_MIN)
                grid.addWidget(empty_unit, row_idx, 2)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText("Введите ответ...")
                widget.setMinimumHeight(38)
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
                        unit_widget.setMinimumHeight(38)
                        self.unit_inputs[spec["name"]] = unit_widget
                        grid.addWidget(unit_widget, row_idx, 2)
                    else:
                        empty_unit = QLabel("—")
                        empty_unit.setAlignment(Qt.AlignCenter)
                        empty_unit.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
                        empty_unit.setMinimumWidth(UNIT_MIN)
                        grid.addWidget(empty_unit, row_idx, 2)
                else:
                    empty_unit = QLabel("—")
                    empty_unit.setAlignment(Qt.AlignCenter)
                    empty_unit.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
                    empty_unit.setMinimumWidth(UNIT_MIN)
                    grid.addWidget(empty_unit, row_idx, 2)

            result_lbl = QLabel("•")
            result_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px;")
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

        # Нижние кнопки управления
        btns = QHBoxLayout()
        btns.setSpacing(12)

        cancel_btn = QPushButton("Прервать и выйти")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setMinimumWidth(150)
        cancel_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        btns.addStretch()

        self.check_btn = QPushButton("Завершить и проверить →")
        self.check_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_btn.setMinimumHeight(44)
        self.check_btn.setMinimumWidth(220)
        self.check_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.check_btn.clicked.connect(self.check)
        btns.addWidget(self.check_btn)

        main_layout.addLayout(btns)

        # Таймеры
        if is_server_mode and self.time_limit > 0:
            self.timer = QTimer()
            self.timer.timeout.connect(self.tick)
            self.timer.start(1000)

        if is_server_mode and self.api_client:
            self.heartbeat_timer = QTimer()
            self.heartbeat_timer.timeout.connect(self.send_heartbeat)
            self.heartbeat_timer.start(HEARTBEAT_INTERVAL * 1000)
            self.send_heartbeat()

            self.stop_check_timer = QTimer()
            self.stop_check_timer.timeout.connect(self.check_if_stopped)
            self.stop_check_timer.start(STOP_CHECK_INTERVAL * 1000)

            self.server_check_timer = QTimer()
            self.server_check_timer.timeout.connect(self.check_server)
            self.server_check_timer.start(SERVER_CHECK_INTERVAL * 1000)

    def keyPressEvent(self, event):
        if (
            (self.is_control or self.is_server_mode)
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

    def send_heartbeat(self):
        if self.api_client:
            self.api_client.heartbeat(
                student_id=self.student_id,
                fio=self.fio,
                group_name=self.group_name,
            )

    def check_server(self):
        if self.finished:
            return
        if not self.api_client:
            return

        if self.api_client.ping():
            self.fail_count = 0
        else:
            self.fail_count += 1
            if self.fail_count >= 3:
                self.forced_stop = True
                self.stop_all_timers()
                self.finished = True
                QMessageBox.warning(
                    self,
                    "Сервер недоступен",
                    "Связь с сервером преподавателя потеряна.\n\nТестирование прервано."
                )
                self.reject()

    def check_if_stopped(self):
        if self.finished:
            return
        if not self.api_client:
            return

        try:
            info = self.api_client.quiz_info()
        except Exception:
            return

        if not info.get("active"):
            self.forced_stop = True
            self.stop_all_timers()
            self.finished = True
            QMessageBox.warning(
                self,
                "Контроль остановлен",
                "Контроль был завершён преподавателем.\n\nТестирование закрывается."
            )
            self.reject()

    def stop_all_timers(self):
        for name in [
            "timer", "heartbeat_timer", "stop_check_timer", "server_check_timer"
        ]:
            t = getattr(self, name, None)
            if t is not None:
                try:
                    t.stop()
                except Exception:
                    pass

    def _fmt_time(self, sec):
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"

    def tick(self):
        self.remaining -= 1
        self.timer_label.setText(f"⏱ {self._fmt_time(max(0, self.remaining))}")

        if self.remaining <= 60 and self.remaining > 10:
            self.timer_label.setStyleSheet(f"""
                color: #FFFFFF;
                background-color: {COLOR_WARNING};
                font-size: 18px;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
            """)
        elif self.remaining <= 10:
            self.timer_label.setStyleSheet(f"""
                color: #FFFFFF;
                background-color: {COLOR_DANGER};
                font-size: 18px;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
            """)

        if self.remaining <= 0:
            self.timer.stop()
            self.time_out()

    def time_out(self):
        if self.finished:
            return
        self.finished = True
        QMessageBox.warning(self, "Время вышло", "Время тестирования истекло. Ответы отправляются на проверку.")
        self.check(auto=True)

    def check(self, auto=False):
        if self.finished and not auto:
            return
        self.finished = True
        self.stop_all_timers()

        errors = []
        total_score = 0.0
        max_score = 0.0
        correct_count = 0

        for spec in self.specs:
            widget = self.inputs[spec["name"]]
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
                correct_count += 1
                self.result_labels[spec["name"]].setText("✔")
                self.result_labels[spec["name"]].setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 20px; font-weight: bold;")
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
                self.result_labels[spec["name"]].setText("✘")
                self.result_labels[spec["name"]].setStyleSheet(f"color: {COLOR_DANGER}; font-size: 20px; font-weight: bold;")

        percent = (total_score / max_score * 100) if max_score > 0 else 0
        grade = _percent_to_grade(percent)

        self.result_data = {
            "correct_count": correct_count,
            "total": len(self.specs),
            "percent": percent,
            "grade": grade,
            "errors": errors,
        }

        if self.is_server_mode and self.api_client and self.student_id:
            duration = self.time_limit - max(0, self.remaining)
            self.api_client.finish_quiz(
                self.student_id, correct_count, total_score, percent, duration
            )

        dialog = ResultDialog(
            station_name=self.station.get("name", ""),
            correct=correct_count,
            total=len(self.specs),
            percent=percent,
            errors=errors,
            is_control=self.is_control or self.is_server_mode,
        )
        dialog.exec_()
        self.accept()

    def closeEvent(self, event):
        if not self.finished and self.api_client and self.fio and self.group_name:
            try:
                self.api_client.disconnect(self.fio, self.group_name)
            except Exception:
                pass
        self.stop_all_timers()
        super().closeEvent(event)

    def reject(self):
        if not self.finished and self.api_client and self.fio and self.group_name:
            try:
                self.api_client.disconnect(self.fio, self.group_name)
            except Exception:
                pass
        self.stop_all_timers()
        super().reject()
