"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import s from "@/components/account/forms.module.css";
import { useAuth } from "@/hooks/useAuth";
import { rupees } from "@/lib/format";
import type { Order } from "@/lib/types";
import { myOrders } from "@/services/authApi";

const SLOT_LABELS: Record<string, string> = { "08-12": "8 AM – 12 PM", "12-16": "12 – 4 PM", "16-20": "4 – 8 PM" };

function Orders() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    myOrders().then(setOrders).catch((e) => setError(e instanceof Error ? e.message : "Couldn't load orders."));
  }, []);

  if (error) return <p className="text-danger small mb-0" role="alert">{error}</p>;
  if (!orders) return <div className="km-skeleton" style={{ height: 120 }} aria-busy="true" />;
  if (!orders.length) {
    return (
      <p className="km-muted mb-0">
        No orders yet. <Link href="/products">Start shopping</Link>
      </p>
    );
  }
  return (
    <ul className={s.orders}>
      {orders.map((o) => (
        <li key={o.id}>
          <span>
            <strong>#{o.id.slice(0, 8)}</strong>
            <span className="km-muted"> · {o.items.reduce((n, i) => n + i.quantity, 0)} items · slot {SLOT_LABELS[o.delivery_slot] ?? o.delivery_slot}</span>
            <br />
            <span className="km-note">{o.items.map((i) => i.product_name).join(", ")}</span>
          </span>
          <span className="text-end">
            <strong>{rupees(o.total_paise)}</strong>
            <br />
            <span className="badge text-bg-light">Demo order</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function AccountPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  if (loading) return <div className="container py-5"><div className="km-skeleton" style={{ height: 240 }} /></div>;

  if (!user) {
    return (
      <div className="container py-5">
        <div className="km-empty">
          <i className="bi bi-person-circle d-block mb-2" />
          <p>Please log in to see your account.</p>
          <Link href="/login" className="btn btn-km me-2">Log in</Link>
          <Link href="/register" className="btn btn-km-outline">Create account</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <h1 className="h3 mb-4">My account</h1>
      <div className="row g-4">
        <div className="col-12 col-lg-4">
          <section className={s.panel}>
            <h2>Profile</h2>
            <p className="mb-1"><strong>{user.name}</strong></p>
            <p className="km-muted mb-1">{user.email}</p>
            <p className="km-note">Member since {new Date(user.created_at).toLocaleDateString("en-IN")}</p>
            <button
              type="button"
              className="btn btn-km-outline btn-sm"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
            >
              <i className="bi bi-box-arrow-right me-1" />Log out
            </button>
          </section>
        </div>
        <div className="col-12 col-lg-8">
          <section className={s.panel}>
            <h2>My orders</h2>
            <Orders />
          </section>
        </div>
      </div>
    </div>
  );
}
