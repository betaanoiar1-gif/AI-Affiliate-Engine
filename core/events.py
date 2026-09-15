from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class Event:
    id: str
    type: str
    payload: dict[str, Any]
    created_at: str


def make_event(event_type: str, payload: dict[str, Any], *, key: str | None = None) -> Event:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    material = f"{event_type}:{key or canonical}".encode()
    event_id = hashlib.sha256(material).hexdigest()
    return Event(event_id, event_type, payload, datetime.now(timezone.utc).isoformat())
