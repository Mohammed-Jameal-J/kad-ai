"""Resend emails: sent in the background, escaped, and never able to break a request."""
from uuid import uuid4

import httpx

from app.core.config import settings
from app.services import email

PASSWORD = "Test-pass-12345"


def test_register_queues_a_welcome_email(client, monkeypatch):
    sent = []
    monkeypatch.setattr(email, "send_welcome", lambda to, name: sent.append((to, name)))
    addr = f"w-{uuid4().hex[:8]}@example.com"
    assert client.post("/api/auth/register", json={"name": "Asha Devi", "email": addr, "password": PASSWORD}).status_code == 201
    client.post("/api/auth/logout")
    assert sent == [(addr, "Asha Devi")]


def test_newsletter_confirms_new_addresses_only_and_answers_the_same(client, monkeypatch):
    sent = []
    monkeypatch.setattr(email, "send_newsletter_confirmation", sent.append)
    addr = f"n-{uuid4().hex[:8]}@Example.com"
    first = client.post("/api/newsletter", json={"email": addr})
    again = client.post("/api/newsletter", json={"email": addr.lower()})
    assert first.status_code == again.status_code == 201 and first.json() == again.json()  # no "already subscribed" leak
    assert sent == [addr.lower()]
    assert client.post("/api/newsletter", json={"email": "not-an-email"}).status_code == 422


def test_newsletter_is_rate_limited(client):
    codes = [client.post("/api/newsletter", json={"email": f"r{i}-{uuid4().hex[:6]}@example.com"}).status_code for i in range(6)]
    assert codes == [201] * 5 + [429]


def test_names_are_escaped_and_failures_never_raise(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "resend_api_key", "re_test")

    def fake_post(url, headers, json, timeout):
        calls.append(json)
        return httpx.Response(403, request=httpx.Request("POST", url))  # e.g. sandbox sender, other recipient

    monkeypatch.setattr(httpx, "post", fake_post)
    assert email.send_welcome("a@example.com", "<script>x</script> Bad") is False
    assert "<script>" not in calls[0]["html"] and "&lt;script&gt;" in calls[0]["html"]

    monkeypatch.setattr(httpx, "post", lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("down")))
    assert email.send_newsletter_confirmation("a@example.com") is False


def test_no_key_means_nothing_is_sent(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call Resend")))
    assert email.send_welcome("a@example.com", "Asha") is False


def test_newsletter_email_has_links_and_replies_reach_the_owner(monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: calls.append(json) or httpx.Response(200, request=httpx.Request("POST", url)))
    assert email.send_newsletter_confirmation("fan@example.com") is True
    sent = calls[0]
    assert sent["subject"] == "Thanks for testing Kad AI" and sent["reply_to"] == email.OWNER_EMAIL
    for link in (email.GITHUB, email.LINKEDIN, f"{settings.site_url}/register", f"mailto:{email.OWNER_EMAIL}"):
        assert link in sent["html"]
