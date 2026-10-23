# Deploy a free demo: Vercel (storefront) + Render (API)

```
Visitor ──► Vercel: Next.js storefront ──/api/* rewrite──► Render: FastAPI + SQLite
                    (pages fetch the API server-side with API_URL)
```

The browser only ever talks to Vercel, so there is no CORS setup and the login cookie stays on
your Vercel domain. Ollama can't run on free hosting (a model needs 3-4 GB RAM, Render free has
512 MB), so the cloud API uses Groq's hosted models instead (step 5).

With `GROQ_API_KEY` set (step 5) the live chat has full AI through Groq. Without it, the chat
answers with rules and a plain product search. CrewAI stays local-only.

## 1. Push the code

Render and Vercel deploy from GitHub, so `render.yaml` and the latest code must be on `main`.

## 2. Backend on Render (first, you need its URL)

1. Sign in at https://render.com with GitHub.
2. **New → Blueprint** → pick the `kad-ai` repository → it reads `render.yaml` → **Apply**.
   (Settings it creates: root `backend`, free plan, Python 3.12.9, `LLM_PROVIDER=groq`,
   `COOKIE_SECURE=true`, `TRUSTED_IP_HEADER=x-real-ip`.)
3. Wait for "Live" (first build ~3 min). Copy the URL, e.g. `https://kad-ai-api.onrender.com`.
4. Check it: open `https://kad-ai-api.onrender.com/api/categories`, you should see JSON.

## 3. Storefront on Vercel

1. Sign in at https://vercel.com with GitHub → **Add New → Project** → import `kad-ai`.
2. **Root Directory: `frontend`** (Framework preset: Next.js is detected).
3. **Environment Variables**: `API_URL` = your Render URL (no trailing slash).
4. **Deploy**. Open the `*.vercel.app` URL.

`API_URL` is read at build time for the `/api/*` rewrite: if you change it later, redeploy
(Deployments → ⋯ → Redeploy). The build itself works even while Render is asleep.

## 4. Try it

- Home page shows products and live prices → Vercel reaches Render.
- Chat: "Add two kilograms of apples to my cart" → instant, Confirm/Cancel.
- Chat: "How do I store bananas?" → an AI answer with web sources (after step 5).
- Register, log in, place a demo order.

## 5. Live AI with Groq + web search with Serper

The live API uses Groq's hosted models (`LLM_PROVIDER=groq`) instead of Ollama:
`openai/gpt-oss-20b` understands the question (JSON), `llama-3.3-70b-versatile` writes answers.
All the same guards apply: validated JSON, keyword filter, price guard, cart changes need Confirm.

1. https://console.groq.com → sign in → **API Keys → Create API Key**. Stay on the free plan
   (no card), so it can never cost money: when the free quota runs out, the chat falls back to rules.
2. https://serper.dev → sign up → copy the API key (free: 2,500 searches).
3. Render → `kad-ai-api` → **Environment** → add `GROQ_API_KEY` and `SERPER_API_KEY` → **Save, rebuild and deploy**.
4. Check: `https://kad-ai-api.onrender.com/api/assistant/status` shows `"provider": "groq", "reachable": true`.
   In the chat, "Papaya or pineapple, which one is sweeter?" shows `openai/gpt-oss-20b → llama-3.3-70b-versatile`;
   "How do I store bananas?" shows web sources under the answer.

Limits (change them under Environment):

| Setting | Default | Protects |
|---|---|---|
| `CHAT_PER_MINUTE` | 10 per visitor | spam |
| `GROQ_DAILY_LIMIT` | 500 AI calls/day, everyone together | Groq free quota |
| `SEARCH_DAILY_LIMIT` | 100 searches/day, everyone together | Serper credits (2,500 total) |
| `SEARCH_PER_IP_PER_HOUR` | 5 per visitor | one person using up the searches |

Web search only runs for food questions the store data can't answer (recipes, storage, ripeness,
season, and nutrition while no verified data exists). Its answer never contains prices, cites its
sources, and says it isn't checked by Kad AI. Questions like "who won the match?" never reach Serper.

## 6. Emails with Resend (welcome + newsletter)

1. Sign up at https://resend.com → **API Keys → Create API Key** (permission: Sending access). Copy it once.
2. Render → `kad-ai-api` → **Environment** → add `RESEND_API_KEY` = the key → **Save, rebuild and deploy**.
   Never commit the key or put it in Vercel (only the backend sends email).
3. Test: register on the live site with the **same email you used for Resend** → a welcome email arrives;
   subscribe to the newsletter → a confirmation arrives. Resend dashboard → **Emails** shows each send.

Sandbox limit: with the default sender `onboarding@resend.dev`, Resend only delivers to your own account
email (others get 403, logged as "Email not sent", and registration still succeeds). To email any
customer, add and verify a domain in Resend (DNS records), then set `EMAIL_FROM="Kad AI <hello@yourdomain>"`.

## Good to know

- **Cold start**: Render free sleeps after 15 min idle. The first visit after that can take
  30-60 s or show "The store server is waking up"; refresh and it works.
- **Data resets**: the SQLite file lives on Render's temporary disk. Every deploy/restart
  re-creates the demo catalog and drops accounts, carts and orders. Fine for a portfolio demo;
  for real data use a hosted Postgres (e.g. Neon free) via `DATABASE_URL`.
- **Abuse**: no AI runs in the cloud, so chat is cheap rules + search; it is also limited to
  10/min per visitor, orders to 5/hour. The Render URL itself is public: someone calling it
  directly can fake `x-real-ip` and dodge per-IP limits (nothing expensive behind it).
- **Updates**: every push to `main` redeploys both automatically.
- **Full AI online** would need a hosted model (e.g. Groq's free tier) or your laptop exposed
  with a tunnel. Not set up.
