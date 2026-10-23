# Setup on Windows

## Backend

```powershell
cd C:\Users\Admin\Desktop\kad_ai\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.seed                       # optional: server also seeds on startup
python -m uvicorn app.main:app --reload --port 8000
```

- API docs (Swagger): http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

If `Activate.ps1` is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
(or skip the venv and use the system Python).

## Frontend

Start the backend first (it serves all product data), then in a second terminal:

```powershell
cd C:\Users\Admin\Desktop\kad_ai\frontend
npm install
npm run dev
```

Open http://localhost:3000. Checks: `npm run lint`, `npx tsc --noEmit`, `npm run build`.

| Symptom | Cause / fix |
|---|---|
| Sections show "The Kad AI API is not reachable" | Backend not running on port 8000. |
| `Port 3000 is in use` | Another dev server is running; stop it or use `npm run dev -- -p 3001`. |
| Type errors about `PageProps<"/...">` | Route types not generated yet: run `npx next typegen` (dev/build do it automatically). |
| Cart empty after switching browser | The cart id lives in that browser's localStorage. |
| Chat says "took too long" | First AI call loads the model (can be 60-90 s on 8 GB RAM); try again, close heavy apps. |
| Chat says "Couldn't reach the assistant" | Backend not running, or Ollama stopped (`ollama list` to check). |
| Checkout says "Not enough stock" | Stock changed after the item was added; lower the quantity in the cart. |

## Tests

```powershell
cd C:\Users\Admin\Desktop\kad_ai\backend
python -m pytest -q

cd C:\Users\Admin\Desktop\kad_ai\frontend
npm test

# end-to-end, with both servers running
cd C:\Users\Admin\Desktop\kad_ai
$env:PYTHONIOENCODING="utf-8"; python scripts\smoke_test.py          # add --ai and/or --order for more
```

## Checking Ollama

```powershell
ollama list                                  # should show qwen3:4b and llama3.2
cd C:\Users\Admin\Desktop\kad_ai\backend
$env:PYTHONIOENCODING="utf-8"; python -m app.ai.check   # loads each model in turn, ~2 min
Invoke-RestMethod http://127.0.0.1:8000/api/assistant/status   # with the API running
```

| Symptom | Cause / fix |
|---|---|
| "Ollama is not running" | Start the Ollama app or `ollama serve`. |
| "Model ... is not installed" | Run `ollama pull <model>` yourself, or change `OLLAMA_*_MODEL` in `.env`. |
| "took too long" | First call loads the model from disk. Close heavy apps, raise `OLLAMA_READ_TIMEOUT`. |
| PC freezes / swapping | Lower `OLLAMA_NUM_CTX` (e.g. 2048) or set `OLLAMA_KEEP_ALIVE=0`. |
| `UnicodeEncodeError` printing ₹ | Set `$env:PYTHONIOENCODING="utf-8"` in the terminal. |

## Talking to the assistant

PowerShell 5.1 needs the body sent as UTF-8 bytes for the ₹ sign:

```powershell
$body = [Text.Encoding]::UTF8.GetBytes('{"message": "Suggest fruits for my family within ₹500"}')
$r = Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/assistant/chat -ContentType "application/json; charset=utf-8" -Body $body
$r.reply; $r.basket.total_paise; $r.pending_action
```

Or use Swagger at http://127.0.0.1:8000/docs → `POST /api/assistant/chat` → Try it out.
`parser` / `writer` in the response show which path ran (rules, qwen3:4b, llama3.2, template).

## Database migrations (Alembic)

Startup runs `alembic upgrade head` automatically, so existing data is kept. After changing a model:

```powershell
cd C:\Users\Admin\Desktop\kad_ai\backend
python -m alembic revision --autogenerate -m "describe the change"
```

Read the generated file in `backend\migrations\versions\`, then restart the backend. The test
`test_migrations.py` fails if a model changes without a migration. To start over with fresh demo data,
stop the server and delete `backend\kadai.db`.

## Example requests (PowerShell)

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products?category=fruits&max_price=100&sort=price_asc"
Invoke-RestMethod "http://127.0.0.1:8000/api/products/search?q=mango"
Invoke-RestMethod "http://127.0.0.1:8000/api/products/shimla-apple"

$cart = Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/cart/items `
  -ContentType application/json -Body '{"product_id": 1, "quantity": 2}'
Invoke-RestMethod http://127.0.0.1:8000/api/cart -Headers @{ "X-Cart-Id" = $cart.cart_id }
```

## Common errors

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run commands from the `backend` folder. |
| `[Errno 10048]` address in use | Port 8000 busy: stop the other server or use `--port 8001`. |
| 422 Unprocessable Entity | Bad input (e.g. `quantity: 0`, `min_price > max_price`, extra `price` field). Read `detail`. |
| 409 Conflict on cart | Quantity exceeds stock; message says how many are available. |
| New column missing / `no such column` | Delete `kadai.db` (see above). |
