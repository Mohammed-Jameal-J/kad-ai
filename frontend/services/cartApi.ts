// Browser-side cart and order calls. Requests go to same-origin /api/*, which next.config.ts proxies to FastAPI.
import type { Cart, CheckoutDetails, Order } from "@/lib/types";

const CART_KEY = "kadai-cart-id";

function readCartId(): string | null {
  try {
    return localStorage.getItem(CART_KEY);
  } catch {
    return null; // private mode / storage blocked: a fresh cart is created on first add
  }
}

function saveCartId(id: string) {
  try {
    localStorage.setItem(CART_KEY, id);
  } catch {}
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const cartId = readCartId();
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(cartId ? { "X-Cart-Id": cartId } : {}) },
    });
  } catch {
    throw new Error("Couldn't reach the store. Check your connection.");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    // FastAPI sends a string for business errors and a list for validation (422) errors.
    // A 5xx without JSON means the proxy couldn't reach FastAPI at all.
    const fallback = res.status >= 500 ? "The store server is not responding right now." : "Please check the details and try again.";
    throw new Error(typeof body.detail === "string" ? body.detail : fallback);
  }
  if (body.cart_id) saveCartId(body.cart_id);
  return body as T;
}

export const fetchCart = () => request<Cart>("/cart");

export const addCartItem = (productId: number, quantity = 1) =>
  request<Cart>("/cart/items", { method: "POST", body: JSON.stringify({ product_id: productId, quantity }) });

export const updateCartItem = (itemId: number, quantity: number) =>
  request<Cart>(`/cart/items/${itemId}`, { method: "PATCH", body: JSON.stringify({ quantity }) });

export const removeCartItem = (itemId: number) => request<Cart>(`/cart/items/${itemId}`, { method: "DELETE" });

export const placeOrder = (details: CheckoutDetails) =>
  request<Order>("/orders", { method: "POST", body: JSON.stringify(details) });
