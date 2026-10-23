"""Time the assistant on messages that used to need the local models.

    python scripts/bench_chat.py            (backend on http://127.0.0.1:8000, Ollama running)

Sends one request every 7 s at most, to stay under the default 10 chats/minute limit.
"""
import json
import sys
import time
import urllib.request

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
MESSAGES = [
    "Add two kilograms of apples to my cart",
    "Suggest fruits within ₹500",
    "Put 3 dozen bananas in my cart",
    "Plan a week of vegetables for my family under 300 rupees",
    "add 1 kg onion and 2 kg tomato",
    "Which is better value, carrots or beetroot?",
    "do you deliver on sunday?",
    "I want something sweet for my kids",
    "Which mangoes are good for my kids?",
]

for message in MESSAGES:
    started = time.perf_counter()
    req = urllib.request.Request(f"{API}/api/assistant/chat", json.dumps({"message": message}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        body = json.load(urllib.request.urlopen(req, timeout=300))
        path = body["parser"] + (f" -> {body['writer']}" if body["writer"] != "template" else "")
        result = f"{body['intent']:<14} {path}"
    except Exception as e:  # noqa: BLE001 - a benchmark reports, it does not crash
        result = f"ERROR {e}"
    took = time.perf_counter() - started
    print(f"{took:6.1f}s  {result:<40} {message}", flush=True)
    time.sleep(max(0, 7 - took))
