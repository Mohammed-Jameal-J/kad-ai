import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import StatusNote from "@/components/ui/StatusNote";
import { getCategories, settle } from "@/lib/api";
import { SectionHead } from "./ProductSection";
import s from "./home.module.css";

async function Cards() {
  const result = await settle(getCategories());
  if (!result.ok) return <StatusNote error={result.error} />;
  const subcategories = result.data.flatMap((c) => c.children);
  return (
    <div className={s.catRow}>
      {subcategories.map((c) => (
        <Link key={c.id} href={`/category/${c.slug}`} className={s.catCard}>
          <span className={s.catImage}>
            <Image src={c.image_path} alt="" width={120} height={120} />
          </span>
          <strong>{c.name}</strong>
          <small>{c.product_count} items</small>
        </Link>
      ))}
    </div>
  );
}

export default function CategoryCards() {
  return (
    <section className="km-section pb-2">
      <div className="container">
        <SectionHead eyebrow="Browse the aisles" title="Shop by category" />
        <Suspense fallback={<div className="km-skeleton" style={{ height: 170 }} />}>
          <Cards />
        </Suspense>
      </div>
    </section>
  );
}
