from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QTextEdit, QPushButton, QTabWidget,
    QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from logic.data_loader import load_stations, resource_path
from ui.quiz_dialog import QuizDialog


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
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("<b>Выберите станцию:</b>"))

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.list_widget)

        self.refresh_list()

        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.title_label = QLabel("<i>Выберите станцию слева</i>")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        self.title_label.setFont(f)
        right_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        right_layout.addWidget(self.image_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        right_layout.addWidget(self.info_text)

        self.study_button = QPushButton("Пройти входной контроль")
        self.study_button.setEnabled(False)
        self.study_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.study_button.clicked.connect(self.start_quiz)
        right_layout.addWidget(self.study_button)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([300, 900])

        layout.addWidget(splitter)

    def refresh_list(self):
        self.list_widget.clear()
        for s in self.stations:
            prefix = "✔ " if s["id"] in self.studied else "☐ "
            item = QListWidgetItem(prefix + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.list_widget.addItem(item)

    def on_station_selected(self, row):
        if row < 0:
            return
        station = self.stations[row]
        self.current_station = station

        self.title_label.setText(station["name"])

        # ===== ФОТО — используем resource_path =====
        if station.get("image"):
            img_path = resource_path(station["image"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                self.image_label.setPixmap(
                    pix.scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.image_label.setText(f"(картинка не найдена: {station['image']})")
        else:
            self.image_label.setText("(картинка отсутствует)")

        html = f"<h3>Назначение</h3><p>{station.get('purpose', '—')}</p>"
        html += "<h3>Тактико-технические характеристики</h3><ul>"
        for spec in station["specs"]:
            unit = f" {spec['unit']}" if spec.get("unit") else ""
            html += f"<li><b>{spec['name']}:</b> {spec['answer']}{unit}</li>"
        html += "</ul>"
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
        self.resize(1200, 750)

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
        tabs.addTab(StationListWidget("radio", self), "Радиорелейные станции")
        tabs.addTab(StationListWidget("satellite", self), "Спутниковые станции")
        layout.addWidget(tabs)

    def go_back(self):
        self.back_callback()
        self.close()
