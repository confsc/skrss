import socket
import threading
import time
import os
import sys


def _get_shared_path():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, "..", ".."))
    return os.path.join(root, "shared")


sys.path.insert(0, _get_shared_path())
from config import (  # noqa: E402
    SERVER_PORT, BROADCAST_PORT, BROADCAST_INTERVAL, BROADCAST_MAGIC,
)


def get_local_ip():
    """
    Определяет IP-адрес в локальной сети.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip.startswith("127."):
                return "127.0.0.1"
            return ip
        except Exception:
            return "127.0.0.1"


class Broadcaster:

    def __init__(self):
        self.running = False
        self.thread = None
        self.local_ip = get_local_ip()
        self.sock = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            print(f"[Broadcast] Ошибка создания сокета: {e}")
            return

        message = f"{BROADCAST_MAGIC}:{self.local_ip}:{SERVER_PORT}".encode("utf-8")

        print(f"[Broadcast] IP: {self.local_ip}, порт: {BROADCAST_PORT}")
        print(f"[Broadcast] Сообщение: {message.decode()}")

        while self.running:
            try:
                self.sock.sendto(message, ("255.255.255.255", BROADCAST_PORT))
            except Exception as e:
                print(f"[Broadcast] Ошибка отправки: {e}")
            time.sleep(BROADCAST_INTERVAL)

    def get_info(self):
        return {
            "ip": self.local_ip,
            "port": SERVER_PORT,
            "broadcast_port": BROADCAST_PORT,
        }


if __name__ == "__main__":
    print("Тест broadcast. Нажми Ctrl+C для остановки.")
    b = Broadcaster()
    b.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        b.stop()
        print("\nОстановлено.")
