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

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        bg_path = resource_path("images/start_background.png")
        pix = QPixmap(bg_path)
        if not pix.isNull():
            img_label.setPixmap(
                pix.scaled(700, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            img_label.setText("(фото не найдено — добавь images/start_background.png)")
            img_label.setStyleSheet("color: red; font-size: 14px;")
        layout.addWidget(img_label)

        layout.addSpacing(20)

        title = QLabel("Тренажёр\nРадиорелейные и спутниковые станции")
        title.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        layout.addSpacing(30)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignCenter)
        buttons.setSpacing(50)

        btn_learn = QPushButton("📚\nРежим обучения")
        btn_learn.setFixedSize(260, 130)
        btn_learn.setStyleSheet(
            "QPushButton { font-size: 18px; background-color: #4CAF50; "
            "color: white; border-radius: 15px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        btn_learn.clicked.connect(self.open_learning)
        buttons.addWidget(btn_learn)

        btn_quiz = QPushButton("📝\nРежим контроля")
        btn_quiz.setFixedSize(260, 130)
        btn_quiz.setStyleSheet(
            "QPushButton { font-size: 18px; background-color: #2196F3; "
            "color: white; border-radius: 15px; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
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
