from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor, QCursor

from logic.data_loader import resource_path

from styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_HOVER,
    COLOR_BG_MAIN, COLOR_CARD_BG, COLOR_BORDER,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_LIGHT
)


class ModeCard(QFrame):
    """Интерактивная карточка выбора режима с ховером и анимацией клика."""
    clicked = pyqtSignal()

    def __init__(self, title, btn_text, is_primary=True, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(130)

        self.normal_style = f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """
        self.hover_style = f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 2px solid {COLOR_PRIMARY if is_primary else COLOR_PRIMARY_HOVER};
                border-radius: 12px;
            }}
        """
        self.setStyleSheet(self.normal_style)

        # Тень
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 18))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_PRIMARY_DARK}; border: none;")
        layout.addWidget(lbl_title)
        layout.addStretch()

        # Кнопка действия внизу карточки
        self.action_btn = QPushButton(btn_text)
        self.action_btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn_bg = COLOR_PRIMARY if is_primary else COLOR_PRIMARY_HOVER
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {COLOR_TEXT_LIGHT};
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                border: none;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY_HOVER if is_primary else COLOR_PRIMARY_DARK};
            }}
        """)
        self.action_btn.clicked.connect(self.clicked.emit)
        layout.addWidget(self.action_btn, 0, Qt.AlignRight)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setStyleSheet(self.hover_style)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.setStyleSheet(self.normal_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StartScreen(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажёр: Радиорелейные и спутниковые станции")
        self.resize(1100, 850)
        self.setMinimumSize(850, 650)
        self.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")

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
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18)

        # Верхняя панель заголовков
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        header_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Тренажёр: Радиорелейные и спутниковые станции")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_PRIMARY_DARK}; font-size: 26px; font-weight: 800;")
        header_layout.addWidget(title)

        subtitle = QLabel("Учебный комплекс изучения ТТХ и контроля знаний")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px; font-weight: 500;")
        header_layout.addWidget(subtitle)
        layout.addWidget(header_widget)

        # Контейнер для фото/иллюстрации
        self.img_container = QFrame()
        self.img_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border: 1.5px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
        """)
        img_layout = QVBoxLayout(self.img_container)
        img_layout.setContentsMargins(10, 10, 10, 10)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumHeight(240)
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img_label.setStyleSheet("border: none; background: transparent;")

        bg_path = resource_path("images/start_background.png")
        pix = QPixmap(bg_path)
        if not pix.isNull():
            self.current_pixmap = pix
        else:
            self.img_label.setText("📷 Иллюстрация комплекса")
            self.img_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 16px; border: none;")

        img_layout.addWidget(self.img_label)
        layout.addWidget(self.img_container, 4)

        # Карточки режимов работы (Обучение и Контроль)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        card_learn = ModeCard(
            title="Обучение",
            btn_text="Начать обучение →",
            is_primary=True,
            parent=self
        )
        card_learn.clicked.connect(self.open_learning)
        cards_layout.addWidget(card_learn)

        card_quiz = ModeCard(
            title="Контроль знаний",
            btn_text="Пройти тестирование →",
            is_primary=False,
            parent=self
        )
        card_quiz.clicked.connect(self.open_quiz)
        cards_layout.addWidget(card_quiz)

        layout.addLayout(cards_layout, 2)

    def update_image(self):
        if not self.current_pixmap:
            return
        w = max(260, self.img_label.width() - 16)
        h = max(180, self.img_label.height() - 16)
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
        from ui.learning_window import LearningWindow
        self.learning_window = LearningWindow(back_callback=self.show)
        self.learning_window.show()
        self.hide()

    def open_quiz(self):
        from ui.student_form import StudentFormDialog
        from logic.network import ServerFinder, ApiClient, try_direct_ip
        from ui.waiting_dialog import WaitingDialog
        from ui.quiz_window import QuizWindow

        dialog = StudentFormDialog(self)
        if dialog.exec_() != StudentFormDialog.Accepted:
            return

        self.fio = dialog.fio
        self.group_name = dialog.group
        manual_ip = dialog.manual_ip

        ip = None
        port = None

        if manual_ip:
            result = try_direct_ip(manual_ip)
            if result:
                ip, port = result
            else:
                QMessageBox.warning(
                    self, "Сервер недоступен",
                    f"По адресу «{manual_ip}» сервер не отвечает.\n\n"
                    "Проверьте IP-адрес и убедитесь, что сервер запущен."
                )
                return
        else:
            finder = ServerFinder()
            if finder.find():
                ip = finder.found_ip
                port = finder.found_port

        if not ip:
            QMessageBox.warning(
                self, "Сервер не найден",
                "Не удалось найти сервер автоматически.\n\n"
                "Попросите преподавателя назвать IP-адрес\n"
                "и введите его вручную в форме авторизации."
            )
            return

        self.api_client = ApiClient(ip, port)

        if not self.api_client.ping():
            QMessageBox.warning(
                self, "Сервер недоступен",
                f"Сервер найден по адресу {ip}:{port}, но не отвечает."
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
