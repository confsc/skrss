import sys
from PyQt5.QtWidgets import QApplication
from ui.start_screen import StartScreen


def main():
    app = QApplication(sys.argv)
    window = StartScreen()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
