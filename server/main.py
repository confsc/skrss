"""
Точка входа сервера.
Запускает:
- Flask API (в отдельном потоке)
- UDP broadcast (в отдельном потоке)
- PyQt5 UI (главный поток)
"""
import os
import sys
import threading
import traceback


def _get_paths():
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, ".."))
    shared = os.path.join(root, "shared")
    server_logic = os.path.join(root, "server", "logic")
    server_ui = os.path.join(root, "server", "ui")
    return root, shared, server_logic, server_ui


ROOT, SHARED, SERVER_LOGIC, SERVER_UI = _get_paths()
sys.path.insert(0, SHARED)
sys.path.insert(0, SERVER_LOGIC)
sys.path.insert(0, SERVER_UI)

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

        icon_path = os.path.join(ROOT, "icon.ico")
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