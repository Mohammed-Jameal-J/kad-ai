"""OllamaClient tests against a fake Ollama (httpx.MockTransport). No real model is loaded."""
from typing import Literal

import httpx
import pytest
from pydantic import BaseModel

from app.ai.ollama import OllamaClient, OllamaError, get_ollama
from app.main import app
from fakes import FakeOllama, make_client


def test_chat_sends_options_and_returns_text():
    fake = FakeOllama("Namaste")
    assert make_client(fake).chat("llama3.2", [{"role": "user", "content": "hi"}]) == "Namaste"
    body = fake.bodies("/api/chat")[0]
    assert body["stream"] is False
    assert body["options"]["num_ctx"] == 4096
    assert body["keep_alive"] == "30m"


def test_think_flag_only_for_thinking_models():
    fake = FakeOllama()
    client = make_client(fake)
    client.chat("qwen3:4b", [])
    client.chat("llama3.2", [])
    qwen_body, llama_body = fake.bodies("/api/chat")
    assert qwen_body["think"] is False
    assert "think" not in llama_body


def test_switching_models_unloads_previous():
    fake = FakeOllama()
    client = make_client(fake)
    client.chat("qwen3:4b", [])
    client.chat("qwen3:4b", [])
    assert fake.bodies("/api/generate") == []  # same model, nothing to unload
    client.chat("llama3.2", [])
    assert fake.bodies("/api/generate") == [{"model": "qwen3:4b", "keep_alive": 0}]


def test_missing_model_is_an_error_and_never_pulled():
    fake = FakeOllama(installed={"llama3.2:latest": ["completion"]})
    with pytest.raises(OllamaError, match="not installed"):
        make_client(fake).chat("qwen3:4b", [])
    assert all(path != "/api/pull" for path, _ in fake.calls)
    assert fake.bodies("/api/chat") == []


def test_unreachable_ollama():
    def refuse(request):
        raise httpx.ConnectError("refused")
    client = OllamaClient(transport=httpx.MockTransport(refuse))
    with pytest.raises(OllamaError, match="not running") as e:
        client.chat("llama3.2", [])
    assert e.value.status_code == 503
    assert client.status()["reachable"] is False


class Intent(BaseModel):
    intent: Literal["search", "other"]
    max_budget_inr: int | None


def test_chat_json_validates_and_sends_schema():
    fake = FakeOllama('{"intent": "search", "max_budget_inr": 200}')
    result = make_client(fake).chat_json("qwen3:4b", [], Intent)
    assert result == Intent(intent="search", max_budget_inr=200)
    assert fake.bodies("/api/chat")[0]["format"]["properties"]["intent"]["enum"] == ["search", "other"]


@pytest.mark.parametrize("reply", ["not json", '{"intent": "buy_everything", "max_budget_inr": 1}'])
def test_chat_json_rejects_bad_output(reply):
    with pytest.raises(OllamaError, match="unexpected format"):
        make_client(FakeOllama(reply)).chat_json("qwen3:4b", [], Intent)


def test_status_endpoint(client):
    app.dependency_overrides[get_ollama] = lambda: make_client(FakeOllama())
    try:
        body = client.get("/api/assistant/status").json()
    finally:
        app.dependency_overrides.clear()
    assert body["reachable"] is True
    assert body["models"]["intent"] == {"name": "qwen3:4b", "available": True,
                                        "capabilities": ["completion", "tools", "thinking"]}
    assert body["models"]["response"]["available"] is True  # "llama3.2" matched "llama3.2:latest"
