# Security

## Reporting a problem

Please do not open a public issue for a security bug. Use GitHub's **Report a vulnerability**
button (Security tab of this repository) so it stays private until fixed.

## What protects a running Kad AI

Publishing the code does not give anyone access to your copy: the database, `.env` and the Ollama
models stay on the machine that runs them. Protection against a visitor flooding the AI or the API:

| Risk | Protection |
|---|---|
| Flooding the AI chat | 10 chats per IP per minute (`CHAT_PER_MINUTE`); at most 3 requests wait for the model, the rest get `503 busy` at once (`OLLAMA_MAX_WAITING`), so the server never runs out of threads |
| Faking a new IP per request | `X-Forwarded-For` is ignored; only `TRUSTED_IP_HEADER` (set it to the header your deploy edge overwrites) is used. Run uvicorn with `--no-proxy-headers` |
| Slow multi-agent endpoint | `/api/assistant/crew` is off unless `CREW_ENABLED=true` |
| Draining paid/free API quotas | Groq: `GROQ_DAILY_LIMIT` calls/day for everyone (over it: rules only; keep Groq on the free plan). Serper: `SEARCH_DAILY_LIMIT`/day and `SEARCH_PER_IP_PER_HOUR`, and only food questions are searched |
| Untrusted web content | Search results are data, never instructions; web answers may not contain any ₹ amount, show their https sources, and are labelled as not checked |
| Prompt injection | Models have no tools, no DB access, no SQL. Prices, totals and stock come only from the database; replies with unknown ₹ amounts are rejected; cart changes need the user's Confirm |
| Buying out stock with fake orders | 5 orders per IP per hour; carts 60 writes per IP per minute |
| Password guessing | 5 failed logins per email+IP and 20 per IP per 15 minutes; scrypt hashes; registrations 10/IP/hour |
| Session theft / CSRF | HttpOnly, SameSite=Lax cookie (set `COOKIE_SECURE=true` on HTTPS); only the token's SHA-256 is stored |
| Large or junk requests | 64 KB body limit, strict Pydantic schemas (`extra="forbid"`), 500 errors never show internals |
| XSS, clickjacking | Content-Security-Policy, `X-Frame-Options: DENY`, replies rendered as text, never HTML |
| Vulnerable dependencies | Dependabot weekly PRs (`.github/dependabot.yml`) |

## Before deploying publicly

- `COOKIE_SECURE=true`, `TRUSTED_IP_HEADER` set for your edge, backend reachable only through it.
- Rate limits live in process memory: use one backend instance, or move them to Redis.
- Put a real reverse-proxy body limit in front (the app trusts `Content-Length`).
