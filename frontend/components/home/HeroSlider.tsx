"use client";

import { Children, useEffect, useRef, useState, type ReactNode } from "react";
import s from "./home.module.css";

const AUTOPLAY_MS = 6000;

// Swipe and snapping are native CSS scroll-snap; this only adds arrows, dots and autoplay.
// Autoplay pauses on hover/focus, while the tab is hidden, and never runs with reduced motion.
export default function HeroSlider({ children, label }: { children: ReactNode; label: string }) {
  const slides = Children.toArray(children);
  const track = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  const goTo = (i: number) => {
    const el = track.current;
    if (!el) return;
    const next = (i + slides.length) % slides.length;
    const rtl = getComputedStyle(el).direction === "rtl"; // RTL scrollLeft runs 0 → negative
    el.scrollTo({ left: (rtl ? -1 : 1) * next * el.clientWidth, behavior: "smooth" });
  };

  useEffect(() => {
    if (paused || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      if (!document.hidden) goTo(index + 1);
    }, AUTOPLAY_MS);
    return () => clearInterval(id);
  });

  return (
    <div
      className={s.slider}
      role="region"
      aria-roledescription="carousel"
      aria-label={label}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div
        ref={track}
        className={s.sliderTrack}
        onScroll={(e) => setIndex(Math.round(Math.abs(e.currentTarget.scrollLeft) / e.currentTarget.clientWidth))}
      >
        {slides.map((slide, i) => (
          <div
            key={i}
            className={s.slide}
            role="group"
            aria-roledescription="slide"
            aria-label={`${i + 1} of ${slides.length}`}
            aria-hidden={i !== index}
            inert={i !== index}
          >
            {slide}
          </div>
        ))}
      </div>
      <button type="button" className={`${s.sliderArrow} ${s.sliderPrev}`} onClick={() => goTo(index - 1)} aria-label="Previous slide">
        <i className="bi bi-chevron-left" />
      </button>
      <button type="button" className={`${s.sliderArrow} ${s.sliderNext}`} onClick={() => goTo(index + 1)} aria-label="Next slide">
        <i className="bi bi-chevron-right" />
      </button>
      <div className={s.sliderDots}>
        {slides.map((_, i) => (
          <button
            key={i}
            type="button"
            className={i === index ? s.dotActive : undefined}
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
            aria-current={i === index}
          />
        ))}
      </div>
    </div>
  );
}
