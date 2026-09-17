import os
import sys
import tempfile
import atexit


LOCK_FILE = os.path.join(tempfile.gettempdir(), "rrs_trainer.lock")


def check_single_instance():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())

            if _is_process_alive(old_pid):
                _show_already_running()
                sys.exit(0)
            else:
                os.remove(LOCK_FILE)
        except (ValueError, OSError):
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(_cleanup)


def _is_process_alive(pid):
    if sys.platform == "win32":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        STILL_ACTIVE = 259
        return exit_code.value == STILL_ACTIVE
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _cleanup():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


def _show_already_running():
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Программа уже запущена",
            "Тренажёр уже открыт.\n\n"
            "Закройте предыдущее окно и запустите снова."
        )
    except Exception:
        print("Программа уже запущена. Закройте предыдущее окно.")
