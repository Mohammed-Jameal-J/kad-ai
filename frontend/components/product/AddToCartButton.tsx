"use client";

import { useState } from "react";
import { useCart } from "@/hooks/useCart";
import s from "./product-card.module.css";

type Props = { productId: number; name: string; inStock: boolean; variant?: "icon" | "full"; quantity?: number };

export default function AddToCartButton({ productId, name, inStock, variant = "icon", quantity = 1 }: Props) {
  const { add } = useCart();
  const [busy, setBusy] = useState(false);

  async function onClick() {
    setBusy(true);
    await add(productId, quantity, name);
    setBusy(false);
  }

  const label = inStock ? `Add ${name} to cart` : `${name} is out of stock`;
  if (variant === "full") {
    return (
      <button type="button" className="btn btn-km btn-lg" onClick={onClick} disabled={!inStock || busy}>
        {busy ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-bag-plus me-2" />}
        {inStock ? "Add to cart" : "Out of stock"}
      </button>
    );
  }
  return (
    <button type="button" className={s.cartBtn} onClick={onClick} disabled={!inStock || busy} aria-label={label} title={label}>
      {busy ? <span className="spinner-border spinner-border-sm" /> : <i className="bi bi-cart-plus" />}
    </button>
  );
}
