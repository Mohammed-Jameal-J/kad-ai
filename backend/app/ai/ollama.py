"""Thin client for the local Ollama HTTP API (http://localhost:11434).

Design choices for an 8-12 GB RAM laptop:
- Calls are serialized with a lock, so only one generation runs at a time.
- When a call needs a different model than the previous call, the previous model is
  unloaded first, so qwen3:4b and llama3.2 are never both resident in RAM.
- Models are never pulled/downloaded here. A missing model is reported as an error.
- Prompts and replies are not logged; only model name, timings and token counts.
"""
import json
import logging
import threading
import time
from contextlib import contextmanager
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.errors import ServiceError

logger = logging.getLogger("kadai.ollama")
T = TypeVar("T", bound=BaseModel)


class OllamaError(ServiceError):
    status_code = 503


BUSY = "The assistant is busy with other customers. Please try again in a moment."


def _full_name(model: str) -> str:
    """Ollama lists "llama3.2" as "llama3.2:latest"."""
    return model if ":" in model else f"{model}:latest"


class OllamaClient:
    def __init__(
        self,
        base_url: str = settings.ollama_base_url,
        keep_alive: str = settings.ollama_keep_alive,
        num_ctx: int = settings.ollama_num_ctx,
        connect_timeout: float = settings.ollama_connect_timeout,
        read_timeout: float = settings.ollama_read_timeout,
        max_waiting: int = settings.ollama_max_waiting,
        queue_wait: float = settings.ollama_queue_wait,
        transport: httpx.BaseTransport | None = None,  # tests pass httpx.MockTransport
    ):
        self.keep_alive = keep_alive
        self.num_ctx = num_ctx
        self._http = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
            transport=transport,
        )
        # ponytail: one global lock, fine for one local machine. Use a job queue if several users share it.
        self._lock = threading.Lock()
        self._last_model: str | None = None
        self.max_waiting = max_waiting
        self.queue_wait = queue_wait
        self._waiting = 0
        self._waiting_lock = threading.Lock()

    @contextmanager
    def _slot(self):
        """The model lock, but bounded: a flood of requests gets 503 "busy" instead of tying up
        every server thread for minutes."""
        with self._waiting_lock:
            if self._waiting >= self.max_waiting:
                raise OllamaError(BUSY, headers={"Retry-After": "30"})
            self._waiting += 1
        try:
            acquired = self._lock.acquire(timeout=self.queue_wait)
        finally:
            with self._waiting_lock:
                self._waiting -= 1
        if not acquired:
            raise OllamaError(BUSY, headers={"Retry-After": "30"})
        try:
            yield
        finally:
            self._lock.release()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            r = self._http.request(method, path, **kwargs)
        except httpx.ConnectError:
            raise OllamaError("Ollama is not running. Start it with `ollama serve` or the Ollama app.")
        except httpx.TimeoutException:
            raise OllamaError("Ollama took too long to respond. Try again, or use a smaller model.")
        if r.is_error:
            raise OllamaError(f"Ollama error {r.status_code}: {r.text[:200]}")
        return r.json()

    def list_models(self) -> dict[str, list[str]]:
        """Installed models -> capabilities, e.g. {"qwen3:4b": ["completion", "tools", "thinking"]}."""
        tags = self._request("GET", "/api/tags")
        return {m["name"]: m.get("capabilities", []) for m in tags.get("models", [])}

    def loaded_models(self) -> list[dict]:
        """Models currently in RAM, with their memory size in bytes."""
        return [
            {"name": m["name"], "size_bytes": m.get("size"), "expires_at": m.get("expires_at")}
            for m in self._request("GET", "/api/ps").get("models", [])
        ]

    def status(self) -> dict:
        """Reachability and model availability. Never loads a model."""
        roles = {"intent": settings.ollama_intent_model, "response": settings.ollama_response_model}
        try:
            version = self._request("GET", "/api/version").get("version")
            installed = self.list_models()
        except OllamaError as e:
            return {"reachable": False, "error": e.detail, "models": {
                role: {"name": name, "available": False} for role, name in roles.items()
            }}
        return {
            "reachable": True,
            "version": version,
            "models": {
                role: {
                    "name": name,
                    "available": _full_name(name) in installed,
                    "capabilities": installed.get(_full_name(name), []),
                }
                for role, name in roles.items()
            },
            "loaded": self.loaded_models(),
        }

    def _capabilities(self, model: str) -> list[str]:
        installed = self.list_models()
        if _full_name(model) not in installed:
            raise OllamaError(
                f"Model '{model}' is not installed. Install it yourself with `ollama pull {model}`, "
                "or set a different model in .env. Kad AI never downloads models automatically."
            )
        return installed[_full_name(model)]

    def unload(self, model: str) -> None:
        self._request("POST", "/api/generate", json={"model": model, "keep_alive": 0})

    @contextmanager
    def exclusive(self, model: str):
        """Hold the model lock for an outside caller (the CrewAI workflow) and make sure `model`
        is installed and is the only model in RAM while it runs."""
        with self._slot():
            self._capabilities(model)
            for loaded in self.loaded_models():
                if loaded["name"] != _full_name(model):
                    self.unload(loaded["name"])
            self._last_model = model
            yield

    def chat(
        self,
        model: str,
        messages: list[dict],
        *,
        schema: dict | None = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        """Run one non-streaming chat completion and return the assistant text.

        `schema` (a JSON schema) makes Ollama constrain the output to valid JSON of that shape.
        """
        with self._slot():
            caps = self._capabilities(model)
            if self._last_model and self._last_model != model:
                self.unload(self._last_model)

            body = {
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {"temperature": temperature, "num_ctx": self.num_ctx, "num_predict": max_tokens},
            }
            if "thinking" in caps:
                # qwen3 "thinks" before answering by default: slow and wastes tokens for extraction.
                # Measured on qwen3:4b / Ollama 0.40.8: think=False stops the separate thinking
                # field, but free-text replies still contain reasoning prose. With a JSON `format`
                # the output is clean, so use the intent model only for structured (schema) calls.
                body["think"] = False
            if schema is not None:
                body["format"] = schema

            started = time.perf_counter()
            data = self._request("POST", "/api/chat", json=body)
            self._last_model = model

        logger.info(
            "ollama model=%s total=%.1fs load=%.1fs prompt_tokens=%s output_tokens=%s",
            model, time.perf_counter() - started, data.get("load_duration", 0) / 1e9,
            data.get("prompt_eval_count"), data.get("eval_count"),
        )
        return data.get("message", {}).get("content", "")

    def chat_json(self, model: str, messages: list[dict], output: type[T], **kwargs) -> T:
        """Chat with JSON-schema-constrained output, validated into a Pydantic model.

        Even with `format`, a small model can return values that break our rules (wrong enum,
        negative budget...), so Pydantic validation is the real gate.
        """
        text = self.chat(model, messages, schema=output.model_json_schema(), **kwargs)
        try:
            return output.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("ollama model=%s returned output that failed validation: %s", model, type(e).__name__)
            raise OllamaError(f"Model '{model}' returned output in an unexpected format")


_client: OllamaClient | None = None


def get_ollama() -> OllamaClient:
    """FastAPI dependency; tests override it with a client using a mock transport."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
