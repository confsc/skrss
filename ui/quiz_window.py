from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import random
from logic.data_loader import load_stations
from ui.quiz_dialog import QuizDialog


class StationListTab(QWidget):

    def __init__(self):
        super().__init__()
        self.stations = load_stations()

        layout = QVBoxLayout(self)

        title = QLabel("<h3>Выберите станцию для контроля</h3>")
        layout.addWidget(title)
        layout.addWidget(QLabel("Двойной клик по станции — начать контроль (7 вопросов)"))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.start_control)

        radio = [s for s in self.stations if s["category"] == "radio"]
        satellite = [s for s in self.stations if s["category"] == "satellite"]

        header_radio = QListWidgetItem("── РАДИОРЕЛЕЙНЫЕ СТАНЦИИ ──")
        header_radio.setFlags(Qt.NoItemFlags)
        header_radio.setForeground(Qt.darkGreen)
        f = QFont()
        f.setBold(True)
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

        dialog = QuizDialog(station, self, count=7, is_control=True)
        dialog.exec_()


class RandomStationTab(QWidget):

    def __init__(self):
        super().__init__()
        self.stations = load_stations()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("<h2>Контроль по всем станциям</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QLabel(
            "Программа выберет случайную станцию из всех 28.\n"
            "Вам будет предложено 7 вопросов:\n"
            "3 ключевых + 4 случайных."
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(info)

        layout.addSpacing(40)

        btn = QPushButton("🎲 Начать контроль по случайной станции")
        btn.setFixedSize(500, 80)
        btn.setStyleSheet(
            "QPushButton { font-size: 16px; background-color: #2196F3; "
            "color: white; border-radius: 15px; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
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
        dialog = QuizDialog(station, self, count=7, is_control=True)
        dialog.exec_()


class QuizWindow(QMainWindow):

    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback

        self.setWindowTitle("Режим контроля")
        self.resize(900, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад на стартовый экран")
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        tabs = QTabWidget()
        tabs.addTab(StationListTab(), "Контроль по станциям")
        tabs.addTab(RandomStationTab(), "Контроль по всем станциям")
        layout.addWidget(tabs)

    def go_back(self):
        self.back_callback()
        self.close()
