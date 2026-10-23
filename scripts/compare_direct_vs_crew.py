"""Run the same prompts through the direct assistant and the CrewAI workflow and compare.

Needs a backend started from backend/.venv-crewai (CrewAI installed), e.g. on port 8001:
    backend\\.venv-crewai\\Scripts\\python -m uvicorn app.main:app --port 8001 --app-dir backend
    python scripts/compare_direct_vs_crew.py --url http://127.0.0.1:8001
"""
import argparse
import threading
import time

import httpx

PROMPTS = [
    "Suggest healthy fruits for my family within ₹500",  # budget + goal: the case a crew is meant for
    "Show me fruits below ₹200",                          # simple lookup: a crew is overkill
]
OLLAMA = "http://localhost:11434"


def peak_model_memory(stop: threading.Event, out: dict) -> None:
    """Sample Ollama's loaded models once a second; record peak total size and model names."""
    while not stop.is_set():
        try:
            models = httpx.get(f"{OLLAMA}/api/ps", timeout=2).json().get("models", [])
            total = sum(m.get("size", 0) for m in models)
            if total > out["bytes"]:
                out.update(bytes=total, models=sorted(m["name"] for m in models))
        except httpx.HTTPError:
            pass
        stop.wait(1)


def run(url: str, path: str, message: str) -> dict:
    stop, peak = threading.Event(), {"bytes": 0, "models": []}
    sampler = threading.Thread(target=peak_model_memory, args=(stop, peak), daemon=True)
    sampler.start()
    started = time.perf_counter()
    try:
        r = httpx.post(f"{url}{path}", json={"message": message}, timeout=900)
        status, body = r.status_code, r.json()
    except httpx.HTTPError as e:
        status, body = f"error ({type(e).__name__})", {}
    finally:
        stop.set()
        sampler.join()
    basket = body.get("basket") or {}
    return {
        "status": status,
        "seconds": time.perf_counter() - started,
        "peak_mb": peak["bytes"] / 1024**2,
        "models": ", ".join(peak["models"]) or "-",
        "parser": body.get("parser"),
        "products": len(body.get("products", [])),
        "total": basket.get("total_paise"),
        "budget": basket.get("budget_paise"),
        "notes": body.get("notes", []),
        "reply": (body.get("reply") or body.get("detail") or "")[:500],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    for message in PROMPTS:
        for label, path in (("direct", "/api/assistant/chat"), ("crewai", "/api/assistant/crew")):
            httpx.post(f"{OLLAMA}/api/generate", json={"model": "qwen3:4b", "keep_alive": 0})   # start cold-ish
            httpx.post(f"{OLLAMA}/api/generate", json={"model": "llama3.2", "keep_alive": 0})
            r = run(args.url, path, message)
            within = r["total"] is not None and (r["budget"] is None or r["total"] <= r["budget"])
            print(f"\n=== {label:6} | {message}")
            print(f"status={r['status']} time={r['seconds']:.1f}s peak_model_ram={r['peak_mb']:.0f}MB models=[{r['models']}] "
                  f"parser={r['parser']} products={r['products']} total_paise={r['total']} within_budget={within}")
            for n in r["notes"]:
                print(f"  note: {n}")
            print("  reply: " + r["reply"].replace("\n", "\n         "))


if __name__ == "__main__":
    main()
