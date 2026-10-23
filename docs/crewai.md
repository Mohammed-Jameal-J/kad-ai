# Optional CrewAI workflow (Stage 8)

A separate, opt-in multi-agent version of the basket assistant, built to compare against the direct
FastAPI + Ollama assistant. The website's chat widget keeps using the direct assistant.

## Run it

CrewAI pins its own versions of pydantic, FastAPI and SQLAlchemy, so it lives in its own virtual environment.
The normal backend (global Python) does not need it; its `/api/assistant/crew` endpoint answers 501 with
instructions.

```powershell
cd C:\Users\Admin\Desktop\kad_ai\backend
python -m venv .venv-crewai
.\.venv-crewai\Scripts\python -m pip install -r requirements-crewai.txt
$env:CREW_ENABLED = "true"   # the endpoint is off by default (slow, easy to abuse)
.\.venv-crewai\Scripts\python -m uvicorn app.main:app --port 8001 --no-proxy-headers
```

```powershell
$body = [Text.Encoding]::UTF8.GetBytes('{"message": "Suggest healthy fruits for my family within ₹500"}')
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/assistant/crew -ContentType "application/json; charset=utf-8" -Body $body -TimeoutSec 1200
```

Compare both approaches: `python scripts\compare_direct_vs_crew.py --url http://127.0.0.1:8001`.

## Design

```
POST /api/assistant/crew {message, budget_inr?}
  OllamaClient.exclusive("llama3.2")   lock + unload other models: one model in RAM, no parallel chat calls
  Crew (sequential, memory off, telemetry/tracing off, share_crew off)
    1 Product discovery agent   tool: search_products   (read-only catalog search)
    2 Nutrition agent           tool: get_nutrition     (verified rows only; says "not available")
    3 Basket planner agent      tool: quote_basket      (DB prices + stock; authoritative total)
  resolve_items()      product names/ids from the planner -> DB ids (unknown names dropped)
  validate_basket()    plain Python: drop invented/out-of-stock ids, clamp to stock, enforce budget
  price guard          explanation/notes with rupee amounts not in the DB are removed
  -> ChatResponse with pending_action (customer must confirm; nothing is added to the cart)
```

- `app/crew/tools.py` and `app/crew/validation.py` have no CrewAI import and are unit-tested in both
  environments. Tools only read; a test asserts stock, carts and orders are unchanged after calling them.
- `app/crew/workflow.py` is the only file that imports CrewAI. Telemetry flags
  (`OTEL_SDK_DISABLED`, `CREWAI_DISABLE_TELEMETRY`, `CREWAI_DISABLE_TRACKING`, `CREWAI_TRACING_ENABLED=false`)
  are set before the import, verified against CrewAI 1.15.28 source.
- Every crew failure (bad model output, timeouts) becomes a 502 with a friendly message, never a raw 500.
- `crew_recommended()` marks when a crew is worth it: a budget **and** a goal (healthy, family, plan, nutrition).
  For anything else the response notes that the direct assistant is faster. `/api/assistant/chat` never
  calls the crew.

## Why one model (llama3.2) for every agent

CrewAI 1.15 talks to Ollama through its OpenAI-compatible `/v1` API, not the native `/api/chat` our service uses.
Through `/v1` we cannot pass `keep_alive`/`num_ctx`, unload between agents, or turn off qwen3's thinking.
Probe results on this machine (one agent, one tool):

| Model via CrewAI | Result |
|---|---|
| llama3.2 | called the tool, valid structured output, 47.9 s |
| qwen3:4b | no answer after 500 s (thinking cannot be disabled over `/v1`); stopped |

## Measured comparison (Windows laptop, CPU only, ~3 GB free RAM, Ollama 0.40.8)

| | Direct assistant (`/chat`) | CrewAI (`/crew`) |
|---|---|---|
| "Suggest healthy fruits for my family within ₹500" | 57–61 s, valid basket ₹500/₹500 (4 of 4 runs) | 0 of 6 runs produced an answer (log below) |
| "Show me fruits below ₹200" | 3 s (rules, no LLM), 8 products | 484 s, basket ₹140 (agents: discovery 327 s, nutrition 65 s, planning 88 s) |
| Peak model RAM | 3.0 GB (qwen3:4b only) | 2.4 GB (llama3.2 only) |
| LLM calls per request | 0–2 | 6–10+ (tool calls, retries, output conversion) |
| Prompt size per call | ~400 tokens | ~2,000 tokens (CrewAI system prompts + tool schemas) |
| Deterministic parts | parsing fallback, DB queries, totals, budget | same backend checks, re-applied after the crew |
| Code | `services/assistant.py` + `ai/` | + `crew/` (3 files), separate venv (~1 GB of packages) |

Family-basket crew runs, in order (each fix below was applied before the next run):

| Run | Time | Outcome |
|---|---|---|
| 1 | 372 s | crash: model put whole rows into `product_ids: list[int]` |
| 2 | 600 s+ | one request generated until the client's 600 s timeout |
| 3 | 308 s | crew finished, then our code failed (session closed before serializing products; fixed + tested) |
| 4 | 414 s | 502: three requests hit the 90 s timeout |
| 5 | 184 s | 502: discovery agent passed the 150 s agent limit |
| 6 | 900 s+ | no answer; two 150 s request timeouts, prompts grew to ~3,100 tokens |

### Reliability problems found (and what was done)

1. **Strict structured output crashed the run**: llama3.2 copied whole tool rows into `product_ids: list[int]`.
   Fix: only the final task is structured; its schema is lenient; names are resolved through the database.
2. **Runaway generation**: one request generated for 10 minutes until the OpenAI client's default 600 s timeout.
   Fix: `max_tokens=500`, `timeout=150`, `max_retries=0`.
3. **Too-tight timeouts**: with 90 s per request and 150 s per agent, cold calls with ~2,000-token prompts failed.
   Fix: 150 s per request, 300 s per agent.
4. **Agents disagreed**: nutrition notes covered products the planner dropped. Fix: keep only notes that mention
   products in the validated basket.
5. **Semantics drift**: "fruits below ₹200" (a per-item limit) was treated as a ₹200 total budget by the planner.
   The direct assistant's rules parser handles this correctly.

### Known limitations

- The model lock (`OllamaClient.exclusive`) works within one backend process. Running the crew backend on
  :8001 next to the main backend on :8000 means two processes can load models at the same time; on 8 GB RAM,
  stop the main backend while experimenting with the crew.
- A crew request can hold its process's model lock for 10+ minutes, blocking direct chat calls in that process.
- The crew endpoint is API-only; the website does not call it (the frontend proxy timeout is 200 s anyway).

## Direct workflow vs CrewAI: conclusions

- **Latency**: the direct assistant answers simple lookups in milliseconds and LLM requests in about a minute.
  The crew takes 3–8 minutes on this hardware, mostly from processing CrewAI's large prompts on CPU.
- **Memory**: similar peak (one model at a time in both), because the crew is pinned to llama3.2 and runs under
  the same model lock. The crew venv adds about 1 GB on disk and a heavier Python process.
- **Complexity**: the crew adds a dependency tree, a second environment, prompt/role design and output
  conversion. All safety still comes from the same deterministic backend code.
- **Reliability**: the direct path is predictable (one validated JSON call, then plain Python). The crew's
  success depends on a 3B model following multi-step tool protocols; it failed more often than it succeeded here.
- **When a crew would make sense**: a GPU or a larger model, tasks that really need several independent research
  steps, and latency of minutes being acceptable. For this shop on an 8 GB CPU laptop, the direct assistant is
  the right default, and that is what the website uses.
