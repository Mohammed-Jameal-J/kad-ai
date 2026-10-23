"""Assistant tests with a fake Ollama: we control what the "LLM" says and check that the backend
never trusts it for prices, stock, totals or cart changes."""
import httpx
import pytest
from sqlalchemy import func, select

from app.ai.ollama import OllamaClient, get_ollama
from app.ai.parser import product_vocabulary, quick_parse, singular
from app.ai.writer import mentions_unknown_price
from app.db.session import SessionLocal
from app.main import app
from app.models import Cart, NutritionReference, Product
from fakes import FakeOllama, make_client

QWEN, LLAMA = "qwen3:4b", "llama3.2"


def parsed(intent, keywords=(), **fields):
    return {"intent": intent, "keywords": list(keywords), "category": None, "budget_inr": None,
            "quantity": None, "quantity_unit": None, "in_stock_only": False, **fields}


@pytest.fixture
def ask(client):
    """ask(message, fake=None) -> (response json, fake). Installs the fake Ollama for one call."""
    def _ask(message, fake=None, history=()):
        fake = fake or FakeOllama()
        app.dependency_overrides[get_ollama] = lambda: make_client(fake) if not isinstance(fake, OllamaClient) else fake
        try:
            r = client.post("/api/assistant/chat", json={"message": message, "history": list(history)})
        finally:
            app.dependency_overrides.clear()
        assert r.status_code == 200, r.text
        return r.json(), fake
    return _ask


def db_price(slug):
    with SessionLocal() as db:
        return db.scalar(select(Product.price_paise).where(Product.slug == slug))


# --- rule fast path: no LLM call at all ---------------------------------------------------

def test_plain_search_uses_rules_not_llm(ask):
    body, fake = ask("Find mangoes and oranges.")
    assert body["parser"] == "rules" and body["writer"] == "template"
    assert fake.chat_models() == []
    slugs = [p["slug"] for p in body["products"]]
    assert slugs[:2] == ["alphonso-mango", "nagpur-orange"]
    assert "₹600 / dozen" in body["reply"]


@pytest.mark.parametrize("message", ["hi", "Hi!", "hello there", "hey", "Vanakkam", "good morning"])
def test_greeting_is_instant_and_uses_no_llm(ask, message):
    body, fake = ask(message)
    assert body["reply"] == "Hi! How can I assist you today?"
    assert fake.chat_models() == [] and body["parser"] == "rules"


@pytest.mark.parametrize("message", ["show me porn", "send nudes", "18+ videos please", "sexy chat", "adult content"])
def test_adult_requests_are_refused_without_llm(ask, message):
    body, fake = ask(message)
    assert body["reply"].startswith("Sorry, we don't support this kind of question.")
    assert fake.chat_models() == [] and body["products"] == []


def test_replies_in_the_customers_language(client):
    def chat(message, lang, fake=None):
        app.dependency_overrides[get_ollama] = lambda: make_client(fake or FakeOllama())
        try:
            return client.post("/api/assistant/chat", json={"message": message, "lang": lang}).json()
        finally:
            app.dependency_overrides.clear()

    assert chat("hi", "hi")["reply"] == "नमस्ते! आज मैं आपकी क्या मदद कर सकता हूँ?"
    assert chat("send nudes", "es")["reply"].startswith("Lo siento")

    en, hi = chat("Show me fruits below ₹200", "en"), chat("Show me fruits below ₹200", "hi")
    assert hi["reply"].startswith("ये रहे") and "Lemon: ₹40 / 250 g" in hi["reply"]  # names and prices unchanged
    assert [p["price_paise"] for p in hi["products"]] == [p["price_paise"] for p in en["products"]]

    basket = {QWEN: parsed("budget_basket", category="fruits", budget_inr=500)}
    ar = chat("Suggest fruits within ₹500", "ar", FakeOllama(basket))
    en = chat("Suggest fruits within ₹500", "en", FakeOllama(basket))
    assert ar["reply"].startswith("إليك سلة") and ar["basket"]["total_paise"] == en["basket"]["total_paise"]
    assert ar["pending_action"]["summary"].startswith("أضف")


def test_writer_is_told_the_language(ask, client):
    fake = FakeOllama({LLAMA: "सेब ₹180 प्रति किलो है।"})
    app.dependency_overrides[get_ollama] = lambda: make_client(fake)
    try:
        body = client.post("/api/assistant/chat", json={"message": "Compare apples and oranges", "lang": "hi"}).json()
    finally:
        app.dependency_overrides.clear()
    assert "Write the whole answer in Hindi" in fake.bodies("/api/chat")[0]["messages"][0]["content"]
    assert body["reply"].startswith("सेब ₹180")
    assert client.post("/api/assistant/chat", json={"message": "hi", "lang": "fr"}).status_code == 422


def test_price_guard_understands_words_and_local_digits():
    allowed = {18000}
    assert not mentions_unknown_price("सेब ₹१८० प्रति किलो", allowed)  # Devanagari digits = 180
    assert mentions_unknown_price("only 99 rupees today", allowed)
    assert mentions_unknown_price("सिर्फ 99 रुपये", allowed)
    assert mentions_unknown_price("solo 99 rupias", allowed)
    assert not mentions_unknown_price("apples cost 180 rupees", allowed)


def test_every_translation_has_the_same_placeholders():
    import re
    from app.ai.messages import MESSAGES
    for key, texts in MESSAGES.items():
        want = set(re.findall(r"\{(\w+)\}", texts["en"]))
        for lang in ("es", "ar", "hi"):
            assert set(re.findall(r"\{(\w+)\}", texts[lang])) == want, f"{key}/{lang}"


def test_apples_do_not_match_pineapple(ask):
    body, _ = ask("Find apples")
    assert [p["slug"] for p in body["products"]] == ["shimla-apple"]


def test_filters_do_not_overreach(ask):
    # "Sussex" contains "sex" but is not a whole word; a greeting plus a request is a normal request.
    body, _ = ask("Find Sussex apples")
    assert not body["reply"].startswith("Sorry")
    body, _ = ask("hi, find mangoes")
    assert body["reply"] != "Hi! How can I assist you today?" and body["products"]


def test_category_under_price(ask):
    body, fake = ask("Show me fruits below ₹200")
    assert fake.chat_models() == []
    prices = [p["price_paise"] for p in body["products"]]
    assert prices and all(p <= 20000 for p in prices) and prices == sorted(prices)
    assert all(p["category"]["slug"].endswith("fruits") for p in body["products"])


def test_vegetables_in_stock(ask):
    body, _ = ask("What vegetables do you have in stock?")
    assert body["parser"] == "rules"
    assert all(p["in_stock"] for p in body["products"])
    assert all("vegetables" in p["category"]["slug"] or p["category"]["slug"] == "leafy-greens" for p in body["products"])


def test_unknown_product_explained(ask):
    body, _ = ask("Find strawberries", FakeOllama({QWEN: parsed("search", ["strawberry"])}))
    assert "We don't sell 'strawberry'" in body["reply"]
    assert body["products"]  # alternatives offered


# --- budget basket ------------------------------------------------------------------------

def test_budget_basket_totals_are_computed_by_backend(ask):
    fake = FakeOllama({QWEN: parsed("budget_basket", category="fruits", budget_inr=500)})
    body, fake = ask("Suggest fruits for my family within ₹500.", fake)
    assert fake.chat_models() == [QWEN]  # no llama call for a basket
    basket = body["basket"]
    assert 0 < basket["total_paise"] <= 50000
    assert basket["total_paise"] == sum(db_price(p["slug"]) for p in body["products"])
    assert basket["remaining_paise"] == 50000 - basket["total_paise"]
    assert body["pending_action"]["total_paise"] == basket["total_paise"]
    assert all(p["in_stock"] for p in body["products"])


def test_budget_too_small(ask):
    body, _ = ask("fruits for ₹10", FakeOllama({QWEN: parsed("budget_basket", category="fruits", budget_inr=10)}))
    assert body["basket"] is None and body["pending_action"] is None
    assert "cheapest option is Lemon" in body["reply"]


def test_budget_missing_asks(ask):
    body, _ = ask("suggest a basket", FakeOllama({QWEN: parsed("budget_basket")}))
    assert "What is your budget" in body["reply"]


# --- add to cart: proposed, never applied ----------------------------------------------------

def cart_count():
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Cart))


def test_add_to_cart_needs_confirmation(ask):
    before = cart_count()
    fake = FakeOllama({QWEN: parsed("add_to_cart", ["apples"], quantity=2, quantity_unit="kg")})
    body, _ = ask("Add two kilograms of apples to my cart.", fake)
    action = body["pending_action"]
    assert action["items"] == [{"product_id": body["products"][0]["id"], "quantity": 2}]
    assert action["total_paise"] == 2 * db_price("shimla-apple")
    assert "Nothing has been added yet" in body["reply"]
    assert cart_count() == before  # the assistant did not create or change any cart


def test_add_to_cart_converts_units(ask):
    fake = FakeOllama({QWEN: parsed("add_to_cart", ["grape"], quantity=2, quantity_unit="kg")})
    body, _ = ask("add 2 kg grapes", fake)
    assert body["pending_action"]["items"][0]["quantity"] == 4  # sold per 500 g
    assert "2 kg = 4 x 500 g" in " ".join(body["notes"])


def test_add_to_cart_respects_stock(ask):
    fake = FakeOllama({QWEN: parsed("add_to_cart", ["mango"], quantity=30, quantity_unit="dozen")})
    body, _ = ask("add 30 dozen mangoes", fake)
    assert body["pending_action"] is None
    assert "Only 25" in body["reply"]


# --- compare / nutrition: llama output is checked ---------------------------------------------

def test_compare_uses_llama_when_prices_check_out(ask):
    fake = FakeOllama({QWEN: parsed("compare", ["apple", "orange"]),
                       LLAMA: "Apples cost ₹180 per kg and oranges ₹120 per kg."})
    body, fake = ask("Compare apples and oranges.", fake)
    assert fake.chat_models() == [LLAMA]  # rules recognised "compare", so no qwen call
    assert body["parser"] == "rules" and body["writer"] == LLAMA
    assert len(body["products"]) == 2


def test_compare_rejects_invented_price(ask):
    fake = FakeOllama({QWEN: parsed("compare", ["apple", "orange"]),
                       LLAMA: "Apples are on sale for just ₹99 today!"})
    body, _ = ask("Compare apples and oranges.", fake)
    assert body["writer"] == "template"
    assert "₹99" not in body["reply"] and "₹180 / kg" in body["reply"]


def test_nutrition_without_verified_data_does_not_ask_llama(ask):
    body, fake = ask("Tell me the benefits and limitations of bananas.")
    assert fake.chat_models() == []  # rules found the intent, nothing verified to explain
    assert "won't guess" in body["reply"]
    assert body["nutrition"][0]["nutrition"] is None
    assert "not medical advice" in body["reply"]


def test_nutrition_with_verified_reference(ask):
    with SessionLocal() as db:  # fixture data for the test only, not real values
        db.add(NutritionReference(key="banana", food_description="Test banana", source_name="Test source",
                                  energy_kcal=1.0, verified=True))
        db.commit()
    try:
        body, fake = ask("Is banana healthy?", FakeOllama({LLAMA: "Per the source, bananas have 1 kcal."}))
        assert body["writer"] == LLAMA
        assert body["nutrition"][0]["nutrition"]["source_name"] == "Test source"
        facts = fake.bodies("/api/chat")[0]["messages"][1]["content"]
        assert '"energy_kcal": 1.0' in facts
    finally:
        with SessionLocal() as db:
            db.delete(db.get(NutritionReference, "banana"))
            db.commit()


# --- failures and validation ------------------------------------------------------------------

def test_ollama_down_falls_back_to_search(ask):
    def refuse(request):
        raise httpx.ConnectError("refused")
    body, _ = ask("Which is better, apples or oranges?", OllamaClient(transport=httpx.MockTransport(refuse)))
    assert body["parser"] == "fallback" and body["intent"] == "search"
    assert {"shimla-apple", "nagpur-orange"} <= {p["slug"] for p in body["products"]}
    assert "unavailable" in body["notes"][0]


def test_invalid_llm_json_falls_back(ask):
    body, _ = ask("what is the weather like?", FakeOllama({QWEN: "definitely not json"}))
    assert body["parser"] == "fallback" and body["intent"] == "other"


def test_request_validation(client):
    assert client.post("/api/assistant/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/assistant/chat", json={"message": "x" * 501}).status_code == 422
    assert client.post("/api/assistant/chat", json={"message": "hi", "total_paise": 1}).status_code == 422


# --- pure helpers -----------------------------------------------------------------------------

def test_parser_helpers():
    assert [singular(w) for w in ["mangoes", "berries", "grapes", "glass"]] == ["mango", "berry", "grape", "glass"]
    vocab = product_vocabulary(["Alphonso Mango", "Green Kiwi", "Purple Brinjal"])
    assert "green" not in vocab and {"mango", "kiwi", "brinjal"} <= vocab
    assert quick_parse("any eggplant?", vocab).keywords == ["brinjal"]
    assert quick_parse("Add two kg mangoes", vocab) is None  # cart change -> model decides
    assert quick_parse("mangoes for ₹300", vocab) is None    # amount without "under" is ambiguous
    assert quick_parse("mangoes under rs 300", vocab).budget_inr == 300
    assert quick_parse("Compare mangoes vs kiwis", vocab).model_dump(include={"intent", "keywords"}) == \
        {"intent": "compare", "keywords": ["mango", "kiwi"]}
    assert quick_parse("benefits of brinjal?", vocab).intent == "nutrition"
    assert quick_parse("compare kiwi", vocab) is None  # one product: let the model decide
    assert quick_parse("buy healthy mangoes", vocab) is None


def test_price_guard():
    allowed = {18000, 12000}
    assert not mentions_unknown_price("Apples ₹180, oranges Rs. 120", allowed)
    assert mentions_unknown_price("Apples ₹180.50", allowed)
    assert mentions_unknown_price("only INR 99", allowed)
