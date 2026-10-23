from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.ratelimit import RateLimiter, client_ip
from app.main import app

pytestmark = pytest.mark.usefixtures("client")
PASSWORD = "correct horse battery"


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_sliding_window():
    clock = FakeClock()
    limiter = RateLimiter(limit=3, window_seconds=60, clock=clock)
    for _ in range(3):
        assert limiter.retry_after("k") is None
        limiter.record("k")
    assert limiter.retry_after("k") == 60
    clock.now += 45
    assert limiter.retry_after("k") == 15
    clock.now += 15  # the oldest attempt has left the window
    assert limiter.retry_after("k") is None
    assert limiter.retry_after("other") is None  # keys are independent


def _request(peer: str, forwarded: str | None = None) -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
    return Request({"type": "http", "client": (peer, 1234), "headers": headers})


def test_forwarded_header_trusted_only_from_our_proxy():
    assert client_ip(_request("127.0.0.1", "203.0.113.7, 10.0.0.1")) == "203.0.113.7"
    assert client_ip(_request("198.51.100.9", "203.0.113.7")) == "198.51.100.9"  # spoofing attempt ignored
    assert client_ip(_request("198.51.100.9")) == "198.51.100.9"


@pytest.fixture
def account():
    email = f"rl-{uuid4().hex[:8]}@example.com"
    with TestClient(app) as c:
        assert c.post("/api/auth/register", json={"name": "Rate Test", "email": email, "password": PASSWORD}).status_code == 201
        c.post("/api/auth/logout")
        yield c, email


def login(c, email, password, **headers):
    return c.post("/api/auth/login", json={"email": email, "password": password}, headers=headers)


def test_too_many_wrong_passwords_locks_login(account):
    c, email = account
    for _ in range(5):
        assert login(c, email, "wrong-password").status_code == 401
    blocked = login(c, email, PASSWORD)  # even the right password is refused while locked
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert "Too many attempts" in blocked.json()["detail"]


def test_successful_login_resets_the_counter(account):
    c, email = account
    for _ in range(4):
        login(c, email, "wrong-password")
    assert login(c, email, PASSWORD).status_code == 200
    for _ in range(4):
        assert login(c, email, "wrong-password").status_code == 401  # fresh budget, not locked yet


def test_spoofed_forwarded_header_does_not_bypass_the_limit(account):
    c, email = account
    for i in range(5):
        login(c, email, "wrong-password", **{"X-Forwarded-For": f"10.0.0.{i}"})
    assert login(c, email, PASSWORD, **{"X-Forwarded-For": "10.9.9.9"}).status_code == 429


def test_password_spraying_across_emails_is_limited():
    with TestClient(app) as c:
        statuses = [login(c, f"nobody-{i}@example.com", "guess").status_code for i in range(21)]
    assert statuses[:20] == [401] * 20 and statuses[20] == 429


def test_registration_and_contact_are_limited_per_ip():
    with TestClient(app) as c:
        for i in range(10):
            c.post("/api/auth/register", json={"name": "Spam", "email": f"spam-{uuid4().hex[:6]}@example.com", "password": PASSWORD})
        r = c.post("/api/auth/register", json={"name": "Spam", "email": f"spam-{uuid4().hex[:6]}@example.com", "password": PASSWORD})
        assert r.status_code == 429
        msg = {"name": "Spam", "email": "s@example.com", "message": "Buy cheap stuff now please"}
        assert [c.post("/api/contact", json=msg).status_code for _ in range(6)] == [201] * 5 + [429]
