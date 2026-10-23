"""End-to-end smoke test against the RUNNING app (backend :8000 + frontend :3000).

Everything goes through the Next.js frontend, so this also checks server rendering, the /api proxy
and security headers. Safe by default: the cart test adds and then removes an item.

    python scripts/smoke_test.py            # pages, proxy, cart, fast chat (no LLM)
    python scripts/smoke_test.py --ai       # + one chat request that uses qwen (can take ~1 min)
    python scripts/smoke_test.py --order    # + place a real demo order (reduces stock by 1 cucumber)
"""
import argparse
import sys

import httpx

FRONTEND = "http://localhost:3000"
BACKEND = "http://127.0.0.1:8000"
failures = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global failures
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}{f'  ({detail})' if detail else ''}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai", action="store_true", help="also run a chat request through the intent model")
    parser.add_argument("--order", action="store_true", help="also place a demo order (changes stock)")
    args = parser.parse_args()

    try:
        health = httpx.get(f"{BACKEND}/api/health", timeout=5).json()
        check("backend health", health.get("status") == "ok")
    except httpx.HTTPError as e:
        check("backend reachable on :8000", False, str(e))
        return 1

    web = httpx.Client(base_url=FRONTEND, timeout=60)
    try:
        web.get("/")
    except httpx.HTTPError as e:
        check("frontend reachable on :3000", False, str(e))
        return 1

    # Server-rendered pages contain real database content once streaming finishes.
    pages = {
        "/": "New products",
        "/products": "All products",
        "/products?q=mango": "Alphonso Mango",
        "/category/fruits": "Everyday Fruits",
        "/product/alphonso-mango": "₹600",
        "/cart": "Your cart",
        "/checkout": "Checkout",
        "/contact": "Coimbatore",
        "/blog": "From our kitchen",
        "/login": "Welcome back",
        "/register": "Create your account",
    }
    for path, expected in pages.items():
        r = web.get(path)
        check(f"page {path}", r.status_code == 200 and expected in r.text, f"status {r.status_code}")
    # With streaming (Partial Prerendering) the shell is already sent with 200 when notFound() runs,
    # so Next.js keeps 200 and adds a noindex tag instead (documented framework behaviour).
    missing = web.get("/product/not-a-real-product").text
    check("unknown product shows not-found + noindex", "find that page" in missing and 'content="noindex"' in missing)

    headers = web.get("/").headers
    check("security headers", headers.get("x-content-type-options") == "nosniff" and headers.get("x-frame-options") == "DENY")

    # Browser-style calls through the Next.js /api proxy.
    check("api proxy", web.get("/api/health").json().get("status") == "ok")
    cucumber = web.get("/api/products/cucumber").json()
    cart = web.post("/api/cart/items", json={"product_id": cucumber["id"], "quantity": 2}).json()
    cart_headers = {"X-Cart-Id": cart["cart_id"]}
    check("cart add: server total", cart["subtotal_paise"] == 2 * cucumber["price_paise"], f"{cart['subtotal_paise']} paise")
    check("cart rejects client price", web.post("/api/cart/items", json={"product_id": cucumber["id"], "price_paise": 1}).status_code == 422)

    if args.order:
        before = cucumber["stock_quantity"]
        order = web.post("/api/orders", headers=cart_headers, json={
            "customer_name": "Smoke Test", "phone": "+91 90000 00000", "address": "1 Test Street, Chennai", "delivery_slot": "08-12",
        })
        after = web.get("/api/products/cucumber").json()["stock_quantity"]
        check("demo order placed", order.status_code == 201, f"status {order.status_code}")
        check("stock reduced by order", after == before - 2, f"{before} -> {after}")
        check("cart emptied after order", web.get("/api/cart", headers=cart_headers).json()["items"] == [])
    else:
        item_id = cart["items"][0]["id"]
        emptied = web.delete(f"/api/cart/items/{item_id}", headers=cart_headers).json()
        check("cart remove", emptied["items"] == [] and emptied["subtotal_paise"] == 0)

    chat = web.post("/api/assistant/chat", json={"message": "Show me fruits below ₹200"}, timeout=60).json()
    prices_ok = all(p["price_paise"] <= 20000 for p in chat.get("products", []))
    check("chat (rules path)", chat.get("parser") == "rules" and chat["products"] and prices_ok, f"{chat.get('duration_ms')} ms")

    if args.ai:
        print("...asking the intent model (can take a minute on first load)")
        r = web.post("/api/assistant/chat", json={"message": "Add two kilograms of apples to my cart"}, timeout=240)
        body = r.json()
        action = body.get("pending_action") or {}
        apple = web.get("/api/products/shimla-apple").json()
        check("chat (qwen) via proxy", r.status_code == 200 and body.get("parser") == "qwen3:4b", f"{body.get('duration_ms')} ms")
        check("chat proposes, does not add", action.get("items") == [{"product_id": apple["id"], "quantity": 2}])
        check("chat total from DB", action.get("total_paise") == 2 * apple["price_paise"])

    print(f"\n{'ALL PASSED' if not failures else f'{failures} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
