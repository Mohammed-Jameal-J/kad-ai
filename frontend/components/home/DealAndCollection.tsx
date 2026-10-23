import Link from "next/link";
import { Suspense } from "react";
import { Price, Rating } from "@/components/product/ProductCard";
import AddToCartButton from "@/components/product/AddToCartButton";
import ProductImage from "@/components/product/ProductImage";
import StatusNote from "@/components/ui/StatusNote";
import { getProducts, settle } from "@/lib/api";
import CollectionTabs from "./CollectionTabs";
import s from "./home.module.css";

async function Content() {
  const result = await settle(
    Promise.all([
      getProducts({ on_sale: true, in_stock: true, page_size: 60 }),
      getProducts({ category: "fruits", in_stock: true, page_size: 4 }),
      getProducts({ category: "vegetables", in_stock: true, page_size: 4 }),
      getProducts({ bestseller: true, page_size: 4, sort: "price_asc" }),
    ]),
  );
  if (!result.ok) return <StatusNote error={result.error} />;
  const [sale, fruits, vegetables, bestsellers] = result.data;
  // Deal of the week = biggest discount currently in the database.
  const deal = [...sale.items].sort((a, b) => b.discount_percent - a.discount_percent)[0];
  return (
      <div className="row g-4">
        <div className="col-12 col-lg-3">
          {deal ? (
            <div className={s.deal}>
              <span className="km-eyebrow">Biggest saving this week</span>
              <h2 className={s.dealTitle}>Deal of the week</h2>
              <Link href={`/product/${deal.slug}`} className={s.dealImage}>
                <ProductImage src={deal.image_path} alt={deal.name} size={260} />
                <span className={s.dealBadge}>-{deal.discount_percent}%</span>
              </Link>
              <h3 className={s.dealName}>
                <Link href={`/product/${deal.slug}`}>{deal.name}</Link>
              </h3>
              <Rating value={deal.rating} />
              <div className="d-flex align-items-end justify-content-between mt-2">
                <Price product={deal} />
                <AddToCartButton productId={deal.id} name={deal.name} inStock={deal.in_stock} />
              </div>
              <p className="km-note mt-2 mb-0">{deal.stock_quantity} in stock · Offer valid while stock lasts</p>
            </div>
          ) : (
            <StatusNote empty="No deals right now." />
          )}
        </div>
        <div className="col-12 col-lg-9">
          <CollectionTabs
            tabs={[
              { id: "fruits", label: "Fruits", products: fruits.items },
              { id: "vegetables", label: "Vegetables", products: vegetables.items },
              { id: "value", label: "Best value", products: bestsellers.items },
            ]}
          />
        </div>
      </div>
  );
}

export default function DealAndCollection() {
  return (
    <section className="km-section">
      <div className="container">
        <Suspense fallback={<div className="km-skeleton" style={{ height: 420 }} />}>
          <Content />
        </Suspense>
      </div>
    </section>
  );
}
