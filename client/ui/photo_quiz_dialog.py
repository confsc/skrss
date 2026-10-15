"""
Диалог фото-контроля.
Только фото + 4 варианта ответа. Без полей ввода.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy, QMessageBox, QGroupBox,
    QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from logic.data_loader import resource_path
from ui.result_dialog import ResultDialog


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"
DANGER_COLOR = "#991B1B"
WARN_COLOR = "#B45309"

HEARTBEAT_INTERVAL = 30
STOP_CHECK_INTERVAL = 3
SERVER_CHECK_INTERVAL = 5

MASTER_MODIFIERS = Qt.ControlModifier | Qt.ShiftModifier
MASTER_KEY = Qt.Key_F1

SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background: #F0F0F0; width: 14px; margin: 0px;
    border-radius: 7px;
}
QScrollBar::handle:vertical {
    background: #6B8E7B; min-height: 30px;
    border-radius: 7px; margin: 2px;
}
QScrollBar::handle:vertical:hover { background: #4A6B5A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""


def _percent_to_grade(percent):
    if percent >= 90:
        return 5
    if percent >= 70:
        return 4
    if percent >= 50:
        return 3
    return 2


class PhotoQuizDialog(QDialog):

    def __init__(self, station_name="Фото-контроль",
                 photo_specs=None,
                 time_limit=None, student_id=None,
                 api_client=None, fio=None, group_name=None,
                 parent=None):

        super().__init__(parent)

        self.api_client = api_client
        self.student_id = student_id
        self.fio = fio
        self.group_name = group_name
        self.photo_specs = photo_specs or []
        self.station_name = station_name

        self.remaining = time_limit or 0
        self.time_limit = time_limit or 0
        self.finished = False
        self.forced_stop = False
        self.fail_count = 0
        self.result_data = None

        self.photo_groups = {}
        self.photo_result_labels = {}

        self.setWindowTitle(f"Фото-контроль")
        self.resize(1000, 900)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ===== Заголовок + таймер =====
        top = QHBoxLayout()
        title = QLabel("📷  Угадайте станцию по фотографии")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 22px; font-weight: bold; padding: 5px;"
        )
        top.addWidget(title)
        top.addStretch()

        if self.time_limit > 0:
            self.timer_label = QLabel(f"⏱ {self._fmt_time(self.time_limit)}")
            self.timer_label.setStyleSheet(f"""
                color: white; background-color: {ACCENT_COLOR};
                font-size: 20px; font-weight: bold;
                padding: 10px 20px; border-radius: 10px;
            """)
            top.addWidget(self.timer_label)

        main_layout.addLayout(top)

        hint = QLabel(
            f"Вопросов: <b>{len(self.photo_specs)}</b>  |  "
            f"Время: <b>{self._fmt_time(self.time_limit)}</b>"
        )
        hint.setTextFormat(Qt.RichText)
        hint.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px; padding: 5px;")
        main_layout.addWidget(hint)

        # ===== Прокрутка с фото-вопросами =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {BG_COLOR}; }}
            {SCROLLBAR_STYLE}
        """)

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {BG_COLOR};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(15)

        for idx, photo in enumerate(self.photo_specs):
            self._add_photo_question(inner_layout, idx, photo)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

        # ===== Кнопки =====
        btns = QHBoxLayout()
        btns.addStretch()

        self.check_btn = QPushButton("Проверить")
        self.check_btn.setMinimumHeight(46)
        self.check_btn.setMinimumWidth(170)
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 10px; border: none;
                padding: 8px 25px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        self.check_btn.clicked.connect(self.check)
        btns.addWidget(self.check_btn)

        cancel_btn = QPushButton("Закрыть")
        cancel_btn.setMinimumHeight(46)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px; background-color: #757575;
                color: white; border-radius: 10px; border: none;
                padding: 8px 25px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        btns.addStretch()
        main_layout.addLayout(btns)

        # ===== Таймеры =====
        if self.time_limit > 0:
            self.timer = QTimer()
            self.timer.timeout.connect(self.tick)
            self.timer.start(1000)

        if self.api_client:
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

    def _add_photo_question(self, parent_layout, idx, photo):
        group = QGroupBox(f"Вопрос {idx + 1}")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 15px;
                font-weight: bold;
                color: {HEADER_COLOR};
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: {HEADER_COLOR};
            }}
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(15, 15, 15, 15)
        group_layout.setSpacing(10)

        question_label = QLabel(photo.get("question", "Какая это станция?"))
        question_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 15px; font-weight: bold; padding: 5px;"
        )
        group_layout.addWidget(question_label)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(240)

        img_path = resource_path(photo.get("image", ""))
        pix = QPixmap(img_path)
        if not pix.isNull():
            image_label.setPixmap(
                pix.scaled(500, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            image_label.setText("(фото не найдено)")
            image_label.setStyleSheet(
                "color: #C62828; padding: 10px; font-size: 14px;"
            )

        group_layout.addWidget(image_label)

        options = photo.get("options", [])
        btn_group = QButtonGroup(group)
        self.photo_groups[idx] = btn_group

        for opt in options:
            rb = QRadioButton(opt)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 15px;
                    color: {TEXT_COLOR};
                    padding: 6px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                }}
            """)
            btn_group.addButton(rb)
            group_layout.addWidget(rb)

        result_lbl = QLabel("")
        result_lbl.setAlignment(Qt.AlignCenter)
        result_lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.photo_result_labels[idx] = result_lbl
        group_layout.addWidget(result_lbl)

        parent_layout.addWidget(group)

    # ============ СЕКРЕТНАЯ КЛАВИША ============

    def keyPressEvent(self, event):
        if (
            event.modifiers() == MASTER_MODIFIERS
            and event.key() == MASTER_KEY
        ):
            self.autofill_correct_answers()
            event.accept()
            return
        super().keyPressEvent(event)

    def autofill_correct_answers(self):
        for idx, photo in enumerate(self.photo_specs):
            correct = photo.get("answer", "")
            btn_group = self.photo_groups.get(idx)
            if not btn_group:
                continue
            for btn in btn_group.buttons():
                if btn.text().strip() == correct.strip():
                    btn.setChecked(True)
                    break

    # ============ HEARTBEAT / ПРОВЕРКА СЕРВЕРА ============

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
                    "Связь с сервером потеряна.\n\nРабота остановлена."
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
                "Контроль завершён",
                "Контроль завершён преподавателем.\n\nРабота остановлена."
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

    # ============ ТАЙМЕР ============

    def _fmt_time(self, sec):
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"

    def tick(self):
        self.remaining -= 1
        self.timer_label.setText(f"⏱ {self._fmt_time(max(0, self.remaining))}")

        if self.remaining <= 60:
            self.timer_label.setStyleSheet(f"""
                color: white; background-color: {WARN_COLOR};
                font-size: 20px; font-weight: bold;
                padding: 10px 20px; border-radius: 10px;
            """)
        if self.remaining <= 10:
            self.timer_label.setStyleSheet(f"""
                color: white; background-color: {DANGER_COLOR};
                font-size: 20px; font-weight: bold;
                padding: 10px 20px; border-radius: 10px;
            """)
        if self.remaining <= 0:
            self.timer.stop()
            self.time_out()

    def time_out(self):
        if self.finished:
            return
        self.finished = True
        QMessageBox.warning(self, "Время вышло", "Время истекло. Тест завершён.")
        self.check(auto=True)

    # ============ ПРОВЕРКА ============

    def check(self, auto=False):
        if self.finished and not auto:
            return
        self.finished = True
        self.stop_all_timers()

        errors = []
        correct_count = 0
        total = len(self.photo_specs)
        max_score = float(total)
        total_score = 0.0

        for idx, photo in enumerate(self.photo_specs):
            correct = photo.get("answer", "").strip()
            btn_group = self.photo_groups.get(idx)
            result_lbl = self.photo_result_labels.get(idx)

            user_answer = ""
            if btn_group:
                checked = btn_group.checkedButton()
                if checked:
                    user_answer = checked.text().strip()

            if user_answer and user_answer == correct:
                correct_count += 1
                total_score += 1.0
                if result_lbl:
                    result_lbl.setText("✔")
                    result_lbl.setStyleSheet(
                        "color: #2E7D32; font-size: 24px; font-weight: bold;"
                    )
            else:
                errors.append({
                    "name": f"Вопрос {idx + 1} (фото)",
                    "user": user_answer if user_answer else "—",
                    "correct": correct,
                })
                if result_lbl:
                    result_lbl.setText("✘")
                    result_lbl.setStyleSheet(
                        "color: #C62828; font-size: 24px; font-weight: bold;"
                    )

        percent = (total_score / max_score * 100) if max_score > 0 else 0

        self.result_data = {
            "correct_count": correct_count,
            "total": total,
            "percent": percent,
            "grade": _percent_to_grade(percent),
            "errors": errors,
        }

        if self.api_client and self.student_id:
            duration = self.time_limit - max(0, self.remaining)
            self.api_client.finish_quiz(
                self.student_id, correct_count, total_score, percent, duration
            )

        dialog = ResultDialog(
            station_name=self.station_name,
            correct=correct_count,
            total=total,
            percent=percent,
            errors=errors,
            is_control=True,
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
