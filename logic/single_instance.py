"""
Защита от двойного запуска программы.
Работает через создание lock-файла во временной папке.
"""
import os
import sys
import tempfile
import atexit


LOCK_FILE = os.path.join(tempfile.gettempdir(), "rrs_trainer.lock")


def check_single_instance():
    """
    Проверяет, запущена ли уже программа.
    Если да — показывает сообщение и завершает процесс.
    Если нет — создаёт lock-файл.
    """
    if os.path.exists(LOCK_FILE):
        # Пытаемся понять, жив ли процесс
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())

            # Проверка: существует ли процесс с таким PID
            if _is_process_alive(old_pid):
                _show_already_running()
                sys.exit(0)
            else:
                # Процесс мёртв — удаляем старый lock и продолжаем
                os.remove(LOCK_FILE)
        except (ValueError, OSError):
            # Битый lock-файл — удаляем
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass

    # Создаём lock-файл с нашим PID
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Удаляем lock-файл при выходе
    atexit.register(_cleanup)


def _is_process_alive(pid):
    """Проверяет, жив ли процесс с указанным PID."""
    if sys.platform == "win32":
        # Windows
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        # Проверяем, завершился ли процесс
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        STILL_ACTIVE = 259
        return exit_code.value == STILL_ACTIVE
    else:
        # Linux / macOS
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _cleanup():
    """Удаляет lock-файл при выходе."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


def _show_already_running():
    """Показывает сообщение о двойном запуске."""
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
        # Если PyQt5 не сработал — хотя бы в консоль
        print("Программа уже запущена. Закройте предыдущее окно.")
