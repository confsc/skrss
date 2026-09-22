from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QTextEdit, QPushButton, QTabWidget,
    QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from logic.data_loader import load_stations, resource_path
from ui.quiz_dialog import QuizDialog


BG_COLOR = "#FAFAFA"
TEXT_COLOR = "#1B1B1B"
HEADER_COLOR = "#1B4332"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"


class StationListWidget(QWidget):

    def __init__(self, category, parent_window):
        super().__init__()
        self.category = category
        self.parent_window = parent_window
        self.stations = [s for s in load_stations() if s["category"] == category]
        self.studied = parent_window.studied
        self.current_station = None

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left.setStyleSheet(f"background-color: {BG_COLOR};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)

        list_title = QLabel("Выберите станцию:")
        list_title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 19px; font-weight: bold; padding: 5px;"
        )
        left_layout.addWidget(list_title)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                font-size: 17px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                padding: 5px;
                color: {TEXT_COLOR};
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid #E0E0E0;
            }}
            QListWidget::item:selected {{
                background-color: {LIGHT_ACCENT};
                color: {HEADER_COLOR};
                font-weight: bold;
                border-radius: 5px;
            }}
            QListWidget::item:hover {{
                background-color: #E8F5E9;
            }}
        """)
        self.list_widget.currentRowChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.list_widget)

        self.refresh_list()

        right = QWidget()
        right.setStyleSheet(f"background-color: {BG_COLOR};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 10, 10, 10)

        self.title_label = QLabel("Выберите станцию слева")
        self.title_label.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 24px; font-weight: bold; padding: 10px;"
        )
        right_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(230)
        self.image_label.setStyleSheet(
            "background-color: white; border: 2px solid #E0E0E0; border-radius: 8px;"
        )
        right_layout.addWidget(self.image_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet(f"""
            QTextEdit {{
                font-size: 16px;
                background-color: white;
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                padding: 10px;
                color: {TEXT_COLOR};
            }}
        """)
        right_layout.addWidget(self.info_text)

        self.study_button = QPushButton("Пройти входной контроль")
        self.study_button.setEnabled(False)
        self.study_button.setMinimumHeight(55)
        self.study_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 19px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #777777;
            }}
        """)
        self.study_button.clicked.connect(self.start_quiz)
        right_layout.addWidget(self.study_button)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([400, 1000])

        layout.addWidget(splitter)

    def refresh_list(self):
        self.list_widget.clear()
        for s in self.stations:
            prefix = "✔ " if s["id"] in self.studied else "○ "
            item = QListWidgetItem(prefix + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

    def on_station_selected(self, row):
        if row < 0:
            return
        station = self.stations[row]
        self.current_station = station

        self.title_label.setText(station["name"])

        if station.get("image"):
            img_path = resource_path(station["image"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                self.image_label.setPixmap(
                    pix.scaled(500, 230, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.image_label.setText(f"(картинка не найдена: {station['image']})")
                self.image_label.setStyleSheet(
                    "color: #C62828; font-size: 15px; padding: 10px;"
                )
        else:
            self.image_label.setText("(картинка отсутствует)")
            self.image_label.setStyleSheet(
                "color: #777; font-size: 15px; padding: 10px;"
            )

        purpose = station.get("purpose", "—")

        html = f"""
        <style>
            h3 {{
                color: {HEADER_COLOR};
                font-size: 20px;
                margin-top: 15px;
                margin-bottom: 8px;
                border-bottom: 2px solid {LIGHT_ACCENT};
                padding-bottom: 5px;
            }}
            p {{
                color: {TEXT_COLOR};
                font-size: 16px;
                line-height: 1.5;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                font-size: 15px;
            }}
            th {{
                background-color: {HEADER_COLOR};
                color: white;
                padding: 10px;
                text-align: left;
                font-size: 16px;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #E0E0E0;
                color: {TEXT_COLOR};
            }}
            tr:nth-child(even) td {{
                background-color: #F5F5F5;
            }}
            tr:hover td {{
                background-color: #E8F5E9;
            }}
        </style>
        <h3>Назначение</h3>
        <p>{purpose}</p>
        <h3>Тактико-технические характеристики</h3>
        <table>
        <tr><th style="width: 65%;">Характеристика</th><th style="width: 35%;">Значение</th></tr>
        """

        for spec in station["specs"]:
            unit = spec.get("unit", "").strip()
            if unit:
                name_with_unit = f"{spec['name']}, {unit}"
            else:
                name_with_unit = spec["name"]
            value = spec["answer"]
            html += f"<tr><td>{name_with_unit}</td><td><b>{value}</b></td></tr>"

        html += "</table>"

        self.info_text.setHtml(html)
        self.study_button.setEnabled(True)

    def start_quiz(self):
        dialog = QuizDialog(self.current_station, self)
        if dialog.exec_() == QuizDialog.Accepted:
            self.studied.add(self.current_station["id"])
            self.refresh_list()
            QMessageBox.information(
                self, "Отлично!",
                f"Станция «{self.current_station['name']}» отмечена как изученная."
            )


class LearningWindow(QMainWindow):

    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.studied = set()

        self.setWindowTitle("Режим обучения")
        self.resize(1400, 850)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад на стартовый экран")
        back_btn.setMinimumHeight(45)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                background-color: {ACCENT_HOVER};
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
            }}
        """)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px;
                background-color: {BG_COLOR};
            }}
            QTabBar::tab {{
                background-color: #E8F5E9;
                color: {TEXT_COLOR};
                padding: 12px 30px;
                font-size: 17px;
                font-weight: bold;
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
        tabs.addTab(StationListWidget("radio", self), "Радиорелейные станции")
        tabs.addTab(StationListWidget("satellite", self), "Спутниковые станции")
        layout.addWidget(tabs)

    def go_back(self):
        self.back_callback()
        self.close()
