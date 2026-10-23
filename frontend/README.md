# Kad AI storefront (Next.js)

Next.js 16 (App Router, Cache Components) + React 19 + TypeScript + Bootstrap 5. No Tailwind.

```powershell
npm install
npm run dev      # http://localhost:3000  (needs the FastAPI backend on :8000)
npm run lint
npm run build
```

- `app/` routes: `/`, `/products`, `/category/[slug]`, `/product/[slug]`, `/cart`, `/checkout`, `/login`, `/register`, `/account`, `/contact`, `/blog`
- `components/` UI (CSS Modules next to each component), `styles/globals.css` design tokens
- `lib/api.ts` server-side API client, `services/cartApi.ts` browser cart calls, `hooks/useCart.tsx` cart state
- `public/images/` public-domain/CC0 photos (sources in `../docs/photo-sources.json`); `public/brand/` logos; `app/icon.png` favicon

`API_URL` (server-only, default `http://127.0.0.1:8000`) tells Next.js where FastAPI is. The browser calls
`/api/*` on the same origin and `next.config.ts` proxies it, so the backend address is never in client code.
