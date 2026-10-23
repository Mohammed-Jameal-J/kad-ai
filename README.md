# Kad AI

Fruit and vegetable store with a local-LLM shopping assistant (Ollama, no paid APIs).
Learning project: Next.js + FastAPI + SQLAlchemy + Ollama, CrewAI later.

All prices are **demonstration prices**, not live market prices.

## Status

| Stage | What | State |
|---|---|---|
| 1-2 | Database, seed catalog, product/category/cart APIs, tests | done |
| 3 | Ollama service (`qwen3:4b` intent, `llama3.2` responses) | done |
| 4 | AI shopping assistant with verified products and backend totals | done (API) |
| 5 | Next.js storefront (Bootstrap 5): home, listing, category, product, cart | done |
| 6 | Floating AI chat widget + checkout demo (orders, stock decrement) | done |
| 7 | Tests (pytest, Vitest, smoke test), error handling, full verification | done, see [docs/verification.md](docs/verification.md) |
| 8 | Optional CrewAI workflow (separate venv) + measured comparison | done, see [docs/crewai.md](docs/crewai.md) |

## Quick start (two terminals)

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Website: http://localhost:3000 · API docs: http://127.0.0.1:8000/docs. Details in [docs/setup.md](docs/setup.md),
design in [docs/architecture.md](docs/architecture.md).

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | |
| GET | `/api/categories` | tree with product counts |
| GET | `/api/products` | `q, category, min_price, max_price` (rupees), `in_stock, featured, bestseller, on_sale, sort, page, page_size` |
| GET | `/api/products/search` | same, `q` required |
| GET | `/api/products/{id or slug}` | includes verified nutrition when available |
| GET | `/api/cart` | header `X-Cart-Id` |
| POST | `/api/cart/items` | `{product_id, quantity}`; creates cart if no header; 201 |
| PATCH | `/api/cart/items/{item_id}` | `{quantity}` (absolute) |
| DELETE | `/api/cart/items/{item_id}` | |
| GET | `/api/assistant/status` | Ollama reachable? models installed? (never loads a model) |
| POST | `/api/auth/register` · `/api/auth/login` · `/api/auth/logout` | accounts; scrypt-hashed passwords, HttpOnly session cookie (7 days) |
| GET | `/api/auth/me` · `/api/orders/mine` | current user and their orders (401 when logged out) |
| POST | `/api/contact` | contact form, stored in the database |
| POST | `/api/assistant/crew` | optional CrewAI workflow; 501 unless run from `backend/.venv-crewai` ([docs](docs/crewai.md)) |
| POST | `/api/orders` | demo checkout for the `X-Cart-Id` cart: `{customer_name, phone, address, delivery_slot}`; 201; no payment fields |
| POST | `/api/assistant/chat` | `{message, history}` → reply, DB products, basket, `pending_action` (cart changes need confirmation) |

Money fields end in `_paise` (integer). ₹180 = `18000`.
