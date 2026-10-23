import Link from "next/link";
import { rupees } from "@/lib/format";
import type { Product } from "@/lib/types";
import AddToCartButton from "./AddToCartButton";
import ProductImage from "./ProductImage";
import s from "./product-card.module.css";

export function Rating({ value }: { value: number }) {
  const full = Math.round(value);
  return (
    <span className={s.rating} aria-label={`Rated ${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <i key={i} className={`bi ${i <= full ? "bi-star-fill" : "bi-star"}`} aria-hidden="true" />
      ))}
    </span>
  );
}

export function Price({ product, large }: { product: Product; large?: boolean }) {
  return (
    <span className={large ? s.priceLarge : s.price}>
      {rupees(product.price_paise)}
      {product.original_price_paise && <del>{rupees(product.original_price_paise)}</del>}
      <small> / {product.unit}</small>
    </span>
  );
}

export default function ProductCard({ product }: { product: Product }) {
  const href = `/product/${product.slug}`;
  return (
    <article className={s.card}>
      {product.discount_percent > 0 && <span className={s.badge}>-{product.discount_percent}%</span>}
      {!product.in_stock && <span className={`${s.badge} ${s.badgeOut}`}>Out of stock</span>}
      <Link href={href} className={s.imageWrap} tabIndex={-1} aria-hidden="true">
        <ProductImage src={product.image_path} alt="" size={300} sizes="(max-width: 768px) 50vw, 240px" className={s.image} />
      </Link>
      <div className={s.body}>
        <span className={s.category}>{product.category.name}</span>
        <h3 className={s.name}>
          <Link href={href}>{product.name}</Link>
        </h3>
        <Rating value={product.rating} />
        <div className={s.footer}>
          <Price product={product} />
          <AddToCartButton productId={product.id} name={product.name} inStock={product.in_stock} />
        </div>
      </div>
    </article>
  );
}

export function ProductGrid({ products, cols = 6 }: { products: Product[]; cols?: number }) {
  return (
    <div className="km-grid" style={{ "--km-cols": cols } as React.CSSProperties}>
      {products.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}

export function ProductGridSkeleton({ count = 6, cols = 6 }: { count?: number; cols?: number }) {
  return (
    <div className="km-grid" style={{ "--km-cols": cols } as React.CSSProperties} aria-busy="true" aria-label="Loading products">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={s.card}>
          <div className={`km-skeleton ${s.imageWrap}`} />
          <div className={s.body}>
            <div className="km-skeleton mb-2" style={{ height: 10, width: "40%" }} />
            <div className="km-skeleton mb-2" style={{ height: 14, width: "85%" }} />
            <div className="km-skeleton" style={{ height: 14, width: "50%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
