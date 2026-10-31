"""Tablero de trabajo persistente estilo Codex (no ejecuta comandos remotos)."""
import sqlite3
from datetime import datetime, timezone


class TaskStore:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks ("
                       "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
                       "detail TEXT NOT NULL, status TEXT NOT NULL, "
                       "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    def list(self):
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(row) for row in rows]
    def create(self, title, detail=""):
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120 or (
            not isinstance(detail, str) or len(detail) > 2000):
            raise ValueError("Título o detalle inválido")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("INSERT INTO tasks(title,detail,status,created_at,updated_at) "
                                "VALUES(?,?,?,?,?)",
                                (title.strip(), detail, "todo", now, now))
            return {"id": cursor.lastrowid, "title": title.strip(),
                    "detail": detail, "status": "todo", "created_at": now}
    def set_status(self, task_id, status):
        if type(task_id) is not int or task_id < 1 or status not in ("todo","doing","done"):
            raise ValueError("ID o estado de tarea inválido")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with sqlite3.connect(self.path) as db:
            result = db.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?",
                                (status, now, task_id))
            if not result.rowcount:
                raise ValueError("Tarea no encontrada")
        return {"id": task_id, "status": status}
