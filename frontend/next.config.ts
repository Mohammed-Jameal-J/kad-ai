import type { NextConfig } from "next";

// Server-only: where Next.js reaches FastAPI. Never exposed to the browser bundle.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  experimental: {
    // Rewrites are proxied with a 30 s default timeout; local LLM replies can take over a minute
    // (model load + swap). Keep this above the backend's OLLAMA_READ_TIMEOUT (180 s).
    proxyTimeout: 200_000,
  },
  // The browser calls same-origin /api/*; Next.js proxies it to FastAPI (no CORS, no exposed URL).
  // ponytail: no Content-Security-Policy yet; Next's inline scripts need a nonce set up via proxy.ts.
  // Add one before deploying anywhere public.
  headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
  rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
