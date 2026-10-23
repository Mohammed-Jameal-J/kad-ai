"""Stage 8: the deterministic parts of the CrewAI integration. These run without CrewAI installed;
the full multi-agent run is exercised live by scripts/compare_direct_vs_crew.py."""
import importlib.util

import pytest
from sqlalchemy import func, select

from app.ai.ollama import get_ollama
from app.crew import tools
from app.crew.validation import validate_basket
from app.db.session import SessionLocal
from app.main import app
from app.models import Cart, Order, Product
from fakes import FakeOllama, make_client

HAS_CREWAI = importlib.util.find_spec("crewai") is not None
pytestmark = pytest.mark.usefixtures("client")  # the client fixture creates and seeds the test database


@pytest.fixture(autouse=True)
def crew_on(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "crew_enabled", True)


def pid(slug):
    with SessionLocal() as db:
        return db.scalar(select(Product.id).where(Product.slug == slug))


def snapshot():
    """Everything a tool must never change."""
    with SessionLocal() as db:
        return (
            tuple(db.scalars(select(Product.stock_quantity).order_by(Product.id))),
            db.scalar(select(func.count()).select_from(Cart)),
            db.scalar(select(func.count()).select_from(Order)),
        )


# --- final validation step -------------------------------------------------------------------

def test_validation_drops_invented_and_out_of_stock_products():
    with SessionLocal() as db:
        r = validate_basket(db, [(999999, 1), (pid("green-kiwi"), 1), (pid("robusta-banana"), 1)], None)
    assert [l["name"] for l in r["lines"]] == ["Robusta Banana"]
    assert any("999999 does not exist" in p for p in r["problems"])
    assert any("Green Kiwi is out of stock" in p for p in r["problems"])


def test_validation_clamps_quantity_and_merges_duplicates():
    mango = pid("alphonso-mango")  # stock 25
    with SessionLocal() as db:
        r = validate_basket(db, [(mango, 20), (mango, 20)], None)
    assert r["lines"][0]["quantity"] == 25
    assert any("from 40 to 25" in p for p in r["problems"])


def test_validation_enforces_budget_with_db_prices():
    items = [(pid("shimla-apple"), 1), (pid("robusta-banana"), 1), (pid("alphonso-mango"), 1)]  # 180 + 60 + 600
    with SessionLocal() as db:
        r = validate_basket(db, items, budget_paise=30000)
    assert r["total_paise"] == 18000 + 6000
    assert r["remaining_paise"] == 30000 - 24000
    assert any("Removed Alphonso Mango" in p for p in r["problems"])


# --- tools: read-only, real data --------------------------------------------------------------

def test_tools_are_read_only():
    before = snapshot()
    tools.search_products("apple")
    tools.search_products(category="vegetables", max_price_inr=50)
    tools.get_nutrition(pid("robusta-banana"))
    tools.quote_basket([pid("shimla-apple"), pid("lemon")], [2, 1], budget_inr=500)
    assert snapshot() == before


def test_search_tool_returns_only_in_stock_db_products():
    rows = tools.search_products(category="fruit", max_price_inr=100)  # "fruit" is normalised to "fruits"
    assert rows and all(r["stock"] > 0 for r in rows)
    assert "Green Kiwi" not in {r["name"] for r in rows}
    assert tools.search_products("strawberry") == []
    assert tools.search_products(category="spaceships")  # unknown category is ignored, not an error


def test_nutrition_tool_says_unavailable_instead_of_guessing():
    r = tools.get_nutrition(pid("robusta-banana"))
    assert r["verified"] is False and "Do not guess" in r["message"]
    assert tools.get_nutrition(999999) == {"product_id": 999999, "error": "No such product."}


def test_quote_tool_total_comes_from_database():
    r = tools.quote_basket([pid("shimla-apple"), pid("lemon")], [2, 1], budget_inr=500)
    assert r["total"] == "₹400" and r["within_budget"] is True
    over = tools.quote_basket([pid("alphonso-mango"), pid("lemon")], [1, 1], budget_inr=100)
    assert over["within_budget"] is False and over["total"] == "₹640"
    # the most expensive line goes first, so the cheap lemon survives
    assert over["suggestion_within_budget"] == {"lines": ["1 x 250 g Lemon = ₹40"], "total": "₹40"}


# --- memory control and routing --------------------------------------------------------------

def test_exclusive_unloads_other_models_first():
    fake = FakeOllama(loaded=["qwen3:4b", "llama3.2:latest"])
    with make_client(fake).exclusive("llama3.2"):
        pass
    assert fake.bodies("/api/generate") == [{"model": "qwen3:4b", "keep_alive": 0}]


@pytest.mark.skipif(not HAS_CREWAI, reason="CrewAI not installed in this environment")
def test_crew_routing_heuristic():
    from app.crew.workflow import crew_recommended
    assert crew_recommended("Suggest healthy fruits for my family within ₹500")
    assert not crew_recommended("Show me mangoes")
    assert not crew_recommended("healthy fruits please")  # no budget: direct assistant is enough


@pytest.mark.skipif(not HAS_CREWAI, reason="CrewAI not installed in this environment")
def test_planner_output_is_resolved_only_through_the_database():
    from app.crew.workflow import BasketProposal, resolve_items
    # What llama3.2 really produced: whole tool rows, names instead of ids, junk.
    proposal = BasketProposal.model_validate({"items": [
        {"product_id": pid("shimla-apple"), "name": "Shimla Apple", "price": "₹180 per kg", "stock": 118},
        {"product_id": "bananas", "quantity": 2},
        {"product_id": "dragon fruit"},  # not sold: dropped
        {"product_id": str(pid("lemon")), "quantity": 99},  # clamped
    ]})
    assert resolve_items(proposal.items) == [(pid("shimla-apple"), 1), (pid("robusta-banana"), 2), (pid("lemon"), 50)]


@pytest.mark.skipif(not HAS_CREWAI, reason="CrewAI not installed in this environment")
def test_crew_result_is_validated_and_returned_as_pending_action(client, monkeypatch):
    """Whole post-processing path with a fake crew result (no LLM): invented product dropped,
    budget enforced with DB prices, explanation with a fake price removed, cart untouched."""
    from types import SimpleNamespace

    from crewai import Crew

    from app.crew.workflow import BasketProposal

    proposal = BasketProposal.model_validate({
        "items": [{"product_id": pid("shimla-apple")}, {"product_id": "bananas"}, {"product_id": 999999},
                  {"product_id": pid("alphonso-mango")}],
        "explanation": "Apples are only ₹5 today!",
    })
    def fake_kickoff(self, inputs=None):
        # the nutrition task's raw text, as the real agent writes it (includes a product not in the basket)
        self.tasks[1].output = SimpleNamespace(raw="- No verified nutrition data for Shimla Apple.\n- No verified nutrition data for Nagpur Orange.")
        return SimpleNamespace(pydantic=proposal)

    monkeypatch.setattr(Crew, "kickoff", fake_kickoff)
    carts_before = snapshot()[1]
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama())
    try:
        r = client.post("/api/assistant/crew", json={"message": "healthy fruits for my family within ₹300"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["parser"] == "crewai"
    assert [p["slug"] for p in body["products"]] == ["shimla-apple", "robusta-banana"]  # mango removed for budget
    assert body["basket"]["total_paise"] == 18000 + 6000 <= body["basket"]["budget_paise"] == 30000
    assert body["pending_action"]["items"] == [{"product_id": pid("shimla-apple"), "quantity": 1}, {"product_id": pid("robusta-banana"), "quantity": 1}]
    assert "₹5" not in body["reply"]
    assert "Shimla Apple" in body["reply"].split("Nutrition notes:")[1]
    assert "Nagpur Orange" not in body["reply"]  # note about a product that is not in the basket: dropped
    assert any("999999 does not exist" in n for n in body["notes"])
    assert snapshot()[1] == carts_before  # nothing was added to any cart


@pytest.mark.skipif(not HAS_CREWAI, reason="CrewAI not installed in this environment")
def test_crew_failure_is_a_clear_502_not_a_500(client, monkeypatch):
    from crewai import Crew

    def explode(*_args, **_kwargs):
        raise ValueError("model returned garbage")

    monkeypatch.setattr(Crew, "kickoff", explode)
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama())
    try:
        r = client.post("/api/assistant/crew", json={"message": "healthy fruits within ₹500"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 502
    assert "regular assistant" in r.json()["detail"]


@pytest.mark.skipif(HAS_CREWAI, reason="only meaningful where CrewAI is NOT installed")
def test_crew_endpoint_explains_when_crewai_missing(client):
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama())
    try:
        r = client.post("/api/assistant/crew", json={"message": "healthy fruits within ₹500"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 501
    assert ".venv-crewai" in r.json()["detail"]


def test_crew_request_validation(client):
    assert client.post("/api/assistant/crew", json={"message": ""}).status_code == 422
    assert client.post("/api/assistant/crew", json={"message": "x", "budget_inr": 0}).status_code == 422
    assert client.post("/api/assistant/crew", json={"message": "x", "tools": ["shell"]}).status_code == 422


def test_crew_endpoint_is_off_by_default(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "crew_enabled", False)
    r = client.post("/api/assistant/crew", json={"message": "healthy fruits within ₹500"})
    assert r.status_code == 501
    assert "CREW_ENABLED" in r.json()["detail"]
