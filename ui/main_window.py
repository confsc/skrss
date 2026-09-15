from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.learning_tab import LearningTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажёр: Радиорелейные и спутниковые станции")
        self.resize(1200, 750)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.learning_radio = LearningTab(category="radio")
        self.learning_satellite = LearningTab(category="satellite")

        tabs.addTab(self.learning_radio, "Радиорелейные станции")
        tabs.addTab(self.learning_satellite, "Спутниковые станции")