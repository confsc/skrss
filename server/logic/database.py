"""
Модуль работы с базой данных SQLite.
"""
import sqlite3
import os
import sys
import time
from datetime import datetime


def _get_shared_path():
    if hasattr(sys, "_MEIPASS"):
        shared = os.path.join(sys._MEIPASS, "shared")
        if os.path.exists(shared):
            return shared
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, "..", ".."))
    return os.path.join(root, "shared")


sys.path.insert(0, _get_shared_path())
from config import DB_FILENAME  # noqa: E402


def _get_db_path():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(os.path.dirname(sys.executable), DB_FILENAME)
    current = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(current, "..", ".."))
    return os.path.join(root, DB_FILENAME)


DB_PATH = _get_db_path()


class Database:

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                station_id TEXT,
                station_name TEXT,
                question_count INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                stopped INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                fio TEXT NOT NULL,
                group_name TEXT NOT NULL,
                station_id TEXT,
                station_name TEXT,
                status TEXT DEFAULT 'waiting',
                question_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                percent REAL DEFAULT 0,
                started_at TEXT,
                finished_at TEXT,
                duration INTEGER DEFAULT 0,
                last_heartbeat REAL DEFAULT 0,
                FOREIGN KEY (quiz_id) REFERENCES quiz_sessions(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                group_name TEXT NOT NULL,
                station_id TEXT,
                station_name TEXT,
                score REAL,
                percent REAL,
                correct_count INTEGER,
                question_count INTEGER,
                duration INTEGER,
                finished_at TEXT
            )
        """)

        self.conn.commit()

    # ---------- Летучки ----------

    def create_quiz(self, topic, station_id=None, station_name=None, question_count=7):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO quiz_sessions
            (topic, station_id, station_name, question_count, started_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            topic,
            station_id,
            station_name,
            question_count,
            datetime.now().isoformat(timespec="seconds"),
        ))
        self.conn.commit()
        return cur.lastrowid

    def get_active_quiz(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM quiz_sessions
            WHERE stopped = 0
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        return dict(row) if row else None

    def stop_quiz(self, quiz_id):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE quiz_sessions SET stopped = 1 WHERE id = ?",
            (quiz_id,)
        )
        cur.execute("""
            UPDATE students SET status = 'interrupted'
            WHERE quiz_id = ? AND status IN ('waiting', 'in_progress')
        """, (quiz_id,))
        self.conn.commit()

    # ---------- Студенты ----------

    def add_student(self, quiz_id, fio, group_name):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO students
            (quiz_id, fio, group_name, status, last_heartbeat)
            VALUES (?, ?, ?, 'waiting', ?)
        """, (quiz_id, fio, group_name, time.time()))
        self.conn.commit()
        return cur.lastrowid

    def find_student(self, quiz_id, fio, group_name):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM students
            WHERE quiz_id = ? AND fio = ? AND group_name = ?
            ORDER BY id DESC LIMIT 1
        """, (quiz_id, fio, group_name))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_student_start(self, student_id, station_id, station_name, question_count):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE students
            SET station_id = ?, station_name = ?, status = 'in_progress',
                question_count = ?, started_at = ?, last_heartbeat = ?
            WHERE id = ?
        """, (
            station_id,
            station_name,
            question_count,
            datetime.now().isoformat(timespec="seconds"),
            time.time(),
            student_id,
        ))
        self.conn.commit()

    def update_student_finish(self, student_id, correct_count, score, percent, duration):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE students
            SET status = 'finished', correct_count = ?, score = ?,
                percent = ?, duration = ?, finished_at = ?
            WHERE id = ?
        """, (
            correct_count,
            score,
            percent,
            duration,
            datetime.now().isoformat(timespec="seconds"),
            student_id,
        ))
        self.conn.commit()

    def update_heartbeat(self, student_id):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE students SET last_heartbeat = ? WHERE id = ?",
            (time.time(), student_id)
        )
        self.conn.commit()

    def get_all_students(self, quiz_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM students WHERE quiz_id = ?
            ORDER BY id
        """, (quiz_id,))
        return [dict(row) for row in cur.fetchall()]

    def check_timeouts(self, quiz_id, timeout_seconds):
        now = time.time()
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM students
            WHERE quiz_id = ? AND status IN ('waiting', 'in_progress')
        """, (quiz_id,))
        students = [dict(r) for r in cur.fetchall()]

        for s in students:
            last = s.get("last_heartbeat") or 0
            if now - last > timeout_seconds:
                cur.execute(
                    "UPDATE students SET status = 'interrupted' WHERE id = ?",
                    (s["id"],)
                )
        self.conn.commit()

    # ---------- История ----------

    def save_attempt(self, fio, group_name, station_id, station_name,
                     score, percent, correct_count, question_count, duration):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO attempts
            (fio, group_name, station_id, station_name, score, percent,
             correct_count, question_count, duration, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fio,
            group_name,
            station_id,
            station_name,
            score,
            percent,
            correct_count,
            question_count,
            duration,
            datetime.now().isoformat(timespec="seconds"),
        ))
        self.conn.commit()

    def get_student_history(self, fio, group_name):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM attempts
            WHERE fio = ? AND group_name = ?
            ORDER BY id DESC
        """, (fio, group_name))
        return [dict(r) for r in cur.fetchall()]

    def get_all_attempts(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM attempts ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    db = Database()
    print(f"База данных создана: {db.db_path}")
    print("Таблицы:")
    cur = db.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cur.fetchall():
        print(f"  - {row[0]}")
    db.close()