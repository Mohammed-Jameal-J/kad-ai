// Account calls. The session lives in an HttpOnly cookie set by FastAPI; the browser sends it
// automatically on same-origin /api requests, and page scripts can never read it.
import type { Order } from "@/lib/types";

export type User = { id: number; name: string; email: string; created_at: string };

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { ...init, headers: { "Content-Type": "application/json" } });
  } catch {
    throw new Error("Couldn't reach the store. Check your connection.");
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const fallback = res.status >= 500 ? "The store server is not responding right now." : "Please check the details and try again.";
    throw Object.assign(new Error(typeof body.detail === "string" ? body.detail : fallback), { status: res.status });
  }
  return body as T;
}

export const register = (name: string, email: string, password: string) =>
  call<User>("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) });

export const login = (email: string, password: string) =>
  call<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });

export const logout = () => call<void>("/auth/logout", { method: "POST" });

export async function me(): Promise<User | null> {
  try {
    return await call<User>("/auth/me");
  } catch (e) {
    if ((e as { status?: number }).status === 401) return null; // guest
    throw e;
  }
}

export const myOrders = () => call<Order[]>("/orders/mine");

export const sendContact = (name: string, email: string, message: string) =>
  call<{ status: string }>("/contact", { method: "POST", body: JSON.stringify({ name, email, message }) });

export const subscribeNewsletter = (email: string) =>
  call<{ status: string }>("/newsletter", { method: "POST", body: JSON.stringify({ email }) });
