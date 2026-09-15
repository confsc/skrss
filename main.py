import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажёр: Радиорелейные и спутниковые станции")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        label = QLabel("Привет! Это тестовая сборка.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 20px; padding: 20px;")
        layout.addWidget(label)

        btn = QPushButton("Нажми меня")
        btn.setStyleSheet("font-size: 16px; padding: 10px;")
        btn.clicked.connect(self.on_click)
        layout.addWidget(btn)

    def on_click(self):
        print("Кнопка нажата!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
