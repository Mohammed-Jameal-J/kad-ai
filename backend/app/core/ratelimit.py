"""Small in-memory sliding-window rate limiter.

ponytail: per-process memory. With several backend instances (or restarts) the counts are not
shared; move to Redis or the database when deploying more than one instance.
"""
import math
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.errors import TooManyAttempts

def client_ip(request: Request) -> str:
    """The address to rate-limit on.

    X-Forwarded-For is NOT trusted by default: the Next.js rewrite proxy passes on whatever the
    browser sent, so anyone could pick a new fake IP per request. Locally every request therefore
    counts as 127.0.0.1 (one shared budget). When deployed behind an edge that overwrites a header
    with the real client IP (Vercel: x-real-ip, nginx: X-Real-IP $remote_addr), set
    TRUSTED_IP_HEADER to it, and make sure the backend is reachable only through that edge.
    Run uvicorn with --no-proxy-headers, or it rewrites request.client from the spoofable header.
    """
    if settings.trusted_ip_header and (value := request.headers.get(settings.trusted_ip_header)):
        return value.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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


def enforce(limiter: RateLimiter, key: str) -> None:
    """Count one request for `key`; 429 with Retry-After once it is over the limit."""
    if wait := limiter.retry_after(key):
        raise TooManyAttempts(wait)
    limiter.record(key)
