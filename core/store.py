from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, created_at);
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY, offer_id TEXT NOT NULL, score REAL NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opportunities_offer ON opportunities(offer_id);
CREATE TABLE IF NOT EXISTS offers (
    id TEXT PRIMARY KEY, network TEXT NOT NULL, name TEXT NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, keyword TEXT NOT NULL, payload TEXT NOT NULL, captured_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_signals_keyword_time ON signals(keyword, captured_at);
CREATE TABLE IF NOT EXISTS content_plans (
    id TEXT PRIMARY KEY, offer_id TEXT NOT NULL, platform TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class SQLiteStore:
    """Dependency-light persistence boundary. It is safe by default and can be replaced by PostgreSQL later."""
    def __init__(self, path: str = "data/affiliate.db"):
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def append_event(self, event_id: str, event_type: str, payload: dict[str, Any], created_at: str) -> bool:
        cur = self.connection.execute("INSERT OR IGNORE INTO events(id,event_type,payload,created_at) VALUES(?,?,?,?)", (event_id, event_type, json.dumps(payload, separators=(",", ":"), sort_keys=True), created_at))
        self.connection.commit()
        return cur.rowcount == 1

    def save_offer(self, offer: dict[str, Any], updated_at: str) -> None:
        self.connection.execute("INSERT INTO offers(id,network,name,payload,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET network=excluded.network,name=excluded.name,payload=excluded.payload,updated_at=excluded.updated_at", (offer["id"], offer["network"], offer["name"], json.dumps(offer, sort_keys=True), updated_at))
        self.connection.commit()

    def save_opportunity(self, opportunity_id: str, offer_id: str, score: float, payload: dict[str, Any], created_at: str) -> None:
        self.connection.execute("INSERT OR REPLACE INTO opportunities(id,offer_id,score,payload,created_at) VALUES(?,?,?,?,?)", (opportunity_id, offer_id, score, json.dumps(payload, sort_keys=True), created_at))
        self.connection.commit()

    def save_signal(self, signal: dict[str, Any], captured_at: str) -> None:
        self.connection.execute("INSERT INTO signals(source,keyword,payload,captured_at) VALUES(?,?,?,?)", (signal["source"], signal["keyword"], json.dumps(signal, sort_keys=True), captured_at))
        self.connection.commit()

    def recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 1000)),)).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.connection.close()
