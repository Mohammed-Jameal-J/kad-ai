"use client";

import { useState } from "react";
import s from "@/components/account/forms.module.css";
import Breadcrumb from "@/components/listing/Breadcrumb";
import { sendContact } from "@/services/authApi";

export default function ContactPage() {
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await sendContact(String(form.get("name")), String(form.get("email")), String(form.get("message")));
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send your message.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Contact us" }]} />
      <div className="container py-4">
        <h1 className="h3">Contact us</h1>
        <p className="km-muted">Questions about an order, delivery areas or a product? Send us a message.</p>
        <div className="row g-4 mt-1">
          <div className="col-12 col-lg-7">
            <div className={s.panel}>
              {sent ? (
                <p className="mb-0" role="status">
                  <i className="bi bi-check-circle-fill text-success me-2" />
                  Thanks! Your message has been received. We usually reply within one working day.
                </p>
              ) : (
                <form onSubmit={onSubmit}>
                  <div className="row g-3">
                    <div className="col-12 col-md-6">
                      <label htmlFor="name" className="form-label">Name</label>
                      <input id="name" name="name" className="form-control" required minLength={2} maxLength={80} autoComplete="name" />
                    </div>
                    <div className="col-12 col-md-6">
                      <label htmlFor="email" className="form-label">Email</label>
                      <input id="email" name="email" type="email" className="form-control" required maxLength={254} autoComplete="email" />
                    </div>
                    <div className="col-12">
                      <label htmlFor="message" className="form-label">Message</label>
                      <textarea id="message" name="message" className="form-control" rows={5} required minLength={10} maxLength={2000} />
                    </div>
                  </div>
                  {error && <div className="alert alert-danger py-2 small mt-3 mb-0" role="alert">{error}</div>}
                  <button type="submit" className="btn btn-km mt-3" disabled={busy}>
                    {busy && <span className="spinner-border spinner-border-sm me-2" />}Send message
                  </button>
                </form>
              )}
            </div>
          </div>
          <div className="col-12 col-lg-5">
            <aside className={s.info}>
              <p><i className="bi bi-geo-alt-fill" /><span>Kad AI<br />Coimbatore, Tamil Nadu</span></p>
              <p><i className="bi bi-clock-fill" /><span>Monday to Saturday, 8 AM to 8 PM</span></p>
              <p className="mb-0"><i className="bi bi-chat-dots-fill" /><span>For quick product questions, try the Ask Kad AI assistant at the bottom right.</span></p>
            </aside>
          </div>
        </div>
      </div>
    </>
  );
}
