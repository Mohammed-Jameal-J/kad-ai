# Kad AI architecture

```
kad_ai/
  backend/                FastAPI + SQLAlchemy + SQLite
    app/
      main.py             app, CORS, body-size limit, error handlers, lifespan (create tables + seed)
      core/config.py      settings from env / .env
      core/errors.py      ServiceError -> JSON {detail} with the right status code
      db/session.py       engine, Base, get_db() dependency
      db/seed.py          idempotent seeding from data/catalog.json
      models/             Category, Product, NutritionReference, Cart, CartItem
      schemas/            Pydantic request/response models
      services/           business logic (catalog queries, cart rules); no HTTP code
      api/                thin routers: parse request -> call service -> return schema
    data/catalog.json     demo catalog (demonstration prices)
    tests/                pytest, uses a throwaway SQLite file
  frontend/               Next.js storefront (Stage 5)
  docs/references/        design reference screenshots
```

## Request flow

```
Browser -> /api/products?category=fruits&max_price=100
  api/catalog.py   validates query params with ProductQuery (422 on bad input)
  services/catalog list_products() builds a SQLAlchemy query (no raw SQL, LIKE input escaped)
  SQLite           returns rows
  ProductPage      serialises; prices stay integer paise
```

## Rules that the AI layer (Stage 3+) must keep

- The database is the only source of product IDs, prices, stock and discounts.
- Money is integer paise. Totals are computed only in `services/cart.py`.
- Cart items store no price; the price is read from the product row every time.
- Clients cannot send prices: `extra="forbid"` rejects unknown fields with 422.
- The AI will call `services/*` functions with validated filters (`ProductQuery`), never generate SQL.
- Nutrition values come only from `nutrition_references` rows with `verified = true`.

## Local LLMs (app/ai/ollama.py)

`OllamaClient` talks to `http://localhost:11434` over HTTP (no SDK):

- `status()` uses `/api/version`, `/api/tags`, `/api/ps`; never loads a model.
- `chat()` uses `/api/chat` with `stream: false`, `keep_alive`, `num_ctx`, `num_predict`.
- `chat_json()` passes a Pydantic model's JSON schema as `format`, then validates the reply
  with Pydantic. Invalid output -> `OllamaError` (503), never silently used.
- Calls are serialized with a lock; switching models unloads the previous one
  (`/api/generate` with `keep_alive: 0`), so only one model is in RAM at a time.
- Missing models raise an error. Nothing is ever pulled automatically.
- Logs contain model, timings and token counts, not prompt text.

Measured on this machine (Ollama 0.40.8, 11.8 GB RAM, `python -m app.ai.check`):

| | qwen3:4b | llama3.2 (3B) |
|---|---|---|
| RAM when loaded (num_ctx 4096) | ~3.0 GB | ~2.4 GB |
| First call incl. load | ~24 s | ~15 s |
| JSON extraction per message | ~10-13 s | ~8-14 s |
| Valid schema output (5 prompts) | 5/5 | 5/5 |
| Keyword quality | precise, singular, no invented items | adds products the user never named |
| Free-text answers | leaks reasoning even with `think: false` | clean |
| `think` flag | supported | `think: true` rejected |

Conclusion: qwen3:4b for intent extraction (JSON only), llama3.2 for customer-facing text.

## Shopping assistant (POST /api/assistant/chat)

```
message
  -> ai/parser.quick_parse()    rules: plain search, "compare X and Y", "benefits of X"   (0 s, no LLM)
  -> ai/parser.llm_parse()      otherwise qwen3:4b + JSON schema                         (~10-15 s)
       Ollama down / bad JSON -> loose rules search ("fallback")
  -> ParsedRequest (Pydantic)   intent, keywords, category, budget_inr, quantity, unit
  -> services/assistant.py      handler per intent, SQLAlchemy via services/catalog + services/cart
       search        DB list, explains misses (not sold / over budget / out of stock)
       budget_basket greedy 1-unit basket <= budget, totals via cart.quote() in paise
       add_to_cart   unit conversion (2 kg -> 4 x 500 g), stock check, pending_action only
       compare       llama3.2 writes from FACTS; reply rejected if it mentions an unknown ₹ amount
       nutrition     llama only when verified nutrition rows exist; otherwise says so
       other         help text
  -> ChatResponse               reply + products (DB) + basket + pending_action + parser/writer used
```

- The models have no tools and no DB/cart access. They produce JSON (qwen) or prose (llama), both checked.
- `pending_action` is never applied by the server. The chat widget shows a Confirm button that calls
  `POST /api/cart/items`, which re-checks stock and prices.
- The server stores no chat history; the client sends the last turns in `history`.
- Nutrition values come only from `backend/data/nutrition.json` rows marked `verified: true`
  (currently empty: the USDA site was unreachable when building; see that file's `_note`).

Measured live (CPU, one model in RAM at a time):

| Request | Path | Time |
|---|---|---|
| "Find mangoes and oranges", "fruits below ₹200", "vegetables in stock" | rules | < 0.1 s |
| "Compare apples and oranges" | rules + llama | ~23 s |
| "Add two kilograms of apples", "benefits of bananas" (qwen path) | qwen | ~14 s |
| "Suggest fruits within ₹500" after a llama call | swap + qwen | ~49 s |
| "Which is better value, carrots or beetroot?" | qwen + swap + llama | ~75 s |

Model swaps dominate. With more free RAM, `OLLAMA_MAX_LOADED_MODELS=2` and removing the unload
in `OllamaClient.chat` would cut the slow rows roughly in half.

## Storefront (frontend/)

Next.js 16 with Cache Components: every page renders a static shell immediately, and anything that reads
the API or the URL (`searchParams`, `params`) sits inside `<Suspense>` with a skeleton fallback.

```
Browser ──► Next.js server ──fetch──► FastAPI :8000      (Server Components: lib/api.ts)
Browser ──► /api/cart/* ──rewrite──► FastAPI :8000      (Client cart calls: services/cartApi.ts)
```

- Product data is never hardcoded: cards, prices, the hero price and the deal of the week come from the API.
- Filters, sort and search are GET forms (`next/form`): shareable URLs, client-side navigation, work without JS.
- Cart state: `hooks/useCart.tsx` (React context); the cart id is stored in localStorage, totals come from the server.
- Errors: `settle()` turns a failed fetch into a friendly `StatusNote`; `app/error.tsx` catches render errors.
- Images: local files in `public/images`, all public domain or CC0 from Wikimedia Commons (no attribution
  required; sources recorded in `docs/photo-sources.json`). Brand logos in `public/brand`. `ProductImage` falls back to
  `placeholder.svg` when a file is missing (e.g. the inactive jamun).

## Chat widget (frontend/components/chat)

- Mounted once in the root layout, so it survives page navigation. The header "Ask Kad AI" button opens it
  via a `kadai:open-chat` window event.
- Conversation lives in `sessionStorage`; the last 10 turns go to the backend as `history` (server stores none).
- Replies are rendered as React text (escaped, `white-space: pre-line`), never as HTML.
- Product cards, basket totals and prices are the backend's verified data. A `pending_action` shows
  Confirm / Cancel; Confirm calls the normal cart API per item (`useCart.addMany`), which re-checks stock.
- Every reply shows which path ran (`rules`, `qwen3:4b`, `→ llama3.2`) and how long it took.
- `next.config.ts` sets `experimental.proxyTimeout: 200_000`: the `/api/*` rewrite proxy otherwise cuts requests
  at 30 s, and local model replies can take over a minute.

## Demo checkout (POST /api/orders)

```
cart (X-Cart-Id) -> services/orders.place_order()
  for each line: UPDATE products SET stock = stock - qty WHERE id = ? AND active AND stock >= qty
                 (rowcount != 1 -> rollback everything, 409 "Not enough stock for X")
  copy name/unit/price into order_items (later price changes never alter a past order)
  delete the cart, commit once
```

No payment fields exist (extra fields such as `card_number` are rejected with 422). Customer details are stored
only in the local SQLite file.

## Cart identity

No login yet. `POST /api/cart/items` without `X-Cart-Id` creates a cart and returns `cart_id`
(a UUID). The frontend stores it and sends it back in the `X-Cart-Id` header.
