"use client";

import Image from "next/image";
import { useState } from "react";
import { subscribeNewsletter } from "@/services/authApi";
import s from "./home.module.css";

export default function Newsletter() {
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await subscribeNewsletter(String(new FormData(e.currentTarget).get("email")));
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not subscribe. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="container km-section pb-0">
      <div className={s.newsletter}>
        <div className={s.newsletterText}>
          <h2>Join our newsletter</h2>
          <p>Seasonal picks, storage tips and weekly deals.</p>
          {done ? (
            <p className={s.newsletterDone} role="status">
              <i className="bi bi-check-circle-fill me-2" />
              Thanks for subscribing! Check your inbox for a confirmation email.
            </p>
          ) : (
            <form onSubmit={onSubmit}>
              <div className={s.newsletterField}>
                <label htmlFor="newsletter-email" className="visually-hidden">
                  Email address
                </label>
                <input id="newsletter-email" name="email" type="email" required placeholder="Your email address" maxLength={254} />
                <button type="submit" disabled={busy}>{busy ? "Subscribing…" : "Subscribe"}</button>
              </div>
              <div className="form-check mt-2">
                <input className="form-check-input" type="checkbox" id="newsletter-consent" required />
                <label className="form-check-label small" htmlFor="newsletter-consent">
                  I agree to receive emails from Kad AI. Unsubscribe any time.
                </label>
              </div>
              {error && <p className="text-danger small mt-2 mb-0" role="alert">{error}</p>}
            </form>
          )}
        </div>
        <div className={s.newsletterImage}>
          <Image src="/images/banners/newsletter.jpg" alt="" fill sizes="(max-width: 768px) 0px, 60vw" />
        </div>
      </div>
    </section>
  );
}
