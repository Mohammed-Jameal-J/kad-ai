"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import s from "./spin.module.css";

export const PRIZES = ["10% off", "Free delivery", "₹50 off", "5% off", "Free coriander", "15% off"];
const SEEN_KEY = "kadai-spin-seen";
export const PRIZE_KEY = "kadai-offer";
const SLICE = 360 / PRIZES.length;
const SKIP_PATHS = ["/register", "/login", "/checkout", "/account"];

function storage(action: (ls: Storage) => string | null | void) {
  try {
    return action(localStorage); // private mode / blocked storage: just behave as "not seen"
  } catch {
    return null;
  }
}

// Shown once per browser, a few seconds after a guest lands on a shopping page.
export default function SpinOffer() {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const dialog = useRef<HTMLDialogElement>(null);
  const [angle, setAngle] = useState(0);
  const [prize, setPrize] = useState<string | null>(null);
  const [spinning, setSpinning] = useState(false);

  useEffect(() => {
    if (loading || user || SKIP_PATHS.some((p) => pathname.startsWith(p))) return;
    if (storage((ls) => ls.getItem(SEEN_KEY))) return;
    const id = setTimeout(() => {
      storage((ls) => ls.setItem(SEEN_KEY, "1"));
      dialog.current?.showModal();
    }, 6000);
    return () => clearTimeout(id);
  }, [loading, user, pathname]);

  function spin() {
    const won = Math.floor(Math.random() * PRIZES.length);
    // Land the middle of slice `won` under the pointer at the top, after 5 full turns.
    setAngle(360 * 5 + (360 - (won * SLICE + SLICE / 2)));
    setSpinning(true);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setTimeout(() => {
      setPrize(PRIZES[won]);
      setSpinning(false);
      storage((ls) => ls.setItem(PRIZE_KEY, PRIZES[won]));
    }, reduced ? 0 : 4200);
  }

  return (
    <dialog ref={dialog} className={s.dialog} aria-labelledby="spin-title">
      <button type="button" className={s.close} onClick={() => dialog.current?.close()} aria-label="Close">
        <i className="bi bi-x-lg" />
      </button>
      <span className="km-eyebrow">Welcome offer</span>
      <h2 id="spin-title" className={s.title}>{prize ? `You won ${prize}!` : "Spin to win a welcome gift"}</h2>
      <p className="km-muted small mb-3">
        {prize ? "Create your free account to keep your gift." : "One spin per visitor. Every slice is a winner."}
      </p>

      <div className={s.wheelBox}>
        <span className={s.pointer} aria-hidden="true" />
        <div className={s.wheel} style={{ transform: `rotate(${angle}deg)` }} aria-hidden="true">
          {PRIZES.map((p, i) => (
            <span key={p} className={s.label} style={{ transform: `rotate(${i * SLICE + SLICE / 2}deg)` }}>
              {p}
            </span>
          ))}
        </div>
        <span className={s.hub} aria-hidden="true" />
      </div>
      <p className="visually-hidden" aria-live="polite">{prize ? `You won ${prize}` : spinning ? "Spinning" : ""}</p>

      {prize ? (
        <Link href="/register" className="btn btn-km w-100" onClick={() => dialog.current?.close()}>
          Register and claim <i className="bi bi-arrow-right ms-1" />
        </Link>
      ) : (
        <button type="button" className="btn btn-km w-100" onClick={spin} disabled={spinning}>
          {spinning ? "Spinning…" : "Spin the wheel"}
        </button>
      )}
      <p className={s.note}>Demo store: gifts are a preview and are not applied to checkout yet.</p>
    </dialog>
  );
}
