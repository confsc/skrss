"""
Окно режима обучения (каталог станций, ТТХ, фото и самопроверка).
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QTextEdit, QPushButton, QTabWidget,
    QSplitter, QMessageBox, QSizePolicy, QLineEdit, QDialog,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QCursor

from logic.data_loader import load_stations, resource_path
from logic.specs_formatter import build_specs_html
from ui.quiz_dialog import QuizDialog

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_PRIMARY_PALE, COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_BORDER_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT, COLOR_SUCCESS, COLOR_SUCCESS_BG, BTN_PRIMARY_STYLE,
    BTN_SECONDARY_STYLE, make_badge_html
)


class ImageViewerDialog(QDialog):
    """Полноразмерный модальный просмотр фото станции с высоким качеством."""

    def __init__(self, pixmap, title_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Просмотр: {title_text}")
        self.resize(1000, 750)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel(title_text)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY_DARK};")
        layout.addWidget(header)

        img_frame = QFrame()
        img_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
        """)
        frame_layout = QVBoxLayout(img_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pixmap = pixmap

        frame_layout.addWidget(self.label)
        layout.addWidget(img_frame, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(140)
        close_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)

        self.update_image()

    def update_image(self):
        if not self.pixmap:
            return
        w = max(400, self.label.width() - 20)
        h = max(300, self.label.height() - 20)
        self.label.setPixmap(
            self.pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()


class StationListWidget(QWidget):

    def __init__(self, category, parent_window):
        super().__init__()
        self.category = category
        self.parent_window = parent_window
        self.stations = [s for s in load_stations() if s["category"] == category]
        self.filtered_stations = list(self.stations)
        self.studied = parent_window.studied
        self.current_station = None
        self.current_pixmap = None

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Левая панель: Поиск и список станций
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(10)

        # Заголовок списка с бейджем прогресса
        list_header = QHBoxLayout()
        list_title = QLabel("Список станций:")
        list_title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 16px; font-weight: 700;")
        list_header.addWidget(list_title)

        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        list_header.addWidget(self.progress_label, 0, Qt.AlignRight)
        left_layout.addLayout(list_header)

        # Быстрый поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по названию...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search_changed)
        left_layout.addWidget(self.search_input)

        # Список станций
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.currentRowChanged.connect(self.on_station_selected)
        left_layout.addWidget(self.list_widget)

        # Правая панель: Детальная карточка станции
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(12)

        # Карточка заголовка выбранной станции
        title_card = QFrame()
        title_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 12px 18px;
            }}
        """)
        t_layout = QHBoxLayout(title_card)
        t_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Выберите станцию из списка слева")
        self.title_label.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 20px; font-weight: 700; border: none;")
        t_layout.addWidget(self.title_label)
        t_layout.addStretch()

        self.station_status_badge = QLabel()
        self.station_status_badge.setStyleSheet("border: none;")
        t_layout.addWidget(self.station_status_badge)
        right_layout.addWidget(title_card)

        # Контейнер для фото с подсказкой зума
        self.img_card = QFrame()
        self.img_card.setCursor(QCursor(Qt.PointingHandCursor))
        self.img_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {COLOR_PRIMARY};
            }}
        """)
        img_layout = QVBoxLayout(self.img_card)
        img_layout.setContentsMargins(8, 8, 8, 8)
        img_layout.setSpacing(4)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("border: none; background: transparent;")
        img_layout.addWidget(self.image_label)

        self.zoom_hint = QLabel("🔍 Нажмите на фото для просмотра в полном размере")
        self.zoom_hint.setAlignment(Qt.AlignCenter)
        self.zoom_hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; border: none;")
        img_layout.addWidget(self.zoom_hint)

        self.img_card.mousePressEvent = self.open_full_image
        right_layout.addWidget(self.img_card, 3)

        # Карточка ТТХ
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.info_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 14px;
            }}
        """)
        right_layout.addWidget(self.info_text, 4)

        # Кнопка самопроверки
        self.study_button = QPushButton("Пройти самопроверку по станции →")
        self.study_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.study_button.setEnabled(False)
        self.study_button.setMinimumHeight(46)
        self.study_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.study_button.setStyleSheet(BTN_PRIMARY_STYLE)
        self.study_button.clicked.connect(self.start_quiz)
        right_layout.addWidget(self.study_button)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        self.refresh_list()

    def on_search_changed(self, text):
        query = text.strip().lower()
        if not query:
            self.filtered_stations = list(self.stations)
        else:
            self.filtered_stations = [
                s for s in self.stations
                if query in s["name"].lower() or query in s.get("purpose", "").lower()
            ]
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        studied_count = sum(1 for s in self.stations if s["id"] in self.studied)
        total_count = len(self.stations)

        self.progress_label.setText(
            make_badge_html(f"{studied_count} / {total_count} изучено", COLOR_PRIMARY_PALE, COLOR_PRIMARY_DARK)
        )

        for s in self.filtered_stations:
            is_done = s["id"] in self.studied
            icon = "✓ " if is_done else "○ "
            item = QListWidgetItem(icon + s["name"])
            item.setData(Qt.UserRole, s["id"])
            if is_done:
                item.setForeground(QColor(COLOR_SUCCESS))
            self.list_widget.addItem(item)

        if self.filtered_stations:
            self.list_widget.setCurrentRow(0)

    def on_station_selected(self, row):
        if not hasattr(self, "title_label") or not hasattr(self, "info_text") or not hasattr(self, "station_status_badge"):
            return
        if row < 0 or row >= len(self.filtered_stations):
            return
        station = self.filtered_stations[row]
        self.current_station = station

        self.title_label.setText(station["name"])

        is_done = station["id"] in self.studied
        if is_done:
            self.station_status_badge.setText(make_badge_html("Изучено", COLOR_SUCCESS_BG, COLOR_SUCCESS))
        else:
            self.station_status_badge.setText(make_badge_html("Не изучено", "#F1F5F9", COLOR_TEXT_MUTED))

        self.current_pixmap = None

        if station.get("image"):
            img_path = resource_path(station["image"])
            pix = QPixmap(img_path)
            if not pix.isNull():
                self.current_pixmap = pix
                self.update_image()
                self.zoom_hint.show()
            else:
                self.image_label.clear()
                self.image_label.setText(f"(изображение не найдено: {station['image']})")
                self.image_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; border: none;")
                self.zoom_hint.hide()
        else:
            self.image_label.clear()
            self.image_label.setText("(изображение отсутствует)")
            self.image_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 13px; border: none;")
            self.zoom_hint.hide()

        purpose = station.get("purpose", "—")
        specs_html = build_specs_html(station)

        html = f"""
        <div style="margin-bottom: 12px;">
            <b style="color: {COLOR_PRIMARY_DARK}; font-size: 15px;">Назначение комплекса:</b>
            <p style="color: {COLOR_TEXT_PRIMARY}; font-size: 14px; line-height: 1.5; margin: 6px 0 12px 0;">{purpose}</p>
        </div>
        {specs_html}
        """

        self.info_text.setHtml(html)
        self.study_button.setEnabled(True)

    def update_image(self):
        if not self.current_pixmap:
            return
        w = max(200, self.image_label.width() - 16)
        h = max(150, self.image_label.height() - 16)
        self.image_label.setPixmap(
            self.current_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def open_full_image(self, event):
        if self.current_pixmap and self.current_station:
            dialog = ImageViewerDialog(self.current_pixmap, self.current_station["name"], self)
            dialog.exec_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def start_quiz(self):
        dialog = QuizDialog(
            station=self.current_station,
            parent=self,
            is_control=False,
        )
        result = dialog.exec_()

        if result != QuizDialog.Accepted:
            return

        data = dialog.result_data or {}
        grade = data.get("grade", 0)
        percent = data.get("percent", 0)
        correct = data.get("correct_count", 0)
        total = data.get("total", 0)

        if grade == 5:
            self.studied.add(self.current_station["id"])
            self.refresh_list()
            QMessageBox.information(
                self,
                "Зачёт получен!",
                f"Станция «{self.current_station['name']}» успешно усвоена.\n\n"
                f"Оценка: 5 ({percent:.1f}%)\n"
                f"Правильных ответов: {correct} из {total}"
            )
        else:
            QMessageBox.warning(
                self,
                "Требуется повторение",
                f"Для зачёта требуется оценка 5 (не менее 90% правильных ответов).\n\n"
                f"Ваш результат: {grade} ({percent:.1f}%)\n"
                f"Правильных: {correct} из {total}\n\n"
                f"Повторите характеристики станции и попробуйте снова."
            )


class LearningWindow(QMainWindow):

    def __init__(self, back_callback):
        super().__init__()
        self.back_callback = back_callback
        self.studied = set()

        self.setWindowTitle("Режим обучения — Каталог и ТТХ станций")
        self.resize(1350, 850)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        # Верхняя панель навигации
        top = QHBoxLayout()
        back_btn = QPushButton("← На главный экран")
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setMinimumHeight(40)
        back_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        back_btn.clicked.connect(self.go_back)
        top.addWidget(back_btn)

        window_title = QLabel("Учебный каталог средств связи")
        window_title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY_DARK}; margin-left: 12px;")
        top.addWidget(window_title)
        top.addStretch()
        layout.addLayout(top)

        # Вкладки категорий
        self.tabs = QTabWidget()
        self.tabs.addTab(StationListWidget("radio", self), "📻 Радиорелейные станции")
        self.tabs.addTab(StationListWidget("satellite", self), "🛰 Спутниковые станции")
        layout.addWidget(self.tabs)

    def go_back(self):
        self.close()

    def closeEvent(self, event):
        if self.back_callback:
            self.back_callback()
            self.back_callback = None
        super().closeEvent(event)
