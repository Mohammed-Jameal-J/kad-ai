"""Live check of the local Ollama models. Loads each model in turn (one at a time).

Run from backend/:  python -m app.ai.check
"""
import time
from typing import Literal

from pydantic import BaseModel, Field

from app.ai.ollama import OllamaClient, OllamaError
from app.core.config import settings


class TrialIntent(BaseModel):
    """Trial extraction schema to compare the models. Stage 4 defines the real one."""
    intent: Literal["search", "nutrition", "compare", "budget_basket", "add_to_cart", "other"]
    keywords: list[str] = Field(max_length=10)
    category: Literal["fruits", "vegetables"] | None
    max_budget_inr: int | None = Field(ge=0)
    quantity: int | None = Field(ge=1)


SYSTEM = (
    "You extract shopping filters from a customer message for a fruit and vegetable store. "
    "Return only JSON. keywords are product names in singular English (e.g. 'apple'). "
    "max_budget_inr is a rupee amount if the customer states one, else null. "
    "quantity is a number of units if stated, else null."
)
MESSAGES = [
    "Show me fruits below ₹200.",
    "Find mangoes and oranges.",
    "Add two kilograms of apples to my cart.",
    "Compare apples and oranges.",
    "Suggest fruits for my family within ₹500.",
]


def mb(n: int | None) -> str:
    return f"{(n or 0) / 1024**2:,.0f} MB"


def check_model(client: OllamaClient, model: str) -> None:
    print(f"\n=== {model} ===")
    started = time.perf_counter()
    reply = client.chat(model, [{"role": "user", "content": "In one short sentence, what is a guava?"}], max_tokens=60)
    print(f"plain reply ({time.perf_counter() - started:.1f}s, includes load): {reply.strip()}")
    print("loaded now:", [(m["name"], mb(m["size_bytes"])) for m in client.loaded_models()])

    ok = 0
    for msg in MESSAGES:
        started = time.perf_counter()
        try:
            result = client.chat_json(model, [
                {"role": "system", "content": SYSTEM}, {"role": "user", "content": msg},
            ], TrialIntent, temperature=0)
            ok += 1
            print(f"  {time.perf_counter() - started:4.1f}s  {msg!r:46} -> {result.model_dump()}")
        except OllamaError as e:
            print(f"  {time.perf_counter() - started:4.1f}s  {msg!r:46} -> ERROR {e.detail}")
    print(f"valid structured outputs: {ok}/{len(MESSAGES)}")


def main() -> None:
    client = OllamaClient()
    status = client.status()
    print("Ollama:", "reachable, version " + str(status.get("version")) if status["reachable"] else status["error"])
    for role, info in status["models"].items():
        print(f"  {role:8} {info['name']:12} available={info['available']} capabilities={info.get('capabilities')}")
    if not status["reachable"]:
        return
    for model in dict.fromkeys([settings.ollama_intent_model, settings.ollama_response_model]):
        try:
            check_model(client, model)
        except OllamaError as e:
            print(f"{model}: {e.detail}")
    client.unload(settings.ollama_response_model)
    print("\nUnloaded. Loaded now:", client.loaded_models())


if __name__ == "__main__":
    main()
