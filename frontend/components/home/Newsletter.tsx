"use client";

import Image from "next/image";
import { useState } from "react";
import s from "./home.module.css";

export default function Newsletter() {
  const [done, setDone] = useState(false);

  return (
    <section className="container km-section pb-0">
      <div className={s.newsletter}>
        <div className={s.newsletterText}>
          <h2>Join our newsletter</h2>
          <p>Seasonal picks, storage tips and weekly deals.</p>
          {done ? (
            <p className={s.newsletterDone} role="status">
              <i className="bi bi-check-circle-fill me-2" />
              Thanks! This is a demo, so your email was not stored or sent anywhere.
            </p>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setDone(true);
              }}
            >
              <div className={s.newsletterField}>
                <label htmlFor="newsletter-email" className="visually-hidden">
                  Email address
                </label>
                <input id="newsletter-email" type="email" required placeholder="Your email address" maxLength={120} />
                <button type="submit">Subscribe</button>
              </div>
              <div className="form-check mt-2">
                <input className="form-check-input" type="checkbox" id="newsletter-consent" required />
                <label className="form-check-label small" htmlFor="newsletter-consent">
                  I agree to receive emails (demo only, nothing is sent)
                </label>
              </div>
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
