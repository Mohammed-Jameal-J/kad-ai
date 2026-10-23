"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { Cart, CheckoutDetails, Order } from "@/lib/types";
import { addCartItem, fetchCart, placeOrder, removeCartItem, updateCartItem } from "@/services/cartApi";

type Toast = { text: string; kind: "success" | "error" };

type CartContextValue = {
  cart: Cart | null;
  loading: boolean;
  /** Set when the cart could not be loaded (e.g. backend down), so pages don't claim it is empty. */
  loadError: string | null;
  reload: () => void;
  count: number;
  add: (productId: number, quantity: number, name: string) => Promise<boolean>;
  update: (itemId: number, quantity: number) => Promise<boolean>;
  remove: (itemId: number) => Promise<boolean>;
  addMany: (items: { product_id: number; quantity: number }[]) => Promise<boolean>;
  checkout: (details: CheckoutDetails) => Promise<Order>;
};

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const flash = useCallback((text: string, kind: Toast["kind"]) => {
    setToast({ text, kind });
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setToast(null), 3500);
  }, []);

  // State updates happen only after the fetch settles, so this is safe to start from an effect.
  const load = useCallback(() => {
    fetchCart()
      .then((c) => {
        setCart(c);
        setLoadError(null);
      })
      .catch((e) => setLoadError(e instanceof Error ? e.message : "Couldn't load your cart"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const reload = useCallback(() => {
    setLoading(true);
    load();
  }, [load]);

  const run = useCallback(
    async (action: () => Promise<Cart>, success?: string) => {
      try {
        setCart(await action());
        if (success) flash(success, "success");
        return true;
      } catch (e) {
        flash(e instanceof Error ? e.message : "Something went wrong", "error");
        return false;
      }
    },
    [flash],
  );

  const value: CartContextValue = {
    cart,
    loading,
    loadError,
    reload,
    count: cart?.item_count ?? 0,
    add: (productId, quantity, name) => run(() => addCartItem(productId, quantity), `${name} added to your cart`),
    update: (itemId, quantity) => run(() => updateCartItem(itemId, quantity)),
    remove: (itemId) => run(() => removeCartItem(itemId), "Item removed"),
    // Used when the customer confirms an assistant proposal. Each add goes through the normal
    // cart API, which re-checks stock; we stop at the first failure and report it.
    addMany: (items) =>
      run(async () => {
        let latest: Cart | null = null;
        for (const item of items) latest = await addCartItem(item.product_id, item.quantity);
        return latest ?? fetchCart();
      }, "Added to your cart"),
    checkout: async (details) => {
      const order = await placeOrder(details); // throws with the server's message on failure
      setCart(await fetchCart().catch(() => null)); // server emptied the cart
      return order;
    },
  };

  return (
    <CartContext.Provider value={value}>
      {children}
      <div className="km-toast-region" aria-live="polite">
        {toast && (
          <div className={`km-toast km-toast-${toast.kind}`} role="status">
            <i className={`bi ${toast.kind === "success" ? "bi-check-circle-fill" : "bi-exclamation-circle-fill"}`} />
            {toast.text}
          </div>
        )}
      </div>
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}
