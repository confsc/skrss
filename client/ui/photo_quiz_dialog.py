"""
Диалог фото-контроля (определение станции по внешнему виду).
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy, QMessageBox, QFrame,
    QRadioButton, QButtonGroup, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QCursor

from logic.data_loader import resource_path, get_cached_pixmap
from ui.result_dialog import ResultDialog

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
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

        self.setWindowTitle("Визуальный контроль: Распознавание станций")
        self.resize(1050, 850)
        self.setMinimumSize(850, 600)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(14)

        # Верхняя плашка
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

        badge_lbl = QLabel(make_badge_html("Визуальное распознавание", COLOR_PRIMARY_PALE, COLOR_PRIMARY_DARK))
        badge_lbl.setStyleSheet("border: none;")
        title_col.addWidget(badge_lbl)

        title = QLabel(f"Определите комплекс по внешнему виду ({len(self.photo_specs)} вопросов)")
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 19px; font-weight: 700; border: none;")
        title_col.addWidget(title)

        h_layout.addLayout(title_col)
        h_layout.addStretch()

        if self.time_limit > 0:
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

        # Область прокрутки с фото-вопросами
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1.5px solid {COLOR_BORDER}; border-radius: 12px; background-color: {COLOR_CARD_BG}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {COLOR_CARD_BG};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(18, 16, 18, 16)
        inner_layout.setSpacing(16)

        for idx, photo in enumerate(self.photo_specs):
            self._add_photo_question(inner_layout, idx, photo)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        main_layout.addWidget(scroll)

        # Кнопки
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
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #F8FAFC;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 14, 18, 14)
        c_layout.setSpacing(10)

        header_row = QHBoxLayout()
        q_title = QLabel(f"Вопрос №{idx + 1}: {photo.get('question', 'Какая станция изображена на фотографии?')}")
        q_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLOR_PRIMARY_DARK}; border: none;")
        header_row.addWidget(q_title)
        header_row.addStretch()

        res_lbl = QLabel("")
        res_lbl.setStyleSheet("font-size: 18px; font-weight: 700; border: none;")
        self.photo_result_labels[idx] = res_lbl
        header_row.addWidget(res_lbl)
        c_layout.addLayout(header_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # Фото в рамке
        img_frame = QFrame()
        img_frame.setStyleSheet(f"background-color: #FFFFFF; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        f_layout = QVBoxLayout(img_frame)
        f_layout.setContentsMargins(6, 6, 6, 6)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(200)
        image_label.setMinimumWidth(320)
        image_label.setStyleSheet("border: none; background: transparent;")

        pix = get_cached_pixmap(photo.get("image", ""))
        if pix and not pix.isNull():
            image_label.setPixmap(pix.scaled(380, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            image_label.setText("📷 Фотография отсутствует")
            image_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; border: none;")

        f_layout.addWidget(image_label)
        content_row.addWidget(img_frame, 1)

        # Варианты ответа (Radio buttons)
        options_col = QVBoxLayout()
        options_col.setSpacing(8)
        btn_group = QButtonGroup(self)

        for opt_idx, option in enumerate(photo.get("options", [])):
            radio = QRadioButton(option)
            radio.setCursor(QCursor(Qt.PointingHandCursor))
            radio.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 14px;
                    font-weight: 500;
                    color: {COLOR_TEXT_PRIMARY};
                    padding: 8px 12px;
                    background-color: #FFFFFF;
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 8px;
                }}
                QRadioButton:hover {{
                    border-color: {COLOR_PRIMARY_HOVER};
                    background-color: {COLOR_PRIMARY_PALE};
                }}
                QRadioButton:checked {{
                    border: 2px solid {COLOR_PRIMARY};
                    font-weight: 700;
                    color: {COLOR_PRIMARY_DARK};
                    background-color: {COLOR_PRIMARY_PALE};
                }}
            """)
            btn_group.addButton(radio, opt_idx)
            options_col.addWidget(radio)

        options_col.addStretch()
        content_row.addLayout(options_col, 1)
        c_layout.addLayout(content_row)

        self.photo_groups[idx] = btn_group
        parent_layout.addWidget(card)

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
            correct = photo.get("correct_answer", "")
            group = self.photo_groups.get(idx)
            if not group:
                continue
            for btn in group.buttons():
                if btn.text().strip().lower() == correct.strip().lower():
                    btn.setChecked(True)
                    break

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
                    self, "Сервер недоступен",
                    "Связь с сервером преподавателя потеряна.\n\nРабота остановлена."
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
                self, "Контроль завершён",
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
        correct_count = 0
        total = len(self.photo_specs)

        for idx, photo in enumerate(self.photo_specs):
            group = self.photo_groups.get(idx)
            selected_btn = group.checkedButton() if group else None
            user_ans = selected_btn.text().strip() if selected_btn else ""
            correct_ans = photo.get("correct_answer", "").strip()

            if user_ans and user_ans.lower() == correct_ans.lower():
                correct_count += 1
                if idx in self.photo_result_labels:
                    self.photo_result_labels[idx].setText("✔")
                    self.photo_result_labels[idx].setStyleSheet(f"color: {COLOR_SUCCESS};")
            else:
                errors.append({
                    "name": f"Вопрос №{idx + 1} ({photo.get('station_name', 'Станция')})",
                    "user": user_ans if user_ans else "Не выбран",
                    "correct": correct_ans,
                })
                if idx in self.photo_result_labels:
                    self.photo_result_labels[idx].setText("✘")
                    self.photo_result_labels[idx].setStyleSheet(f"color: {COLOR_DANGER};")

        percent = (correct_count / total * 100) if total > 0 else 0
        grade = _percent_to_grade(percent)

        self.result_data = {
            "correct_count": correct_count,
            "total": total,
            "percent": percent,
            "grade": grade,
            "errors": errors,
        }

        if self.api_client and self.student_id:
            duration = self.time_limit - max(0, self.remaining)
            self.api_client.finish_quiz(
                self.student_id, correct_count, float(correct_count), percent, duration
            )

        dialog = ResultDialog(
            station_name="Фото-контроль станций",
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
