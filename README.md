# Kad AI

Fruit and vegetable store with an AI shopping assistant. Next.js + FastAPI + SQLAlchemy, with local
models (Ollama) on your machine and hosted models (Groq) on the live site.

**Live demo:** https://kad-ai.vercel.app · All prices are **demonstration prices**, not live market prices.

## Features

- Storefront: categories, search and filters, product pages, cart, demo checkout, accounts, 4 languages (English, Spanish, Arabic with RTL, Hindi)
- AI assistant: finds products, builds a basket within a budget, compares items, proposes cart changes (applied only after Confirm)
- Grounded answers: prices, stock and totals come only from the database; replies with invented prices, nutrient figures or disease claims are rejected
- Web search (Serper) for food questions the store data can't answer, with sources shown
- Instant rule-based answers for common requests; typo-tolerant
- Security: per-visitor rate limits, daily caps on AI and search, CSP, HttpOnly session cookies, scrypt passwords
- Emails with Resend: welcome and newsletter
- Tested: pytest, Vitest, DeepEval quality checks

| Where | Intent model | Answer model |
|---|---|---|
| Local (`LLM_PROVIDER=ollama`) | `qwen3:4b` | `llama3.2` |
| Live (`LLM_PROVIDER=groq`) | `openai/gpt-oss-20b` | `openai/gpt-oss-120b` |

An optional CrewAI multi-agent workflow runs locally only ([docs/crewai.md](docs/crewai.md)).

## Quick start (two terminals)

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000 --no-proxy-headers
```

```powershell
cd frontend
npm install
npm run dev
```

Website: http://localhost:3000. Local AI needs [Ollama](https://ollama.com) with `qwen3:4b` and `llama3.2`.

## Docs

- [Setup](docs/setup.md) · [Architecture](docs/architecture.md) · [Deploy (Vercel + Render)](docs/deploy.md)
- [Verification and test results](docs/verification.md) · [Security](SECURITY.md)

## Author

Mohammed Jameal J · [GitHub](https://github.com/Mohammed-Jameal-J) · [LinkedIn](https://www.linkedin.com/in/mohammed-jameal-j/) · mohammedjameal031@gmail.com

## License

[MIT](LICENSE)
