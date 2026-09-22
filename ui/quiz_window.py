from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import random
from logic.data_loader import load_stations
from ui.quiz_dialog import QuizDialog


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"

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


class StationListTab(QWidget):

    def __init__(self):
        super().__init__()
        self.stations = load_stations()
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Выберите станцию для контроля")
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(title)

        hint = QLabel("Двойной клик по станции — начать контроль")
        hint.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 15px;")
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                font-size: 17px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                padding: 8px;
                color: {TEXT_COLOR};
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid #E0E0E0;
                outline: none;
            }}
            QListWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
                font-weight: bold;
                border-radius: 5px;
                border: none;
                outline: none;
            }}
            QListWidget::item:focus {{
                border: none;
                outline: none;
            }}
            QListWidget::item:hover {{
                background-color: #E8F5E9;
            }}
            {SCROLLBAR_STYLE}
        """)
        self.list_widget.itemDoubleClicked.connect(self.start_control)

        radio = [s for s in self.stations if s["category"] == "radio"]
        satellite = [s for s in self.stations if s["category"] == "satellite"]

        f = QFont()
        f.setBold(True)
        f.setPointSize(13)

        header_radio = QListWidgetItem("── РАДИОРЕЛЕЙНЫЕ СТАНЦИИ ──")
        header_radio.setFlags(Qt.NoItemFlags)
        header_radio.setForeground(Qt.darkGreen)
        header_radio.setFont(f)
        self.list_widget.addItem(header_radio)

        for s in radio:
            item = QListWidgetItem("  " + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

        header_sat = QListWidgetItem("── СПУТНИКОВЫЕ СТАНЦИИ ──")
        header_sat.setFlags(Qt.NoItemFlags)
        header_sat.setForeground(Qt.darkBlue)
        header_sat.setFont(f)
        self.list_widget.addItem(header_sat)

        for s in satellite:
            item = QListWidgetItem("  " + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

    def start_control(self, item):
        station_id = item.data(Qt.UserRole)
        if not station_id:
            return

        station = next((s for s in self.stations if s["id"] == station_id), None)
        if not station:
            return

        dialog = QuizDialog(station, self, is_control=True)
        dialog.exec_()


class RandomStationTab(QWidget):

    def __init__(self):
        super().__init__()
        self.stations = load_stations()
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        title = QLabel("Контроль по всем станциям")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 26px; font-weight: bold;"
        )
        layout.addWidget(title)

        info = QLabel(
            "Программа выберет случайную станцию из всех доступных.\n"
            "Количество вопросов зависит от станции (70%, от 7 до 15)."
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"font-size: 16px; color: {TEXT_COLOR}; line-height: 1.6;")
        layout.addWidget(info)

        layout.addSpacing(20)

        btn = QPushButton("🎲  Начать контроль по случайной станции")
        btn.setMinimumSize(550, 90)
        btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 18px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 15px;
                border: none;
                padding: 15px 30px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
        """)
        btn.clicked.connect(self.start_control)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def start_control(self):
        if not self.stations:
            QMessageBox.warning(self, "Ошибка", "Нет станций в базе.")
            return
        station = random.choice(self.stations)
        dialog = QuizDialog(station, self, is_control=True)
        dialog.exec_()


class QuizWindow(QMainWindow):

    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback

        self.setWindowTitle("Режим контроля")
        self.resize(1250, 850)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад на стартовый экран")
        back_btn.setMinimumHeight(48)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {ACCENT_HOVER};
                color: white;
                border-radius: 8px;
                padding: 8px 22px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
            }}
        """)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 10px;
                background-color: {BG_COLOR};
            }}
            QTabBar::tab {{
                background-color: #E8F5E9;
                color: {TEXT_COLOR};
                padding: 20px 30px;
                font-size: 15px;
                font-weight: bold;
                min-width: 280px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_COLOR};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {LIGHT_ACCENT};
            }}
        """)
        self.tabs.addTab(StationListTab(), "Контроль по станциям")
        self.tabs.addTab(RandomStationTab(), "Контроль по всем станциям")
        layout.addWidget(self.tabs)

    def go_back(self):
        self.back_callback()
        self.close()
