from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, created_at);
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    score REAL NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opportunities_offer ON opportunities(offer_id);
"""


class SQLiteStore:
    """Dependency-light persistent store; PostgreSQL can replace this behind the same service boundary."""
    def __init__(self, path: str = "data/affiliate.db"):
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def append_event(self, event_id: str, event_type: str, payload: dict[str, Any], created_at: str) -> bool:
        cur = self.connection.execute(
            "INSERT OR IGNORE INTO events(id,event_type,payload,created_at) VALUES(?,?,?,?)",
            (event_id, event_type, json.dumps(payload, separators=(",", ":"), sort_keys=True), created_at),
        )
        self.connection.commit()
        return cur.rowcount == 1

    def recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 1000)),)).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.connection.close()
