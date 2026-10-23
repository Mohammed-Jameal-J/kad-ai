import json

import httpx

from app.ai.ollama import OllamaClient

INSTALLED = {
    "qwen3:4b": ["completion", "tools", "thinking"],
    "llama3.2:latest": ["completion", "tools"],
}


class FakeOllama:
    """Stands in for the Ollama HTTP API. `reply` is one string, or {model_name: reply}."""

    def __init__(self, reply: str | dict = "Hello", installed=INSTALLED, loaded: list[str] = ()):
        self.reply = reply
        self.installed = installed
        self.loaded = list(loaded)  # models reported by /api/ps as currently in RAM
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        self.calls.append((request.url.path, body))
        match request.url.path:
            case "/api/version":
                return httpx.Response(200, json={"version": "0.40.8"})
            case "/api/tags":
                return httpx.Response(200, json={"models": [
                    {"name": n, "capabilities": c} for n, c in self.installed.items()
                ]})
            case "/api/ps":
                return httpx.Response(200, json={"models": [{"name": n, "size": 1} for n in self.loaded]})
            case "/api/generate":  # only used for unloading
                return httpx.Response(200, json={"done": True, "done_reason": "unload"})
            case "/api/chat":
                reply = self.reply[body["model"]] if isinstance(self.reply, dict) else self.reply
                if isinstance(reply, dict):
                    reply = json.dumps(reply)
                return httpx.Response(200, json={"message": {"role": "assistant", "content": reply}})
        return httpx.Response(404, text="not found")

    def bodies(self, path: str) -> list[dict]:
        return [b for p, b in self.calls if p == path]

    def chat_models(self) -> list[str]:
        return [b["model"] for b in self.bodies("/api/chat")]


def make_client(fake) -> OllamaClient:
    return OllamaClient(transport=httpx.MockTransport(fake))
