// Server-side API client, used by Server Components only. Browser code uses services/cartApi.ts.
import type { Category, ProductDetail, ProductFilters, ProductPage } from "./types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function toQuery(params: object): string {
  const entries = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "" && v !== false)
    .map(([k, v]) => [k, String(v)]);
  return entries.length ? `?${new URLSearchParams(entries)}` : "";
}

async function get<T>(path: string, params: object = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}${toQuery(params)}`);
  } catch {
    throw new ApiError(503, "The store server is waking up or not reachable. Please refresh in a few seconds.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Invalid request";
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export type Settled<T> = { ok: true; data: T } | { ok: false; error: unknown };

/** Await a fetch without throwing, so components can render an error state outside try/catch. */
export async function settle<T>(promise: Promise<T>): Promise<Settled<T>> {
  try {
    return { ok: true, data: await promise };
  } catch (error) {
    return { ok: false, error };
  }
}

export const getCategories = () => get<Category[]>("/api/categories");

export const getProducts = (filters: ProductFilters = {}) => get<ProductPage>("/api/products", filters);

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  try {
    return await get<ProductDetail>(`/api/products/${encodeURIComponent(slug)}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
