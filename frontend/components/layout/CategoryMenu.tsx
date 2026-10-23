"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import type { Category } from "@/lib/types";
import s from "./header.module.css";

export default function CategoryMenu({ categories }: { categories: Category[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { t } = useLanguage();

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === "Escape" : !ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div className={s.catMenu} ref={ref}>
      <button
        type="button"
        className={s.catButton}
        aria-expanded={open}
        aria-controls="category-menu"
        disabled={!categories.length}
        onClick={() => setOpen((v) => !v)}
      >
        <i className="bi bi-grid" /> <span className="d-none d-sm-inline">{t("shopByCategories")}</span>
        <i className="bi bi-chevron-down small" />
      </button>
      {open && (
        <div id="category-menu" className={s.catPanel}>
          {categories.map((parent) => (
            <div key={parent.id}>
              <Link href={`/category/${parent.slug}`} className={s.catParent} onClick={() => setOpen(false)}>
                {parent.name} <span>{parent.product_count}</span>
              </Link>
              {parent.children.map((child) => (
                <Link key={child.id} href={`/category/${child.slug}`} className={s.catChild} onClick={() => setOpen(false)}>
                  {child.name} <span>{child.product_count}</span>
                </Link>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
