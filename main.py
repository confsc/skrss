import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.start_screen import StartScreen


def resource_path(relative_path):
    """Работает и в .exe, и в исходниках."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    app = QApplication(sys.argv)

    # Иконка окна
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = StartScreen()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
