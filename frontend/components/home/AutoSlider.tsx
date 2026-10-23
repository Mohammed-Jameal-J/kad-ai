"use client";

import { Children, useEffect, useRef, useState, type ReactNode } from "react";
import s from "./home.module.css";

type Props = { children: ReactNode; label: string; slideClassName: string; className?: string; interval?: number };

// Swiping and snapping are native CSS scroll-snap; this only moves one slide every `interval` ms.
// Pauses on hover/focus and while the tab is hidden; never moves with reduced motion.
export default function AutoSlider({ children, label, slideClassName, className = "", interval = 5000 }: Props) {
  const slides = Children.toArray(children);
  const track = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      const el = track.current;
      const first = el?.firstElementChild as HTMLElement | null;
      if (!el || !first || document.hidden) return;
      const step = first.offsetWidth + (parseFloat(getComputedStyle(el).columnGap) || 0); // "normal" gap → NaN → 0
      const pos = Math.abs(el.scrollLeft); // RTL scrollLeft runs 0 → negative
      const next = pos + el.clientWidth >= el.scrollWidth - 4 ? 0 : pos + step; // loop back at the end
      el.scrollTo({ left: getComputedStyle(el).direction === "rtl" ? -next : next, behavior: "smooth" });
    }, interval);
    return () => clearInterval(id);
  }, [paused, interval]);

  return (
    <div
      ref={track}
      className={`${s.sliderTrack} ${className}`}
      role="region"
      aria-roledescription="carousel"
      aria-label={label}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      {slides.map((slide, i) => (
        <div key={i} className={slideClassName} role="group" aria-roledescription="slide" aria-label={`${i + 1} of ${slides.length}`}>
          {slide}
        </div>
      ))}
    </div>
  );
}
