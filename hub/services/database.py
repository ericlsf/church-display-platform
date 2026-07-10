import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from services.config import CONFIG_DIR

DB_PATH = CONFIG_DIR / "hub.sqlite3"


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()


def initialize_database():
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL DEFAULT 'general',
                level TEXT NOT NULL DEFAULT 'info',
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
            """
        )


def record_event(message, category="general", level="info", metadata=None):
    initialize_database()
    with connection() as db:
        db.execute(
            "INSERT INTO events(category, level, message, metadata_json) VALUES (?, ?, ?, ?)",
            (category, level, str(message), json.dumps(metadata or {}, sort_keys=True)),
        )


def recent_events(limit=100):
    initialize_database()
    with connection() as db:
        rows = db.execute(
            "SELECT created_at, category, level, message, metadata_json FROM events ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 1000)),),
        ).fetchall()
    return [dict(row) for row in rows]
