"""Small in-memory sliding-window rate limiter.

ponytail: per-process memory. With several backend instances (or restarts) the counts are not
shared; move to Redis or the database when deploying more than one instance.
"""
import math
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

# Requests from these addresses are our own Next.js proxy, so the real client is in X-Forwarded-For.
TRUSTED_PROXIES = {"127.0.0.1", "::1"}


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if peer in TRUSTED_PROXIES and forwarded:
        return forwarded.split(",")[0].strip()  # left-most = original client
    return peer


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, clock=time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        hits = self._hits[key]
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        return hits

    def retry_after(self, key: str) -> int | None:
        """Seconds until `key` may try again, or None if it is not blocked."""
        with self._lock:
            now = self._clock()
            hits = self._prune(key, now)
            if len(hits) < self.limit:
                return None
            return max(1, math.ceil(hits[0] + self.window - now))

    def record(self, key: str) -> None:
        with self._lock:
            self._prune(key, self._clock()).append(self._clock())

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()
