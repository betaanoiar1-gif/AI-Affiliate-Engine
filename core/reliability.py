from __future__ import annotations
import random
import time
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], *, attempts: int = 3, base_delay: float = 0.25, max_delay: float = 5.0) -> T:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:  # providers are untrusted boundaries
            last = exc
            if attempt == attempts - 1:
                break
            delay = min(max_delay, base_delay * (2 ** attempt)) * (0.8 + random.random() * 0.4)
            time.sleep(delay)
    assert last is not None
    raise last


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_seconds: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()


class RateLimiter:
    def __init__(self, calls: int, period_seconds: float = 60.0):
        if calls < 1 or period_seconds <= 0:
            raise ValueError("invalid rate limit")
        self.calls = calls
        self.period = period_seconds
        self.timestamps: list[float] = []
        self.lock = Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.timestamps = [t for t in self.timestamps if now - t < self.period]
                if len(self.timestamps) < self.calls:
                    self.timestamps.append(now)
                    return
                wait = self.period - (now - self.timestamps[0])
            time.sleep(max(0.01, wait))
