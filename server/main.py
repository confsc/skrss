import sys
import os
import threading
import traceback
import datetime


def _log_path():
    if hasattr(sys, "_MEIPASS"):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "server.log")


LOG_PATH = _log_path()


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


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
            shared = os.path.join(base, "shared")
        if not os.path.exists(server_logic):
            server_logic = os.path.join(base, "logic")
        if not os.path.exists(server_ui):
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

    log(f"Paths: shared={shared}")
    log(f"Paths: server_logic={server_logic}")
    log(f"Paths: server_ui={server_ui}")


log("=" * 60)
log("Server starting")
log(f"sys._MEIPASS = {getattr(sys, '_MEIPASS', 'None')}")
log(f"sys.executable = {sys.executable}")
log(f"__file__ = {__file__}")
log(f"cwd = {os.getcwd()}")

_setup_paths()

try:
    from config import SERVER_HOST, SERVER_PORT
    log(f"config loaded: {SERVER_HOST}:{SERVER_PORT}")
except Exception as e:
    log(f"config import error: {e}")
    log(traceback.format_exc())


def run_flask():
    try:
        from api import create_app
        app, _ = create_app()
        log(f"Flask started on {SERVER_HOST}:{SERVER_PORT}")
        app.run(
            host=SERVER_HOST,
            port=SERVER_PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except Exception as e:
        log(f"Flask error: {e}")
        log(traceback.format_exc())


def run_ui():
    try:
        log("run_ui: import PyQt5")
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon

        log("run_ui: import main_window")
        from main_window import ServerWindow

        log("run_ui: create QApplication")
        app = QApplication(sys.argv)

        icon_path = resource_path("icon.ico")
        log(f"icon_path = {icon_path}, exists = {os.path.exists(icon_path)}")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        log("run_ui: create ServerWindow")
        window = ServerWindow()
        log("run_ui: show window")
        window.show()

        log("run_ui: enter event loop")
        sys.exit(app.exec_())
    except Exception as e:
        log(f"UI error: {e}")
        log(traceback.format_exc())


def main():
    log("main: start")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    log("main: flask thread started")
    run_ui()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())