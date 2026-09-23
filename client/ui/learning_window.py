from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QTextEdit, QPushButton, QTabWidget,
    QSplitter, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from logic.data_loader import load_stations, resource_path
from logic.specs_formatter import build_specs_html
from ui.quiz_dialog import QuizDialog


BG_COLOR = "#FAFAFA"
TEXT_COLOR = "#1B1B1B"
HEADER_COLOR = "#1B4332"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"

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
QScrollBar:horizontal {
    background: #F0F0F0; height: 14px; margin: 0px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal {
    background: #6B8E7B; min-width: 30px;
    border-radius: 7px; margin: 2px;
}
QScrollBar::handle:horizontal:hover { background: #4A6B5A; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
"""


class StationListWidget(QWidget):

    def __init__(self, category, parent_window):
        super().__init__()
        self.category = category
        self.parent_window = parent_window
        self.stations = [s for s in load_stations() if s["category"] == category]
        self.studied = parent_window.studied
        self.current_station = None
        self.current_pixmap = None

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left = QWidget()
        left.setStyleSheet(f"background-color: {BG_COLOR};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)

        list_title = QLabel("Выберите станцию:")
        list_title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 18px; font-weight: bold; padding: 5px;"
        )
        left_layout.addWidget(list_title)

        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                font-size: 16px; background-color: white;
                border: 2px solid {LIGHT_ACCENT}; border-radius: 8px;
                padding: 5px; color: {TEXT_COLOR}; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid #E0E0E0; outline: none;
            }}
            QListWidget::item:selected {{
                background-color: {LIGHT_ACCENT}; color: {HEADER_COLOR};
                font-weight: bold; border-radius: 5px;
                border: none; outline: none;
            }}
            QListWidget::item:hover {{ background-color: #E8F5E9; }}
            {SCROLLBAR_STYLE}
        """)
        self.list_widget.currentRowChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.list_widget)

        self.refresh_list()

        right = QWidget()
        right.setStyleSheet(f"background-color: {BG_COLOR};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        self.title_label = QLabel("Выберите станцию слева")
        self.title_label.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 22px; font-weight: bold; padding: 8px;"
        )
        right_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(220)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("background-color: transparent; border: none;")
        right_layout.addWidget(self.image_label, 3)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.info_text.setStyleSheet(f"""
            QTextEdit {{
                font-size: 15px; background-color: white;
                border: none; border-radius: 8px;
                padding: 15px; color: {TEXT_COLOR};
            }}
            {SCROLLBAR_STYLE}
        """)
        right_layout.addWidget(self.info_text, 4)

        self.study_button = QPushButton("Пройти входной контроль")
        self.study_button.setEnabled(False)
        self.study_button.setMinimumHeight(50)
        self.study_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.study_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 17px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 10px; padding: 10px 20px; border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: #CCCCCC; color: #777777; }}
        """)
        self.study_button.clicked.connect(self.start_quiz)
        right_layout.addWidget(self.study_button)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

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

        self.current_pixmap = None

        if station.get("image"):
            img_path = resource_path(station["image"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                self.current_pixmap = pix
                self.update_image()
            else:
                self.image_label.clear()
                self.image_label.setText(f"(картинка не найдена: {station['image']})")
                self.image_label.setStyleSheet(
                    "color: #C62828; font-size: 15px; padding: 10px; border: none;"
                )
        else:
            self.image_label.clear()
            self.image_label.setText("(картинка отсутствует)")
            self.image_label.setStyleSheet(
                "color: #777; font-size: 15px; padding: 10px; border: none;"
            )

        purpose = station.get("purpose", "—")
        specs_html = build_specs_html(station)

        html = f"""
        <style>
            h3 {{
                color: {HEADER_COLOR}; font-size: 18px;
                margin-top: 10px; margin-bottom: 8px;
                border-bottom: 2px solid {LIGHT_ACCENT}; padding-bottom: 5px;
            }}
            p {{
                color: {TEXT_COLOR}; font-size: 15px;
                line-height: 1.5; margin: 5px 0;
            }}
        </style>
        <h3>Назначение</h3>
        <p>{purpose}</p>
        {specs_html}
        """

        self.info_text.setHtml(html)
        self.study_button.setEnabled(True)

    def update_image(self):
        if not self.current_pixmap:
            return
        w = max(200, self.image_label.width() - 20)
        h = max(150, self.image_label.height() - 20)
        self.image_label.setPixmap(
            self.current_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def start_quiz(self):
        dialog = QuizDialog(
            station=self.current_station,
            parent=self,
            is_control=False,
        )
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
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        top = QHBoxLayout()
        back_btn = QPushButton("← Назад на стартовый экран")
        back_btn.setMinimumHeight(44)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 15px; background-color: {ACCENT_HOVER};
                color: white; border-radius: 8px;
                padding: 8px 20px; border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_COLOR}; }}
        """)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {LIGHT_ACCENT};
                border-radius: 8px; background-color: {BG_COLOR};
                top: -1px;
            }}
            QTabBar {{ background-color: transparent; }}
            QTabBar::tab {{
                background-color: #E8F5E9; color: {TEXT_COLOR};
                padding: 12px 28px; font-size: 15px; font-weight: bold;
                min-width: 220px; min-height: 22px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px; margin-top: 0px;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_COLOR}; color: white;
            }}
            QTabBar::tab:hover {{ background-color: {LIGHT_ACCENT}; }}
        """)
        self.tabs.addTab(StationListWidget("radio", self), "Радиорелейные станции")
        self.tabs.addTab(StationListWidget("satellite", self), "Спутниковые станции")
        layout.addWidget(self.tabs)

    def go_back(self):
        self.back_callback()
        self.close()