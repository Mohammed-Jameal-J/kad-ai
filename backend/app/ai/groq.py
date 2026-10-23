"""Hosted LLMs through Groq's OpenAI-compatible API (https://console.groq.com/docs), for deployments
that can't run Ollama. Same interface as OllamaClient (chat, chat_json, status), so the parser,
writer and their guards (Pydantic validation, keyword filter, price guard) work unchanged.

Abuse/cost guard: a global daily request cap (GROQ_DAILY_LIMIT). Over the cap, or on any Groq error
(including Groq's own free-tier 429), calls raise OllamaError and the assistant falls back to rules.
"""
import json
import logging
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.ollama import OllamaError
from app.core.config import settings
from app.core.ratelimit import RateLimiter

logger = logging.getLogger("kadai.groq")
T = TypeVar("T", bound=BaseModel)

DAILY = RateLimiter(limit=settings.groq_daily_limit, window_seconds=24 * 3600)


class GroqClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):  # tests pass httpx.MockTransport
        self.intent_model = settings.groq_intent_model
        self.response_model = settings.groq_response_model
        self._http = httpx.Client(
            base_url="https://api.groq.com/openai/v1",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            timeout=httpx.Timeout(30, connect=5),
            transport=transport,
        )

    def _post(self, body: dict) -> dict:
        if not settings.ai_enabled:
            raise OllamaError("The AI assistant is switched off on this server; using quick rules and search.")
        if not settings.groq_api_key:
            raise OllamaError("The AI assistant is not set up on this server; using quick rules and search.")
        if DAILY.retry_after("all"):
            raise OllamaError("The AI assistant reached today's limit; using quick rules and search.")
        DAILY.record("all")
        try:
            r = self._http.post("/chat/completions", json=body)
        except httpx.HTTPError:
            raise OllamaError("The AI service is not reachable right now.")
        if r.status_code == 429:
            raise OllamaError("The AI service is busy right now.")
        if r.is_error:
            logger.warning("groq model=%s status=%s", body["model"], r.status_code)  # body may echo the prompt: not logged
            raise OllamaError(f"The AI service returned an error ({r.status_code}).")
        return r.json()

    def chat(self, model: str, messages: list[dict], *, schema: dict | None = None,
             temperature: float = 0.2, max_tokens: int = 512) -> str:
        body = {"model": model, "messages": messages, "temperature": temperature, "max_completion_tokens": max_tokens}
        if schema is not None:
            # Best-effort schema (strict mode needs every field required); Pydantic is the real gate.
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "answer", "strict": False, "schema": schema}}
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"  # reasoning model: keep it quick for extraction
        started = time.perf_counter()
        data = self._post(body)
        usage = data.get("usage", {})
        logger.info("groq model=%s total=%.1fs prompt_tokens=%s output_tokens=%s", model,
                    time.perf_counter() - started, usage.get("prompt_tokens"), usage.get("completion_tokens"))
        return (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""

    def chat_json(self, model: str, messages: list[dict], output: type[T], **kwargs) -> T:
        text = self.chat(model, messages, schema=output.model_json_schema(), **kwargs)
        try:
            return output.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("groq model=%s returned output that failed validation: %s", model, type(e).__name__)
            raise OllamaError(f"Model '{model}' returned output in an unexpected format")

    def status(self) -> dict:
        roles = {"intent": self.intent_model, "response": self.response_model}
        ok = settings.ai_enabled and bool(settings.groq_api_key)
        return {
            "provider": "groq", "reachable": ok,
            **({} if ok else {"error": "GROQ_API_KEY is not set or AI is switched off."}),
            "models": {role: {"name": name, "available": ok} for role, name in roles.items()},
            "requests_left_today": None if not ok else DAILY.limit - DAILY.used("all"),
        }
