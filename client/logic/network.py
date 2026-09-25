"""
Сетевой модуль клиента.
"""
import socket
import time
import json
import os
import sys
import requests


BROADCAST_PORT = 5001
CLIENT_SEARCH_TIMEOUT = 3
BROADCAST_MAGIC = "RRS_TRAINER_SERVER"

API_PING = "/api/ping"
API_QUIZ_INFO = "/api/quiz_info"
API_START = "/api/start"
API_FINISH = "/api/finish"
API_HEARTBEAT = "/api/heartbeat"

SERVER_PORT = 5000


class ServerFinder:

    def __init__(self):
        self.found_ip = None
        self.found_port = None

    def find(self, timeout=None):
        if timeout is None:
            timeout = CLIENT_SEARCH_TIMEOUT

        self.found_ip = None
        self.found_port = None

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", BROADCAST_PORT))
            sock.settimeout(timeout)

            start = time.time()
            while time.time() - start < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    break

                try:
                    message = data.decode("utf-8")
                except Exception:
                    continue

                if message.startswith(BROADCAST_MAGIC + ":"):
                    parts = message.split(":")
                    if len(parts) >= 3:
                        ip = parts[1]
                        port = int(parts[2])
                        self.found_ip = ip
                        self.found_port = port
                        return True
        except Exception as e:
            print(f"[Finder] Ошибка: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

        return False


def try_direct_ip(ip, port=None):
    if port is None:
        port = SERVER_PORT

    ip = (ip or "").strip()
    if not ip:
        return None

    ip = ip.replace("http://", "").replace("https://", "").strip("/")
    if ":" in ip:
        try:
            ip, p = ip.split(":", 1)
            port = int(p)
        except Exception:
            pass

    api = ApiClient(ip, port)
    if api.ping():
        return (ip, port)
    return None


class ApiClient:

    def __init__(self, ip, port):
        self.base_url = f"http://{ip}:{port}"
        self.timeout = 10

    def ping(self):
        try:
            r = requests.get(self.base_url + API_PING, timeout=self.timeout)
            return r.json().get("status") == "ok"
        except Exception:
            return False

    def quiz_info(self):
        try:
            r = requests.get(self.base_url + API_QUIZ_INFO, timeout=self.timeout)
            return r.json()
        except Exception as e:
            print(f"[API] quiz_info: {e}")
            return {"active": False}

    def start_quiz(self, fio, group_name):
        try:
            r = requests.post(
                self.base_url + API_START,
                json={"fio": fio, "group": group_name},
                timeout=self.timeout,
            )
            return r.status_code, r.json()
        except Exception as e:
            print(f"[API] start_quiz: {e}")
            return 0, {"status": "error", "message": str(e)}

    def finish_quiz(self, student_id, correct_count, score, percent, duration):
        try:
            r = requests.post(
                self.base_url + API_FINISH,
                json={
                    "student_id": student_id,
                    "correct_count": correct_count,
                    "score": score,
                    "percent": percent,
                    "duration": duration,
                },
                timeout=self.timeout,
            )
            return r.status_code == 200
        except Exception as e:
            print(f"[API] finish_quiz: {e}")
            return False

    def heartbeat(self, student_id):
        try:
            requests.post(
                self.base_url + API_HEARTBEAT,
                json={"student_id": student_id},
                timeout=self.timeout,
            )
        except Exception:
            pass


if __name__ == "__main__":
    print("Поиск сервера...")
    f = ServerFinder()
    if f.find():
        print(f"Сервер найден: {f.found_ip}:{f.found_port}")
        api = ApiClient(f.found_ip, f.found_port)
        print(f"Ping: {api.ping()}")
    else:
        print("Сервер не найден.")
