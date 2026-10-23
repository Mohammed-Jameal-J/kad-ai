"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import s from "@/components/account/forms.module.css";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    if (form.get("password") !== form.get("confirm")) {
      setError("The two passwords don't match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(String(form.get("name")), String(form.get("email")), String(form.get("password")));
      router.push("/account");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account.");
      setBusy(false);
    }
  }

  return (
    <div className="container py-4">
      <div className={s.card}>
        <h1>Create your account</h1>
        <p className="km-muted mb-0">Save your details and see all your orders in one place.</p>
        <form onSubmit={onSubmit}>
          <div className="mb-3">
            <label htmlFor="name" className="form-label">Full name</label>
            <input id="name" name="name" className="form-control" required minLength={2} maxLength={80} autoComplete="name" />
          </div>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email</label>
            <input id="email" name="email" type="email" className="form-control" required maxLength={254} autoComplete="email" />
          </div>
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <input id="password" name="password" type="password" className="form-control" required minLength={8} maxLength={128} autoComplete="new-password" aria-describedby="password-help" />
            <div id="password-help" className="form-text">At least 8 characters.</div>
          </div>
          <div className="mb-3">
            <label htmlFor="confirm" className="form-label">Confirm password</label>
            <input id="confirm" name="confirm" type="password" className="form-control" required minLength={8} maxLength={128} autoComplete="new-password" />
          </div>
          {error && <div className="alert alert-danger py-2 small" role="alert">{error}</div>}
          <button type="submit" className="btn btn-km w-100" disabled={busy}>
            {busy && <span className="spinner-border spinner-border-sm me-2" />}Create account
          </button>
        </form>
        <p className={s.switch}>Already have an account? <Link href="/login">Log in</Link></p>
      </div>
    </div>
  );
}
