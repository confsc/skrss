import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
ui_dir = os.path.join(current_dir, "ui")
if ui_dir not in sys.path:
    sys.path.insert(0, ui_dir)
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
shared_dir = os.path.join(root_dir, "shared")
if shared_dir not in sys.path:
    sys.path.insert(0, shared_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from logic.single_instance import check_single_instance
from styles import GLOBAL_APP_STYLE


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def main():
    check_single_instance()

    # ????????? ????????? High-DPI ??????? ?? ???????? QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    from ui.start_screen import StartScreen

    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_APP_STYLE)

    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = StartScreen()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()