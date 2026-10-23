"use client";

import { useState } from "react";
import ProductCard from "@/components/product/ProductCard";
import type { Product } from "@/lib/types";
import s from "./home.module.css";

type Tab = { id: string; label: string; products: Product[] };

export default function CollectionTabs({ tabs }: { tabs: Tab[] }) {
  const [active, setActive] = useState(tabs[0].id);
  const current = tabs.find((t) => t.id === active) ?? tabs[0];
  return (
    <div>
      <div className={s.tabsHead}>
        <div>
          <span className="km-eyebrow">Our collection</span>
          <h2 className="km-section-title">Shop by categories</h2>
        </div>
        <div className={s.tabs} role="tablist" aria-label="Product collections">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={t.id === active}
              aria-controls="collection-panel"
              className={t.id === active ? s.tabActive : s.tab}
              onClick={() => setActive(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <div id="collection-panel" role="tabpanel" aria-labelledby={`tab-${current.id}`} className="km-grid" style={{ "--km-cols": 4 } as React.CSSProperties}>
        {current.products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}
