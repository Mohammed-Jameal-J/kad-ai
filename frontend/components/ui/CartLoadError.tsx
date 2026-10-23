"use client";

import { useCart } from "@/hooks/useCart";

/** Shown instead of "your cart is empty" when the cart could not be loaded at all. */
export default function CartLoadError() {
  const { loadError, reload } = useCart();
  return (
    <div className="km-empty" role="alert">
      <i className="bi bi-wifi-off d-block mb-2" />
      <p>{loadError ?? "Couldn't load your cart."} Is the backend running?</p>
      <button type="button" className="btn btn-km" onClick={reload}>Try again</button>
    </div>
  );
}
