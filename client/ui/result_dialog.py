"""
?????????? ???? ??????????? ??????????? ???????????? / ????????.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_SUCCESS_BG, COLOR_WARNING, COLOR_WARNING_BG,
    COLOR_DANGER, COLOR_DANGER_BG, BTN_PRIMARY_STYLE, BTN_SECONDARY_STYLE,
    make_badge_html
)


def _percent_to_grade(percent):
    if percent >= 90:
        return 5, "???????", COLOR_SUCCESS, COLOR_SUCCESS_BG
    if percent >= 70:
        return 4, "??????", "#15803D", "#DCFCE7"
    if percent >= 50:
        return 3, "?????????????????", COLOR_WARNING, COLOR_WARNING_BG
    return 2, "?? ???????", COLOR_DANGER, COLOR_DANGER_BG


class ResultDialog(QDialog):

    def __init__(self, station_name, correct, total, percent, errors, is_control=False):
        super().__init__()
        self.setWindowTitle("?????????? ???????? ??????")
        self.setFixedSize(560, 560)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        self.errors = errors
        grade, grade_text, grade_color, grade_bg = _percent_to_grade(percent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(16)

        # ??????? ???????? ???????????
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        # ????? ? ???????
        mode_str = "?????????? / ????? ????????" if is_control else "???????????? ??????"
        mode_lbl = QLabel(mode_str)
        mode_lbl.setAlignment(Qt.AlignCenter)
        mode_lbl.setStyleSheet(f"color: {COLOR_PRIMARY}; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; border: none;")
        card_layout.addWidget(mode_lbl)

        station_lbl = QLabel(station_name if station_name else "???????? ????")
        station_lbl.setAlignment(Qt.AlignCenter)
        station_lbl.setWordWrap(True)
        station_lbl.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 18px; font-weight: 700; border: none;")
        card_layout.addWidget(station_lbl)

        # ??????????? ???? ??????
        grade_box = QFrame()
        grade_box.setStyleSheet(f"""
            QFrame {{
                background-color: {grade_bg};
                border: 2px solid {grade_color};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        g_layout = QVBoxLayout(grade_box)
        g_layout.setAlignment(Qt.AlignCenter)
        g_layout.setSpacing(2)

        grade_num = QLabel(str(grade))
        grade_num.setAlignment(Qt.AlignCenter)
        grade_num.setStyleSheet(f"color: {grade_color}; font-size: 54px; font-weight: 800; border: none;")
        g_layout.addWidget(grade_num)

        verdict_lbl = QLabel(grade_text)
        verdict_lbl.setAlignment(Qt.AlignCenter)
        verdict_lbl.setStyleSheet(f"color: {grade_color}; font-size: 14px; font-weight: 700; border: none; letter-spacing: 1px;")
        g_layout.addWidget(verdict_lbl)

        card_layout.addWidget(grade_box)

        # ??????????: ????? ? ????????
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        # ?????? ?????????? ???????
        box_score = QFrame()
        box_score.setStyleSheet(f"background-color: #F8FAFC; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 8px;")
        bs_layout = QVBoxLayout(box_score)
        bs_layout.setAlignment(Qt.AlignCenter)
        bs_val = QLabel(f"{correct} ?? {total}")
        bs_val.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; border: none;")
        bs_lbl = QLabel("?????????? ???????")
        bs_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; border: none;")
        bs_layout.addWidget(bs_val, 0, Qt.AlignCenter)
        bs_layout.addWidget(bs_lbl, 0, Qt.AlignCenter)
        stats_layout.addWidget(box_score)

        # ?????? ?????????
        box_percent = QFrame()
        box_percent.setStyleSheet(f"background-color: #F8FAFC; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 8px;")
        bp_layout = QVBoxLayout(box_percent)
        bp_layout.setAlignment(Qt.AlignCenter)
        bp_val = QLabel(f"{percent:.1f}%")
        bp_val.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY_DARK}; border: none;")
        bp_lbl = QLabel("??????? ??????????")
        bp_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; border: none;")
        bp_layout.addWidget(bp_val, 0, Qt.AlignCenter)
        bp_layout.addWidget(bp_lbl, 0, Qt.AlignCenter)
        stats_layout.addWidget(box_percent)

        card_layout.addLayout(stats_layout)
        layout.addWidget(card)

        # ??????
        btns = QHBoxLayout()
        btns.setSpacing(12)

        if errors:
            err_btn = QPushButton(f"?????? ?????? ({len(errors)})")
            err_btn.setCursor(QCursor(Qt.PointingHandCursor))
            err_btn.setMinimumHeight(44)
            err_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FEF2F2;
                    color: {COLOR_DANGER};
                    font-size: 14px;
                    font-weight: 600;
                    border: 1.5px solid #FECACA;
                    border-radius: 8px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: #FEE2E2;
                }}
            """)
            err_btn.clicked.connect(self.show_errors)
            btns.addWidget(err_btn, 1)

        close_btn = QPushButton("?????????")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn, 1)

        layout.addLayout(btns)

    def show_errors(self):
        ErrorsDialog(self.errors, parent=self).exec_()


class ErrorsDialog(QDialog):

    def __init__(self, errors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("????????? ?????? ?????????? ??????")
        self.resize(720, 580)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"?????? ???????? ??????? (?????: {len(errors)})")
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1.5px solid {COLOR_BORDER}; border-radius: 10px; background-color: {COLOR_CARD_BG}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {COLOR_CARD_BG};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(10)
        inner_layout.setContentsMargins(14, 14, 14, 14)

        for i, err in enumerate(errors, 1):
            err_card = QFrame()
            err_card.setStyleSheet(f"""
                QFrame {{
                    background-color: #FFF5F5;
                    border: 1px solid #FED7D7;
                    border-left: 4px solid {COLOR_DANGER};
                    border-radius: 6px;
                }}
            """)
            c_layout = QVBoxLayout(err_card)
            c_layout.setContentsMargins(14, 10, 14, 10)
            c_layout.setSpacing(4)

            name_lbl = QLabel(f"{i}. {err['name']}")
            name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; border: none;")
            c_layout.addWidget(name_lbl)

            ans_row = QHBoxLayout()
            ans_row.setSpacing(16)

            user_lbl = QLabel(f"??? ?????: <span style='color:{COLOR_DANGER}; font-weight:600;'>{err['user'] or '-'}</span>")
            user_lbl.setStyleSheet("font-size: 13px; border: none;")
            ans_row.addWidget(user_lbl)

            corr_lbl = QLabel(f"?????????: <span style='color:{COLOR_SUCCESS}; font-weight:700;'>{err['correct']}</span>")
            corr_lbl.setStyleSheet("font-size: 13px; border: none;")
            ans_row.addWidget(corr_lbl)
            ans_row.addStretch()

            c_layout.addLayout(ans_row)
            inner_layout.addWidget(err_card)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        close_btn = QPushButton("???????, ???????")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(160)
        close_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)
