import type { NextConfig } from "next";

// Server-only: where Next.js reaches FastAPI. Never exposed to the browser bundle.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
const isDev = process.env.NODE_ENV !== "production";

// Everything (scripts, fonts, images, API) is same-origin, so the policy can be strict.
// ponytail: 'unsafe-inline' scripts because Next's inline bootstrap scripts need it without nonces,
// and nonces (proxy.ts) would make every page dynamic. Still blocks third-party scripts, plugins,
// framing, <base> hijacking and off-site form posts. Dev adds eval + websocket for hot reload.
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  `connect-src 'self'${isDev ? " ws:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  ...(isDev ? [] : ["upgrade-insecure-requests"]),
].join("; ");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  experimental: {
    // Rewrites are proxied with a 30 s default timeout; local LLM replies can take over a minute
    // (model load + swap). Keep this above the backend's OLLAMA_READ_TIMEOUT (180 s).
    proxyTimeout: 200_000,
  },
  // The browser calls same-origin /api/*; Next.js proxies it to FastAPI (no CORS, no exposed URL).
  headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Content-Security-Policy", value: CSP },
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
          // HTTPS only once deployed; on http://localhost HSTS would just be ignored or get in the way.
          ...(isDev ? [] : [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" }]),
        ],
      },
    ];
  },
  rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
