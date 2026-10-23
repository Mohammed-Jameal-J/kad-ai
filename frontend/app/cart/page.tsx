"use client";

import Link from "next/link";
import Breadcrumb from "@/components/listing/Breadcrumb";
import ProductImage from "@/components/product/ProductImage";
import { QuantityStepper } from "@/components/product/QuantityAddToCart";
import CartLoadError from "@/components/ui/CartLoadError";
import { useCart } from "@/hooks/useCart";
import { rupees } from "@/lib/format";
import s from "./cart.module.css";

export default function CartPage() {
  const { cart, loading, loadError, update, remove } = useCart();
  const items = cart?.items ?? [];

  return (
    <>
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Cart" }]} />
      <div className="container py-4">
        <h1 className="h3 mb-4">Your cart</h1>
        {loading ? (
          <div className="km-skeleton" style={{ height: 240 }} aria-busy="true" />
        ) : loadError ? (
          <CartLoadError />
        ) : items.length === 0 ? (
          <div className="km-empty">
            <i className="bi bi-bag d-block mb-2" />
            <p>Your cart is empty.</p>
            <Link href="/products" className="btn btn-km">Browse products</Link>
          </div>
        ) : (
          <div className="row g-4">
            <div className="col-12 col-lg-8">
              <ul className={s.lines}>
                {items.map((line) => {
                  const max = Math.min(line.product.stock_quantity, 50);
                  return (
                    <li key={line.id} className={s.line}>
                      <ProductImage src={line.product.image_path} alt="" size={88} className={s.thumb} />
                      <div className={s.info}>
                        <Link href={`/product/${line.product.slug}`} className={s.name}>{line.product.name}</Link>
                        <span className="km-note">{rupees(line.unit_price_paise)} / {line.product.unit}</span>
                        {!line.available && (
                          <span className={s.warn}>
                            <i className="bi bi-exclamation-triangle me-1" />
                            Only {line.product.stock_quantity} in stock. Please reduce the quantity.
                          </span>
                        )}
                      </div>
                      <QuantityStepper value={line.quantity} max={Math.max(max, 1)} onChange={(n) => update(line.id, n)} label={`Quantity of ${line.product.name}`} />
                      <strong className={s.total}>{rupees(line.line_total_paise)}</strong>
                      <button type="button" className={s.remove} onClick={() => remove(line.id)} aria-label={`Remove ${line.product.name}`}>
                        <i className="bi bi-trash3" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div className="col-12 col-lg-4">
              <aside className={s.summary}>
                <h2 className="h5">Order summary</h2>
                <dl>
                  <div><dt>Items</dt><dd>{cart?.item_count}</dd></div>
                  <div className={s.subtotal}><dt>Subtotal</dt><dd>{rupees(cart?.subtotal_paise ?? 0)}</dd></div>
                </dl>
                <p className="km-note">Subtotal calculated by the server from current database prices. {cart?.price_note}</p>
                <Link href="/checkout" className="btn btn-km w-100">
                  Proceed to checkout (demo)
                </Link>
                <Link href="/products" className="btn btn-link w-100 mt-1 km-muted">Continue shopping</Link>
              </aside>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
