import Link from "next/link";
import { Suspense } from "react";
import { ProductGrid, ProductGridSkeleton } from "@/components/product/ProductCard";
import StatusNote from "@/components/ui/StatusNote";
import { getProducts, settle } from "@/lib/api";
import type { ProductFilters } from "@/lib/types";

export function SectionHead({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="km-section-head">
      <span className="km-eyebrow">{eyebrow}</span>
      <h2 className="km-section-title">{title}</h2>
    </div>
  );
}

async function Products({ filters }: { filters: ProductFilters }) {
  const result = await settle(getProducts({ page_size: 6, ...filters }));
  if (!result.ok) return <StatusNote error={result.error} />;
  return result.data.items.length ? <ProductGrid products={result.data.items} /> : <StatusNote />;
}

type Props = { eyebrow: string; title: string; filters: ProductFilters; viewAll: string };

export default function ProductSection({ eyebrow, title, filters, viewAll }: Props) {
  return (
    <section className="km-section">
      <div className="container">
        <SectionHead eyebrow={eyebrow} title={title} />
        <Suspense fallback={<ProductGridSkeleton />}>
          <Products filters={filters} />
        </Suspense>
        <div className="text-center mt-4">
          <Link href={viewAll} className="btn btn-km-outline btn-sm px-4">
            View all
          </Link>
        </div>
      </div>
    </section>
  );
}
