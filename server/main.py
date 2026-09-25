import sys
import os
import threading
import traceback
import datetime


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def log_path():
    return os.path.join(_app_dir(), "server.log")


def log(msg):
    try:
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


def _setup_paths():
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        for p in [base,
                  os.path.join(base, "shared"),
                  os.path.join(base, "logic"),
                  os.path.join(base, "ui"),
                  os.path.join(base, "data")]:
            if p not in sys.path:
                sys.path.insert(0, p)
        log(f"MEIPASS: {base}")
        log(f"Files: {sorted(os.listdir(base))}")
    else:
        current = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(current, ".."))
        for p in [current,
                  os.path.join(root, "shared"),
                  os.path.join(root, "server", "logic"),
                  os.path.join(root, "server", "ui")]:
            if p not in sys.path:
                sys.path.insert(0, p)


log("=" * 60)
log("Server starting")
log(f"frozen = {getattr(sys, 'frozen', False)}")
log(f"sys.executable = {sys.executable}")

_setup_paths()

try:
    from config import SERVER_HOST, SERVER_PORT
    log(f"config: {SERVER_HOST}:{SERVER_PORT}")
except Exception as e:
    log(f"config error: {e}")
    log(traceback.format_exc())
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5000


def run_flask():
    try:
        log("run_flask: import api")
        from api import create_app
        app, _ = create_app()
        log(f"Flask: {SERVER_HOST}:{SERVER_PORT}")
        app.run(host=SERVER_HOST, port=SERVER_PORT,
                debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        log(f"Flask error: {e}")
        log(traceback.format_exc())


def run_ui():
    try:
        log("run_ui: import PyQt5")
        from PyQt5.QtWidgets import QApplication

        log("run_ui: import main_window")
        from main_window import ServerWindow

        app = QApplication(sys.argv)
        window = ServerWindow()
        window.show()
        log("run_ui: window shown")
        sys.exit(app.exec_())
    except Exception as e:
        log(f"UI error: {e}")
        log(traceback.format_exc())


def main():
    log("main: start")
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    run_ui()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
