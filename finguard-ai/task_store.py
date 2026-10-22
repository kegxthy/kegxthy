"""SQLite task persistence; one Uvicorn worker only."""

import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self):
        self.path = Path(os.getenv("FINGUARD_DB", "data/tasks.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_hours = int(os.getenv("FINGUARD_RETENTION_HOURS", "24"))
        if not 1 <= self.retention_hours <= 168:
            raise ValueError("FINGUARD_RETENTION_HOURS must be between 1 and 168")
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA secure_delete=ON")
        return db

    def save(self, task):
        task["updated_at"] = now()
        created = datetime.fromisoformat(task.get("created_at", task["updated_at"]))
        deadline = created + timedelta(hours=self.retention_hours)
        # Policy changes may shorten, never silently extend existing retention.
        previous = datetime.fromisoformat(task.get("expires_at", deadline.isoformat()))
        task["expires_at"] = min(deadline, previous).isoformat()
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

    def cleanup(self, active_ids=(), at=None):
        cutoff = at or datetime.now(timezone.utc)
        removed = 0
        for task in self.all():
            created = datetime.fromisoformat(task.get("created_at", task["updated_at"]))
            deadline = created + timedelta(hours=self.retention_hours)
            if "expires_at" in task:
                deadline = min(deadline, datetime.fromisoformat(task["expires_at"]))
            if task["id"] not in active_ids and deadline <= cutoff:
                self.delete(task["id"])
                removed += 1
        return removed

    def stored_bytes(self):
        with self.connect() as db:
            return db.execute(
                "SELECT COALESCE(SUM(length(CAST(body AS BLOB))),0) FROM tasks"
            ).fetchone()[0]

    def backup(self, destination):
        destination = Path(destination)
        if destination.resolve() == self.path.resolve() or destination.exists():
            raise ValueError("Backup destination must be a new, separate file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
