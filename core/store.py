from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, created_at);
CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, offer_id TEXT NOT NULL, score REAL NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_opportunities_offer ON opportunities(offer_id);
CREATE TABLE IF NOT EXISTS offers (id TEXT PRIMARY KEY, network TEXT NOT NULL, name TEXT NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, keyword TEXT NOT NULL, payload TEXT NOT NULL, captured_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_signals_keyword_time ON signals(keyword, captured_at);
CREATE TABLE IF NOT EXISTS content_plans (id TEXT PRIMARY KEY, offer_id TEXT NOT NULL, platform TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS experiments (id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS clicks (id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL, variant_id TEXT, source TEXT, medium TEXT, content_id TEXT, offer_id TEXT NOT NULL, clicked_at TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_clicks_campaign ON clicks(campaign_id, clicked_at);
CREATE TABLE IF NOT EXISTS conversions (id TEXT PRIMARY KEY, click_id TEXT, offer_id TEXT NOT NULL, amount REAL NOT NULL, commission REAL NOT NULL, currency TEXT NOT NULL, converted_at TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_conversions_offer_time ON conversions(offer_id, converted_at);
CREATE TABLE IF NOT EXISTS audit_log (id TEXT PRIMARY KEY, action TEXT NOT NULL, actor TEXT NOT NULL, outcome TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at);
"""


class SQLiteStore:
    """Durable persistence boundary with idempotent events and attribution primitives."""

    def __init__(self, path: str = "data/affiliate.db"):
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.executescript(SCHEMA)
        if self.connection.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 0:
            self.connection.execute("INSERT INTO schema_version(version) VALUES(1)")
        self.connection.commit()

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)

    def append_event(self, event_id: str, event_type: str, payload: dict[str, Any], created_at: str) -> bool:
        cur = self.connection.execute("INSERT OR IGNORE INTO events(id,event_type,payload,created_at) VALUES(?,?,?,?)", (event_id, event_type, self._json(payload), created_at))
        self.connection.commit()
        return cur.rowcount == 1

    def save_offer(self, offer: dict[str, Any], updated_at: str) -> None:
        self.connection.execute("INSERT INTO offers(id,network,name,payload,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET network=excluded.network,name=excluded.name,payload=excluded.payload,updated_at=excluded.updated_at", (offer["id"], offer["network"], offer["name"], self._json(offer), updated_at))
        self.connection.commit()

    def save_opportunity(self, opportunity_id: str, offer_id: str, score: float, payload: dict[str, Any], created_at: str) -> None:
        self.connection.execute("INSERT OR REPLACE INTO opportunities(id,offer_id,score,payload,created_at) VALUES(?,?,?,?,?)", (opportunity_id, offer_id, score, self._json(payload), created_at))
        self.connection.commit()

    def save_signal(self, signal: dict[str, Any], captured_at: str) -> None:
        self.connection.execute("INSERT INTO signals(source,keyword,payload,captured_at) VALUES(?,?,?,?)", (signal["source"], signal["keyword"], self._json(signal), captured_at))
        self.connection.commit()

    def save_click(self, click: dict[str, Any]) -> bool:
        cur = self.connection.execute("INSERT OR IGNORE INTO clicks(id,campaign_id,variant_id,source,medium,content_id,offer_id,clicked_at,metadata) VALUES(?,?,?,?,?,?,?,?,?)", (click["id"], click["campaign_id"], click.get("variant_id"), click.get("source"), click.get("medium"), click.get("content_id"), click["offer_id"], click["clicked_at"], self._json(click.get("metadata", {}))))
        self.connection.commit()
        return cur.rowcount == 1

    def save_conversion(self, conversion: dict[str, Any]) -> bool:
        cur = self.connection.execute("INSERT OR IGNORE INTO conversions(id,click_id,offer_id,amount,commission,currency,converted_at,metadata) VALUES(?,?,?,?,?,?,?,?)", (conversion["id"], conversion.get("click_id"), conversion["offer_id"], conversion["amount"], conversion["commission"], conversion["currency"], conversion["converted_at"], self._json(conversion.get("metadata", {}))))
        self.connection.commit()
        return cur.rowcount == 1

    def audit(self, event_id: str, action: str, actor: str, outcome: str, payload: dict[str, Any], created_at: str) -> None:
        self.connection.execute("INSERT OR IGNORE INTO audit_log(id,action,actor,outcome,payload,created_at) VALUES(?,?,?,?,?,?)", (event_id, action, actor, outcome, self._json(payload), created_at))
        self.connection.commit()

    def recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 1000)),)).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict[str, int]:
        tables = ("events", "opportunities", "offers", "signals", "content_plans", "experiments", "clicks", "conversions", "audit_log")
        return {table: int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}

    def close(self) -> None:
        self.connection.close()
