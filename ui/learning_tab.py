from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QTextEdit, QPushButton, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from logic.data_loader import load_stations


class LearningTab(QWidget):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.stations = [s for s in load_stations() if s["category"] == category]
        self.studied = set()  # сбрасывается при перезапуске

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # Левая часть — список станций
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("<b>Выберите станцию:</b>"))

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.list_widget)

        self.refresh_list()

        # Правая часть — ТТХ станции
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.title_label = QLabel("<i>Выберите станцию слева</i>")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        right_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        right_layout.addWidget(self.image_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        right_layout.addWidget(self.info_text)

        self.study_button = QPushButton("Отметить как изученную")
        self.study_button.setEnabled(False)
        self.study_button.clicked.connect(self.mark_studied)
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

        # Картинка
        if station.get("image"):
            pix = QPixmap(station["image"])
            if not pix.isNull():
                self.image_label.setPixmap(
                    pix.scaled(400, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.image_label.setText("(картинка не найдена)")
        else:
            self.image_label.setText("(картинка отсутствует)")

        # ТТХ
        html = f"<h3>Назначение</h3><p>{station.get('purpose', '—')}</p>"
        html += "<h3>Тактико-технические характеристики</h3><ul>"
        for spec in station["specs"]:
            unit = f" {spec['unit']}" if spec.get("unit") else ""
            html += f"<li><b>{spec['name']}:</b> {spec['answer']}{unit}</li>"
        html += "</ul>"
        self.info_text.setHtml(html)

        self.study_button.setEnabled(True)

    def mark_studied(self):
        self.studied.add(self.current_station["id"])
        self.refresh_list()
        QMessageBox.information(
            self, "Готово",
            f"Станция «{self.current_station['name']}» отмечена как изученная."
        )