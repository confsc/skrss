from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from logic.data_loader import resource_path
from ui.learning_window import LearningWindow
from ui.quiz_window import QuizWindow


HEADER_COLOR = "#1B4332"
TEXT_COLOR = "#1B1B1B"
ACCENT_COLOR = "#2D6A4F"
ACCENT_HOVER = "#40916C"
LIGHT_ACCENT = "#95D5B2"
BG_COLOR = "#FAFAFA"


class StartScreen(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажёр: Радиорелейные и спутниковые станции")
        self.resize(1100, 850)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.learning_window = None
        self.quiz_window = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        bg_path = resource_path("images/start_background.png")
        pix = QPixmap(bg_path)
        if not pix.isNull():
            img_label.setPixmap(
                pix.scaled(750, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            img_label.setText("(фото не найдено — добавь images/start_background.png)")
            img_label.setStyleSheet(
                "color: #C62828; font-size: 16px; padding: 20px;"
            )
        img_label.setStyleSheet(
            img_label.styleSheet()
            + "background-color: white; border: 2px solid #E0E0E0; border-radius: 12px;"
        )
        layout.addWidget(img_label)

        layout.addSpacing(15)

        title = QLabel("Тренажёр: Радиорелейные и спутниковые станции")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 28px; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(title)

        layout.addSpacing(20)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignCenter)
        buttons.setSpacing(60)

        btn_learn = QPushButton("📚\nРежим обучения")
        btn_learn.setFixedSize(300, 150)
        btn_learn.setStyleSheet(f"""
            QPushButton {{
                font-size: 20px;
                font-weight: bold;
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 15px;
                border: 3px solid {LIGHT_ACCENT};
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
                border-color: {ACCENT_COLOR};
            }}
        """)
        btn_learn.clicked.connect(self.open_learning)
        buttons.addWidget(btn_learn)

        btn_quiz = QPushButton("📝\nРежим контроля")
        btn_quiz.setFixedSize(300, 150)
        btn_quiz.setStyleSheet(f"""
            QPushButton {{
                font-size: 20px;
                font-weight: bold;
                background-color: {ACCENT_HOVER};
                color: white;
                border-radius: 15px;
                border: 3px solid {LIGHT_ACCENT};
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR};
                border-color: {ACCENT_COLOR};
            }}
        """)
        btn_quiz.clicked.connect(self.open_quiz)
        buttons.addWidget(btn_quiz)

        layout.addLayout(buttons)

    def open_learning(self):
        self.learning_window = LearningWindow(back_callback=self.show)
        self.learning_window.show()
        self.hide()

    def open_quiz(self):
        self.quiz_window = QuizWindow(back_callback=self.show)
        self.quiz_window.show()
        self.hide()
