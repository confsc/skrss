import sys
import os
import threading
import traceback


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def _setup_paths():
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        shared = os.path.join(base, "shared")
        server_logic = os.path.join(base, "server", "logic")
        server_ui = os.path.join(base, "server", "ui")
        if not os.path.exists(shared):
            server_logic = os.path.join(base, "logic")
            server_ui = os.path.join(base, "ui")
    else:
        current = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(current, ".."))
        shared = os.path.join(root, "shared")
        server_logic = os.path.join(root, "server", "logic")
        server_ui = os.path.join(root, "server", "ui")

    for p in [shared, server_logic, server_ui]:
        if p not in sys.path:
            sys.path.insert(0, p)


_setup_paths()

from config import SERVER_HOST, SERVER_PORT  # noqa: E402


def run_flask():
    try:
        from api import create_app
        app, _ = create_app()
        print(f"[API] Запуск на {SERVER_HOST}:{SERVER_PORT}")
        app.run(
            host=SERVER_HOST,
            port=SERVER_PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except Exception as e:
        print(f"[API] Ошибка: {e}")
        traceback.print_exc()


def run_ui():
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon
        from main_window import ServerWindow

        app = QApplication(sys.argv)

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        window = ServerWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"[UI] Ошибка: {e}")
        traceback.print_exc()


def main():
    print("=" * 60)
    print("  СЕРВЕР ТРЕНАЖЁРА")
    print("=" * 60)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    run_ui()


if __name__ == "__main__":
    main()