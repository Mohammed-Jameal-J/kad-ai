"""Groq (hosted LLM) and Serper (web search): request shape, guards, daily caps, chat integration."""
import json

import httpx
import pytest

from app.ai import groq, websearch
from app.ai.groq import GroqClient
from app.ai.ollama import OllamaError, get_ollama
from app.core.config import settings
from app.main import app
from app.schemas.assistant import ParsedRequest


def completion(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}], "usage": {}})


@pytest.fixture
def groq_on(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "gsk_test")
    monkeypatch.setattr(settings, "ai_enabled", True)


def groq_client(handler, calls=None):
    def record(request: httpx.Request):
        if calls is not None:
            calls.append((request, json.loads(request.content)))
        return handler(json.loads(request.content))
    return GroqClient(transport=httpx.MockTransport(record))


def test_groq_json_request_shape_and_validation(groq_on):
    calls = []
    client = groq_client(lambda body: completion('{"intent": "search", "keywords": ["mango"]}'), calls)
    parsed = client.chat_json(client.intent_model, [{"role": "user", "content": "mangoes?"}], ParsedRequest)
    assert parsed.intent == "search" and parsed.keywords == ["mango"]
    request, body = calls[0]
    assert request.url.path == "/openai/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer gsk_test"
    assert body["model"] == settings.groq_intent_model
    assert body["response_format"]["type"] == "json_schema"
    assert body["reasoning_effort"] == "low"  # gpt-oss intent model


def test_groq_errors_become_fallback_errors(groq_on, monkeypatch):
    busy = groq_client(lambda body: httpx.Response(429, json={"error": "rate"}))
    with pytest.raises(OllamaError, match="busy"):
        busy.chat("llama-3.3-70b-versatile", [{"role": "user", "content": "hi"}])
    bad_json = groq_client(lambda body: completion("not json"))
    with pytest.raises(OllamaError, match="unexpected format"):
        bad_json.chat_json(bad_json.intent_model, [{"role": "user", "content": "x"}], ParsedRequest)

    monkeypatch.setattr(settings, "groq_api_key", "")
    never = groq_client(lambda body: pytest.fail("no key: must not call Groq"))
    with pytest.raises(OllamaError, match="not set up"):
        never.chat("m", [{"role": "user", "content": "hi"}])


def test_groq_daily_cap(groq_on, monkeypatch):
    monkeypatch.setattr(groq.DAILY, "limit", 2)
    client = groq_client(lambda body: completion("ok"))
    assert [client.chat("m", [{"role": "user", "content": "hi"}]) for _ in range(2)] == ["ok", "ok"]
    with pytest.raises(OllamaError, match="today's limit"):
        client.chat("m", [{"role": "user", "content": "hi"}])
    assert client.status()["requests_left_today"] == 0


def test_chat_through_groq_uses_both_models(client, groq_on):
    def reply(body):
        if body["model"] == settings.groq_intent_model:
            return completion('{"intent": "compare", "keywords": ["papaya", "pineapple"]}')
        return completion("Papaya is soft and mild; pineapple is tangy and juicy.")
    app.dependency_overrides[get_ollama] = lambda: groq_client(reply)
    try:
        body = client.post("/api/assistant/chat", json={"message": "Papaya or pineapple, which one is sweeter?"}).json()
    finally:
        app.dependency_overrides.clear()
    assert body["parser"] == settings.groq_intent_model
    assert body["writer"] == settings.groq_response_model
    assert {p["slug"] for p in body["products"]} >= {"red-lady-papaya", "queen-pineapple"}


def serper(organic):
    return httpx.MockTransport(lambda request: httpx.Response(200, json={"organic": organic}))


def test_search_keeps_https_results_only_and_has_caps(monkeypatch):
    monkeypatch.setattr(settings, "serper_api_key", "serper_test")
    results = websearch.search("mango juice", "1.2.3.4", transport=serper([
        {"title": "Safe", "link": "https://example.com/a", "snippet": "Blend ripe mango."},
        {"title": "Bad", "link": "javascript:alert(1)", "snippet": "x"},
        {"title": "Plain", "link": "http://example.com/b", "snippet": "x"},
    ]))
    assert [r["url"] for r in results] == ["https://example.com/a"]

    monkeypatch.setattr(websearch.PER_IP, "limit", 1)  # that visitor used their search already
    with pytest.raises(websearch.SearchUnavailable):
        websearch.search("again", "1.2.3.4", transport=serper([]))

    monkeypatch.setattr(settings, "serper_api_key", "")
    with pytest.raises(websearch.SearchUnavailable):
        websearch.search("x", "5.6.7.8", transport=serper([]))


@pytest.fixture
def web(monkeypatch):
    monkeypatch.setattr(settings, "serper_api_key", "serper_test")
    searched = []

    def fake_search(query, client):
        searched.append(query)
        return [{"title": "Mango juice guide", "url": "https://example.com/juice", "snippet": "Blend ripe mango with water."}]
    monkeypatch.setattr(websearch, "search", fake_search)
    return searched


def test_food_question_answered_from_web_with_sources(client, web):
    from fakes import FakeOllama, make_client
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama({
        "qwen3:4b": {"intent": "other", "keywords": ["mango"]},
        "llama3.2": "Blend ripe mango with a little water and chill it [1].",
    }))
    try:
        body = client.post("/api/assistant/chat", json={"message": "How do I make mango juice at home?"}).json()
    finally:
        app.dependency_overrides.clear()
    assert web and body["sources"] == [{"title": "Mango juice guide", "url": "https://example.com/juice"}]
    assert "[1]" in body["reply"] and "not checked" in body["notes"][-1]


def test_web_answer_with_a_price_is_rejected(client, web):
    from fakes import FakeOllama, make_client
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama({
        "qwen3:4b": {"intent": "other", "keywords": ["mango"]},
        "llama3.2": "Mangoes cost ₹40 at most shops [1].",  # invented price from the web
    }))
    try:
        body = client.post("/api/assistant/chat", json={"message": "How do I make mango juice at home?"}).json()
    finally:
        app.dependency_overrides.clear()
    assert "₹40" not in body["reply"] and body["writer"] == "template"  # snippets shown instead
    assert "Blend ripe mango" in body["reply"]


def test_non_food_question_never_searches(client, web):
    from fakes import FakeOllama, make_client
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama({"qwen3:4b": {"intent": "other"}}))
    try:
        body = client.post("/api/assistant/chat", json={"message": "Who won the cricket match yesterday?"}).json()
    finally:
        app.dependency_overrides.clear()
    assert web == [] and body["sources"] == []
