from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from logic.data_loader import resource_path
from ui.learning_window import LearningWindow
from ui.quiz_window import QuizWindow


class StartScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажёр: Радиорелейные и спутниковые станции")
        self.resize(1000, 800)

        self.learning_window = None
        self.quiz_window = None

        # ==== ОСНОВНОЙ КОНТЕЙНЕР ====
        central = QWidget()
        self.setCentralWidget(central)

        # ==== ФОНОВОЕ ФОТО (QLabel на весь экран) ====
        self.bg_label = QLabel(central)
        self.bg_label.setGeometry(0, 0, 1000, 800)
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setScaledContents(True)  # растянуть фото на весь label
        bg_path = resource_path("images/start_background.png")
        pix = QPixmap(bg_path)
        if not pix.isNull():
            self.bg_label.setPixmap(pix)
        else:
            self.bg_label.setText("(фон не найден)")
        self.bg_label.lower()  # опустить на задний план

        # ==== КОНТЕЙНЕР С КНОПКАМИ (поверх фото) ====
        overlay = QWidget(central)
        overlay.setGeometry(0, 0, 1000, 800)
        overlay.setStyleSheet("background: transparent;")  # прозрачный фон
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)

        # --- Заголовок ---
        title = QLabel("Тренажёр\nРадиорелейные и спутниковые станции")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: white; background: rgba(0,0,0,120); "
            "padding: 15px; border-radius: 10px; font-size: 22px; font-weight: bold;"
        )
        overlay_layout.addWidget(title)

        overlay_layout.addSpacing(60)

        # --- Кнопки ---
        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignCenter)
        buttons.setSpacing(50)

        btn_learn = QPushButton("📚\nРежим обучения")
        btn_learn.setFixedSize(260, 130)
        btn_learn.setStyleSheet(
            "QPushButton { font-size: 18px; background-color: rgba(76,175,80,220); "
            "color: white; border-radius: 15px; border: 2px solid white; }"
            "QPushButton:hover { background-color: rgba(69,160,73,240); }"
        )
        btn_learn.clicked.connect(self.open_learning)
        buttons.addWidget(btn_learn)

        btn_quiz = QPushButton("📝\nРежим контроля")
        btn_quiz.setFixedSize(260, 130)
        btn_quiz.setStyleSheet(
            "QPushButton { font-size: 18px; background-color: rgba(33,150,243,220); "
            "color: white; border-radius: 15px; border: 2px solid white; }"
            "QPushButton:hover { background-color: rgba(25,118,210,240); }"
        )
        btn_quiz.clicked.connect(self.open_quiz)
        buttons.addWidget(btn_quiz)

        overlay_layout.addLayout(buttons)

        overlay.raise_()  # поднять поверх фото

    def resizeEvent(self, event):
        """Растягиваем фон и overlay при изменении размера окна."""
        w, h = self.centralWidget().width(), self.centralWidget().height()
        self.bg_label.setGeometry(0, 0, w, h)
        # overlay тоже растягиваем
        for child in self.centralWidget().children():
            if isinstance(child, QWidget) and child is not self.bg_label:
                child.setGeometry(0, 0, w, h)
        super().resizeEvent(event)

    def open_learning(self):
        self.learning_window = LearningWindow(back_callback=self.show)
        self.learning_window.show()
        self.hide()

    def open_quiz(self):
        self.quiz_window = QuizWindow(back_callback=self.show)
        self.quiz_window.show()
        self.hide()
