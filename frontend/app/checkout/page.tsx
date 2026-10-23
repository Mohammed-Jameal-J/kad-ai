"use client";

import Link from "next/link";
import { useState } from "react";
import Breadcrumb from "@/components/listing/Breadcrumb";
import CartLoadError from "@/components/ui/CartLoadError";
import { useAuth } from "@/hooks/useAuth";
import { useCart } from "@/hooks/useCart";
import { rupees } from "@/lib/format";
import type { CheckoutDetails, DeliverySlot, Order } from "@/lib/types";
import s from "./checkout.module.css";

const SLOTS: { value: DeliverySlot; label: string }[] = [
  { value: "08-12", label: "Morning, 8 AM to 12 PM" },
  { value: "12-16", label: "Afternoon, 12 PM to 4 PM" },
  { value: "16-20", label: "Evening, 4 PM to 8 PM" },
];

function Confirmation({ order }: { order: Order }) {
  const slot = SLOTS.find((x) => x.value === order.delivery_slot)?.label;
  return (
    <div className={s.confirm}>
      <i className="bi bi-check-circle-fill" />
      <h1 className="h3">Demo order placed</h1>
      <p className="km-muted">{order.notice}</p>
      <dl className={s.facts}>
        <div><dt>Order id</dt><dd><code>{order.id.slice(0, 8)}</code></dd></div>
        <div><dt>Name</dt><dd>{order.customer_name}</dd></div>
        <div><dt>Delivery slot</dt><dd>{slot}</dd></div>
        <div><dt>Payment</dt><dd>Cash on delivery (demo, nothing collected)</dd></div>
      </dl>
      <ul className={s.summaryLines}>
        {order.items.map((i) => (
          <li key={i.product_id}>
            <span>{i.quantity} × {i.unit} {i.product_name}</span>
            <span>{rupees(i.line_total_paise)}</span>
          </li>
        ))}
        <li className={s.total}><span>Total</span><span>{rupees(order.total_paise)}</span></li>
      </ul>
      <Link href="/products" className="btn btn-km mt-3">Continue shopping</Link>
    </div>
  );
}

export default function CheckoutPage() {
  const { cart, loading, loadError, checkout } = useCart();
  const { user } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const items = cart?.items ?? [];
  const blocked = items.some((i) => !i.available);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const details: CheckoutDetails = {
      customer_name: String(form.get("customer_name")),
      phone: String(form.get("phone")),
      address: String(form.get("address")),
      delivery_slot: String(form.get("delivery_slot")) as DeliverySlot,
    };
    setSubmitting(true);
    setError(null);
    try {
      setOrder(await checkout(details));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not place the order.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Cart", href: "/cart" }, { label: "Checkout" }]} />
      <div className="container py-4">
        {order ? (
          <Confirmation order={order} />
        ) : (
          <>
            <div className={s.demoBanner} role="note">
              <i className="bi bi-info-circle-fill" />
              <span>
                <strong>Demo checkout.</strong> No payment is taken, no card details are asked for, and nothing will be
                delivered. Your details are saved only in the local demo database on this computer.
              </span>
            </div>
            <h1 className="h3 mb-4">Checkout</h1>

            {loading ? (
              <div className="km-skeleton" style={{ height: 320 }} aria-busy="true" />
            ) : loadError ? (
              <CartLoadError />
            ) : items.length === 0 ? (
              <div className="km-empty">
                <i className="bi bi-bag d-block mb-2" />
                <p>Your cart is empty, so there is nothing to check out.</p>
                <Link href="/products" className="btn btn-km">Browse products</Link>
              </div>
            ) : (
              <div className="row g-4">
                <div className="col-12 col-lg-7">
                  <form className={s.form} onSubmit={onSubmit}>
                    <h2 className="h5">Delivery details</h2>
                    <div className="mb-3">
                      <label htmlFor="customer_name" className="form-label">Full name</label>
                      <input id="customer_name" name="customer_name" className="form-control" required minLength={2} maxLength={80} autoComplete="name" defaultValue={user?.name} key={user?.id ?? "guest"} />
                      {user && <div className="form-text">This order will be saved to your account.</div>}
                    </div>
                    <div className="mb-3">
                      <label htmlFor="phone" className="form-label">Phone</label>
                      <input id="phone" name="phone" type="tel" className="form-control" required pattern="\+?[0-9][0-9 \-]{6,18}" placeholder="+91 98765 43210" autoComplete="tel" />
                    </div>
                    <div className="mb-3">
                      <label htmlFor="address" className="form-label">Delivery address</label>
                      <textarea id="address" name="address" className="form-control" rows={3} required minLength={5} maxLength={300} autoComplete="street-address" />
                    </div>
                    <fieldset className="mb-3">
                      <legend className="form-label fs-6">Delivery slot (next day)</legend>
                      {SLOTS.map((slot, i) => (
                        <div key={slot.value} className="form-check">
                          <input className="form-check-input" type="radio" name="delivery_slot" id={`slot-${slot.value}`} value={slot.value} defaultChecked={i === 0} />
                          <label className="form-check-label" htmlFor={`slot-${slot.value}`}>{slot.label}</label>
                        </div>
                      ))}
                    </fieldset>
                    <div className={s.payment}>
                      <i className="bi bi-cash-coin" />
                      <span>Payment: <strong>cash on delivery (demo)</strong>. Nothing is charged.</span>
                    </div>
                    {error && (
                      <div className="alert alert-danger py-2 small" role="alert">
                        {error} <Link href="/cart">Review your cart</Link>
                      </div>
                    )}
                    <button type="submit" className="btn btn-km btn-lg w-100" disabled={submitting || blocked}>
                      {submitting && <span className="spinner-border spinner-border-sm me-2" />}
                      Place demo order · {rupees(cart?.subtotal_paise ?? 0)}
                    </button>
                    {blocked && <p className="small text-danger mt-2 mb-0">Some items exceed available stock. Please update your cart first.</p>}
                  </form>
                </div>
                <div className="col-12 col-lg-5">
                  <aside className={s.summary}>
                    <h2 className="h5">Order summary</h2>
                    <ul className={s.summaryLines}>
                      {items.map((line) => (
                        <li key={line.id}>
                          <span>{line.quantity} × {line.product.unit} {line.product.name}</span>
                          <span>{rupees(line.line_total_paise)}</span>
                        </li>
                      ))}
                      <li className={s.total}><span>Total</span><span>{rupees(cart?.subtotal_paise ?? 0)}</span></li>
                    </ul>
                    <p className="km-note mb-0">The server re-checks stock and recalculates prices when you place the order. {cart?.price_note}</p>
                  </aside>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
