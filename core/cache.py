from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class TTLCache:
    """Small persistent cache that reduces repeated public requests and quota usage."""

    def __init__(self, path: str = "data/cache.db") -> None:
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires_at REAL NOT NULL)")
        self.connection.commit()

    @staticmethod
    def key(namespace: str, value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, key: str) -> Any | None:
        row = self.connection.execute("SELECT value, expires_at FROM cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        if row[1] <= time.time():
            self.connection.execute("DELETE FROM cache WHERE key=?", (key,))
            self.connection.commit()
            return None
        return json.loads(row[0])

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        expires = time.time() + max(0.0, ttl_seconds)
        self.connection.execute("INSERT OR REPLACE INTO cache(key,value,expires_at) VALUES(?,?,?)", (key, json.dumps(value, default=str), expires))
        self.connection.commit()

    def purge_expired(self) -> int:
        cur = self.connection.execute("DELETE FROM cache WHERE expires_at <= ?", (time.time(),))
        self.connection.commit()
        return cur.rowcount

    def close(self) -> None:
        self.connection.close()
