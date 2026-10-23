"use client";

import { useState } from "react";
import AddToCartButton from "./AddToCartButton";

const MAX_PER_LINE = 50; // same limit as the backend (schemas/cart.py)

export function QuantityStepper({ value, max, onChange, label }: { value: number; max: number; onChange: (n: number) => void; label: string }) {
  return (
    <div className="input-group" style={{ width: 132 }}>
      <button type="button" className="btn btn-outline-secondary" onClick={() => onChange(value - 1)} disabled={value <= 1} aria-label={`Decrease ${label}`}>
        −
      </button>
      <input
        className="form-control text-center"
        inputMode="numeric"
        value={value}
        aria-label={label}
        onChange={(e) => {
          const n = Number(e.target.value.replace(/\D/g, ""));
          if (n >= 1) onChange(Math.min(n, max));
        }}
      />
      <button type="button" className="btn btn-outline-secondary" onClick={() => onChange(value + 1)} disabled={value >= max} aria-label={`Increase ${label}`}>
        +
      </button>
    </div>
  );
}

export default function QuantityAddToCart({ productId, name, unit, stock }: { productId: number; name: string; unit: string; stock: number }) {
  const max = Math.max(1, Math.min(stock, MAX_PER_LINE));
  const [qty, setQty] = useState(1);
  return (
    <div className="d-flex flex-wrap align-items-center gap-3">
      <QuantityStepper value={qty} max={max} onChange={(n) => setQty(Math.max(1, Math.min(n, max)))} label={`Quantity in ${unit}`} />
      <AddToCartButton productId={productId} name={name} inStock={stock > 0} variant="full" quantity={qty} />
    </div>
  );
}
