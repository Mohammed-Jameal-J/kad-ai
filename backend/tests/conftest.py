import os
import tempfile
from pathlib import Path

import pytest

# Must be set before `app` is imported, so the engine points at a throwaway database.
_tmp = Path(tempfile.mkdtemp(prefix="kadai-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["OLLAMA_PREWARM"] = "false"  # tests never touch a real Ollama
os.environ["RESEND_API_KEY"] = ""  # ...or send real email, even if .env has a key
os.environ["SERPER_API_KEY"] = ""  # ...or search the web
os.environ["GROQ_API_KEY"] = ""
os.environ["LLM_PROVIDER"] = "ollama"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # `with` runs the lifespan, which creates tables and seeds
        yield c


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Rate limiters are process-wide; start every test with clean counters."""
    from app.ai import groq, websearch
    from app.api import assistant, auth, cart, orders
    for limiter in (auth.LOGIN_FAILURES, auth.LOGIN_FAILURES_PER_IP, auth.REGISTRATIONS_PER_IP, auth.CONTACT_PER_IP, auth.NEWSLETTER_PER_IP,
                    assistant.CHAT_PER_IP, cart.CART_WRITES_PER_IP, orders.ORDERS_PER_IP,
                    groq.DAILY, websearch.DAILY, websearch.PER_IP):
        limiter.clear()


@pytest.fixture(scope="session")
def product_id(client):
    def lookup(slug: str) -> int:
        return client.get(f"/api/products/{slug}").json()["id"]
    return lookup
