"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import s from "@/components/account/forms.module.css";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      router.push("/account");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
      setBusy(false);
    }
  }

  return (
    <div className="container py-4">
      <div className={s.card}>
        <h1>Welcome back</h1>
        <p className="km-muted mb-0">Log in to see your orders.</p>
        <form onSubmit={onSubmit}>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email</label>
            <input id="email" name="email" type="email" className="form-control" required maxLength={254} autoComplete="email" />
          </div>
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <input id="password" name="password" type="password" className="form-control" required maxLength={128} autoComplete="current-password" />
          </div>
          {error && <div className="alert alert-danger py-2 small" role="alert">{error}</div>}
          <button type="submit" className="btn btn-km w-100" disabled={busy}>
            {busy && <span className="spinner-border spinner-border-sm me-2" />}Log in
          </button>
        </form>
        <p className={s.switch}>New to Kad AI? <Link href="/register">Create an account</Link></p>
      </div>
    </div>
  );
}
