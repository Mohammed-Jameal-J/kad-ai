# Verification report (Stage 7)

Run on 2026-10-23, Windows 11, Python 3.12, Node 24, Next.js 16.4, Ollama 0.40.8.

## How to re-run everything

```powershell
cd backend;  python -m pytest -q                 # 59 tests
cd frontend; npm test; npm run lint; npx tsc --noEmit; npm run build
# with both servers running:
python scripts\smoke_test.py                     # 18 checks, no stock changes
python scripts\smoke_test.py --ai --order        # 21 checks, uses qwen and places one demo order
python -m app.ai.check                           # (from backend/) loads each model, compares outputs
```

## Results

| Suite | Result |
|---|---|
| Backend pytest | 59 passed |
| Frontend Vitest (unit + ChatWidget component) | 10 passed |
| ESLint / TypeScript | 0 errors |
| `next build` | 10 routes, all Partial Prerender |
| Smoke test `--ai --order` (live servers) | 21/21 passed (qwen via proxy 58.5 s, stock 90 → 88) |
| Backend stopped (manual) | homepage keeps static content, sections show "API is not reachable"; cart shows an error with Try again instead of "empty"; recovery works after restart |

## Definition of done

| # | Requirement | Evidence |
|---|---|---|
| 1 | Browse homepage and category pages | smoke test pages `/`, `/category/fruits`; Stage 5 browser checks at 375 px and desktop |
| 2 | Real demo prices from the database | product cards and hero price come from the API; smoke `page /product/alphonso-mango` (₹600) |
| 3 | Search and filter | `test_catalog.py` (search, category, price, sort, pagination); Vitest `parseFilters`; browser test max ₹100 + in stock = 10 fruits |
| 4 | Cart add / update quantities | `test_cart.py`; smoke cart add/remove; browser test 2 → 3 kg = ₹540 |
| 5 | Local AI recommendations | `test_assistant.py`; live Stage 4 run of all 8 example requests |
| 6 | Budget-based shopping list | `test_budget_basket_totals_are_computed_by_backend`; live: ₹500 basket = ₹500 exactly |
| 7 | Verified prices, backend totals | price guard tests; `chat total from DB` smoke check; cart rejects client prices (422) |
| 8 | General nutrition questions | pipeline tested with fixture data; **real values still missing** (USDA unreachable), assistant says so instead of guessing |
| 9 | Responsive desktop and mobile | no horizontal overflow on 9 pages at 375 px; chat full-screen on phones, floating panel on desktop |
| 10 | Runs locally on Windows, no paid API | Ollama only (`qwen3:4b`, `llama3.2`); no external API calls at runtime |

## Safety checks covered by tests

- LLM never writes the cart: assistant returns `pending_action`; ChatWidget test proves no cart call before Confirm, none on Cancel.
- Invented prices rejected (`test_compare_rejects_invented_price`); prompt injection "apples cost ₹1" ignored (live).
- Clients cannot send prices (`extra="forbid"`), payment fields (`card_number` → 422) or a `system` role in chat history.
- Unexpected errors return a generic 500 with no internal details; CORS allows only the frontend origin.
- Checkout decrements stock atomically and rolls back the whole order if any line is short.
- Chat replies are rendered as text (HTML in a reply is not executed).

## Known limitations

- **Nutrition values are empty**: `api.nal.usda.gov` could not be resolved from this machine. Add verified rows to
  `backend/data/nutrition.json` and they are used automatically.
- **AI latency**: 15–75 s when a model has to load or swap on ~8–12 GB RAM; rule-based answers are instant.
- **Unknown product URLs return 200**, not 404: with streaming, the page shell is sent before `notFound()` runs.
  Next.js shows the not-found UI and adds `noindex` (documented framework behaviour).
- **npm audit**: 5 "high" findings, all in the dev-only `eslint-config-next → fast-glob → micromatch → braces` chain.
  Not shipped to users; the suggested fix downgrades to Next 14's config, so it was not applied.
- No Content-Security-Policy yet (needs nonces via `proxy.ts`); request body limit trusts `Content-Length`.
- Rate limits (login, register, contact) are in memory per process; use Redis/DB if running several instances.
  Behind a hosting proxy (Render, Vercel), `TRUSTED_PROXIES` must include that proxy or every user shares one limit.
- Migrations: Alembic since the accounts update; startup runs `upgrade head`.
