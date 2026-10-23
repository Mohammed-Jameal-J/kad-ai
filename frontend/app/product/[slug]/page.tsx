import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import Breadcrumb from "@/components/listing/Breadcrumb";
import ProductCard, { Price, Rating } from "@/components/product/ProductCard";
import ProductImage from "@/components/product/ProductImage";
import QuantityAddToCart from "@/components/product/QuantityAddToCart";
import { getProduct, getProducts } from "@/lib/api";
import type { Nutrition, ProductDetail } from "@/lib/types";
import s from "./product.module.css";

const NUTRIENTS: [keyof Nutrition, string, string][] = [
  ["energy_kcal", "Energy", "kcal"],
  ["carbohydrate_g", "Carbohydrate", "g"],
  ["sugars_g", "Sugars", "g"],
  ["fiber_g", "Fibre", "g"],
  ["protein_g", "Protein", "g"],
  ["fat_g", "Fat", "g"],
  ["vitamin_c_mg", "Vitamin C", "mg"],
  ["potassium_mg", "Potassium", "mg"],
];

function NutritionPanel({ product }: { product: ProductDetail }) {
  const n = product.nutrition;
  if (!n) {
    return (
      <div className={s.panel}>
        <h2>Nutrition</h2>
        <p className="km-muted mb-0">
          Verified nutrition data for {product.name} is not available yet. We only show values copied from a cited
          public source, so we would rather show nothing than guess.
        </p>
      </div>
    );
  }
  return (
    <div className={s.panel}>
      <h2>Nutrition per {n.serving_size_g} g</h2>
      <table className="table table-sm mb-2">
        <tbody>
          {NUTRIENTS.filter(([key]) => n[key] !== null).map(([key, label, unit]) => (
            <tr key={key}>
              <th scope="row" className="fw-normal">{label}</th>
              <td className="text-end">{n[key]} {unit}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="km-note mb-0">
        Source: {n.source_url ? <a href={n.source_url} target="_blank" rel="noreferrer">{n.source_name}</a> : n.source_name}
        {" "}({n.food_description}). General information, not medical advice.
      </p>
    </div>
  );
}

async function Related({ category, exclude }: { category: string; exclude: number }) {
  const page = await getProducts({ category, page_size: 5 }).catch(() => null);
  const items = page?.items.filter((p) => p.id !== exclude).slice(0, 4) ?? [];
  if (!items.length) return null;
  return (
    <section className="km-section pb-0">
      <h2 className="km-section-title mb-3">You may also like</h2>
      <div className="km-grid" style={{ "--km-cols": 4 } as React.CSSProperties}>
        {items.map((p) => <ProductCard key={p.id} product={p} />)}
      </div>
    </section>
  );
}

async function ProductContent({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  return (
    <>
      <Breadcrumb
        items={[
          { label: "Home", href: "/" },
          { label: product.category.name, href: `/category/${product.category.slug}` },
          { label: product.name },
        ]}
      />
      <div className="container py-4">
        <div className="row g-4 g-lg-5">
          <div className="col-12 col-md-6 col-lg-5">
            <div className={s.imageBox}>
              {product.discount_percent > 0 && <span className={s.badge}>-{product.discount_percent}%</span>}
              <ProductImage src={product.image_path} alt={product.name} size={600} sizes="(max-width: 768px) 100vw, 500px" eager className={s.image} />
            </div>
          </div>
          <div className="col-12 col-md-6 col-lg-7">
            <Link href={`/category/${product.category.slug}`} className={s.category}>{product.category.name}</Link>
            <h1 className={s.name}>{product.name}</h1>
            <div className="d-flex align-items-center gap-2 mb-3">
              <Rating value={product.rating} />
              <span className="km-note">{product.rating.toFixed(1)} demo rating</span>
            </div>
            <Price product={product} large />
            <p className={product.in_stock ? s.inStock : s.outStock}>
              <i className={`bi ${product.in_stock ? "bi-check-circle-fill" : "bi-x-circle-fill"} me-1`} />
              {product.in_stock ? `In stock: ${product.stock_quantity} × ${product.unit}` : "Out of stock"}
            </p>
            <p className={s.description}>{product.description}</p>
            <QuantityAddToCart productId={product.id} name={product.name} unit={product.unit} stock={product.stock_quantity} />
            <p className="km-note mt-3">{product.price_note} Final totals are calculated by the server.</p>
            <NutritionPanel product={product} />
          </div>
        </div>
        <Suspense fallback={null}>
          <Related category={product.category.slug} exclude={product.id} />
        </Suspense>
      </div>
    </>
  );
}

export default function ProductPage({ params }: PageProps<"/product/[slug]">) {
  return (
    <Suspense fallback={<div className="container py-5"><div className="km-skeleton" style={{ height: 480 }} /></div>}>
      <ProductContent params={params} />
    </Suspense>
  );
}
