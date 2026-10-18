"""SQLite task persistence; one Uvicorn worker only."""

import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self):
        self.path = Path(os.getenv("FINGUARD_DB", "data/tasks.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, task):
        task["updated_at"] = now()
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO tasks VALUES (?,?)",
                (task["id"], json.dumps(task, ensure_ascii=False)),
            )

    def get(self, token):
        with self.connect() as db:
            row = db.execute("SELECT body FROM tasks WHERE id=?", (token,)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM tasks ORDER BY rowid DESC").fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, token):
        with self.connect() as db:
            db.execute("DELETE FROM tasks WHERE id=?", (token,))
