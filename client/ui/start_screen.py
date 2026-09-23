from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from logic.data_loader import resource_path
from logic.network import ServerFinder, ApiClient
from ui.learning_window import LearningWindow
from ui.quiz_window import QuizWindow
from ui.student_form import StudentFormDialog
from ui.waiting_dialog import WaitingDialog


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
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.learning_window = None
        self.quiz_window = None
        self.current_pixmap = None

        self.api_client = None
        self.fio = ""
        self.group_name = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumHeight(280)
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setStyleSheet("background-color: transparent; border: none;")

        bg_path = resource_path("images/start_background.png")
        pix = QPixmap(bg_path)
        if not pix.isNull():
            self.current_pixmap = pix
        else:
            self.img_label.setText("(фото не найдено)")
            self.img_label.setStyleSheet(
                "color: #C62828; font-size: 16px; padding: 20px; border: none;"
            )

        layout.addWidget(self.img_label, 5)

        title = QLabel("Тренажёр: Радиорелейные и спутниковые станции")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {HEADER_COLOR}; font-size: 26px; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(title, 1)

        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignCenter)
        buttons.setSpacing(50)

        btn_learn = QPushButton("📚\nРежим обучения")
        btn_learn.setMinimumSize(280, 140)
        btn_learn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_learn.setStyleSheet(f"""
            QPushButton {{
                font-size: 20px; font-weight: bold;
                background-color: {ACCENT_COLOR}; color: white;
                border-radius: 15px; border: none; padding: 15px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        btn_learn.clicked.connect(self.open_learning)
        buttons.addWidget(btn_learn)

        btn_quiz = QPushButton("📝\nРежим контроля")
        btn_quiz.setMinimumSize(280, 140)
        btn_quiz.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_quiz.setStyleSheet(f"""
            QPushButton {{
                font-size: 20px; font-weight: bold;
                background-color: {ACCENT_HOVER}; color: white;
                border-radius: 15px; border: none; padding: 15px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_COLOR}; }}
        """)
        btn_quiz.clicked.connect(self.open_quiz)
        buttons.addWidget(btn_quiz)

        layout.addLayout(buttons)

    def update_image(self):
        if not self.current_pixmap:
            return
        w = max(300, self.img_label.width() - 20)
        h = max(200, self.img_label.height() - 20)
        self.img_label.setPixmap(
            self.current_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_image()
        self.api_client = None
        self.fio = ""
        self.group_name = ""

    def open_learning(self):
        self.learning_window = LearningWindow(back_callback=self.show)
        self.learning_window.show()
        self.hide()

    def open_quiz(self):
        dialog = StudentFormDialog(self)
        if dialog.exec_() != StudentFormDialog.Accepted:
            return

        self.fio = dialog.fio
        self.group_name = dialog.group

        finder = ServerFinder()
        found = finder.find()

        if not found:
            QMessageBox.warning(
                self, "Сервер не найден",
                "Не удалось найти сервер преподавателя.\n\n"
                "Проверьте, что вы в одной сети с преподавателем.\n"
                "Попробуйте ещё раз позже."
            )
            return

        self.api_client = ApiClient(finder.found_ip, finder.found_port)

        if not self.api_client.ping():
            QMessageBox.warning(
                self, "Сервер недоступен",
                "Сервер найден, но не отвечает.\n"
                "Попробуйте ещё раз."
            )
            return

        waiting = WaitingDialog(self.api_client, self.fio, self.group_name, self)
        result = waiting.exec_()

        if result != WaitingDialog.Accepted or not waiting.result:
            return

        self.quiz_window = QuizWindow(
            back_callback=self.show,
            api_client=self.api_client,
            fio=self.fio,
            group_name=self.group_name,
        )
        self.quiz_window.show()
        self.hide()