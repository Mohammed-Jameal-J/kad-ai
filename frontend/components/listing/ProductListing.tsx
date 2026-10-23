import Form from "next/form";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ProductGrid } from "@/components/product/ProductCard";
import ProductImage from "@/components/product/ProductImage";
import StatusNote from "@/components/ui/StatusNote";
import { ApiError, getCategories, getProducts, toQuery } from "@/lib/api";
import { rupees } from "@/lib/format";
import type { Category, ProductFilters } from "@/lib/types";
import Breadcrumb from "./Breadcrumb";
import { parseFilters } from "./filters";
import SortSelect from "./SortSelect";
import s from "./listing.module.css";

type Props = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
  categorySlug?: string;
};

function findCategory(tree: Category[], slug: string): { category: Category; parent?: Category } | null {
  for (const parent of tree) {
    if (parent.slug === slug) return { category: parent };
    const child = parent.children.find((c) => c.slug === slug);
    if (child) return { category: child, parent };
  }
  return null;
}

function FilterForm({ basePath, filters, id }: { basePath: string; filters: ProductFilters; id: string }) {
  return (
    <Form action={basePath} className={s.filterForm}>
      {filters.q && <input type="hidden" name="q" value={filters.q} />}
      {filters.sort && <input type="hidden" name="sort" value={filters.sort} />}
      {filters.featured && <input type="hidden" name="featured" value="true" />}
      {filters.bestseller && <input type="hidden" name="bestseller" value="true" />}
      <h3 className={s.sideTitle}>Price (₹)</h3>
      <div className="d-flex gap-2 align-items-center">
        <label className="visually-hidden" htmlFor={`${id}-min`}>Minimum price</label>
        <input id={`${id}-min`} name="min_price" type="number" min={0} placeholder="Min" defaultValue={filters.min_price} className="form-control form-control-sm" />
        <span className="km-muted">to</span>
        <label className="visually-hidden" htmlFor={`${id}-max`}>Maximum price</label>
        <input id={`${id}-max`} name="max_price" type="number" min={0} placeholder="Max" defaultValue={filters.max_price} className="form-control form-control-sm" />
      </div>
      <h3 className={`${s.sideTitle} mt-4`}>Availability</h3>
      <div className="form-check">
        <input className="form-check-input" type="checkbox" name="in_stock" value="true" id={`${id}-stock`} defaultChecked={filters.in_stock} />
        <label className="form-check-label" htmlFor={`${id}-stock`}>In stock only</label>
      </div>
      <div className="form-check">
        <input className="form-check-input" type="checkbox" name="on_sale" value="true" id={`${id}-sale`} defaultChecked={filters.on_sale} />
        <label className="form-check-label" htmlFor={`${id}-sale`}>On sale</label>
      </div>
      <div className="d-flex gap-2 mt-3">
        <button type="submit" className="btn btn-km btn-sm">Apply filters</button>
        <Link href={basePath} className="btn btn-link btn-sm km-muted">Clear</Link>
      </div>
    </Form>
  );
}

export default async function ProductListing({ searchParams, categorySlug }: Props) {
  const params = await searchParams;
  let tree: Category[] = [];
  try {
    tree = await getCategories();
  } catch (error) {
    return <div className="container py-5"><StatusNote error={error} /></div>;
  }

  const found = categorySlug ? findCategory(tree, categorySlug) : null;
  if (categorySlug && !found) notFound();
  const category = found?.category;
  const basePath = category ? `/category/${category.slug}` : "/products";
  const filters = parseFilters(params, category?.slug);

  const title = category?.name ?? (filters.q ? `Results for “${filters.q}”` : "All products");
  const crumbs = [
    { label: "Home", href: "/" },
    ...(found?.parent ? [{ label: found.parent.name, href: `/category/${found.parent.slug}` }] : []),
    ...(category ? [] : [{ label: "Products", href: "/products" }]),
    { label: category?.name ?? (filters.q ? "Search" : "All products") },
  ];

  const [result, bestsellers] = await Promise.allSettled([
    getProducts(filters),
    getProducts({ bestseller: true, page_size: 3, category: category?.slug }),
  ]);
  const page = result.status === "fulfilled" ? result.value : null;
  const error = result.status === "rejected" ? result.reason : null;

  // Keep current filters in pagination links, minus the page number and category (it's in the path).
  const linkFilters = { ...filters, category: undefined, page_size: undefined };
  const pageHref = (n: number) => `${basePath}${toQuery({ ...linkFilters, page: n > 1 ? n : undefined })}`;

  return (
    <>
      <Breadcrumb items={crumbs} />
      <div className="container py-4">
        <div className="row g-4">
          <aside className="col-12 col-lg-3">
            <details className={`${s.mobileFilters} d-lg-none`}>
              <summary>
                <i className="bi bi-funnel me-1" /> Filters
              </summary>
              <FilterForm basePath={basePath} filters={filters} id="m" />
            </details>

            <div className="d-none d-lg-block">
              <section className={s.sideBox}>
                <h2 className={s.sideHeading}>Shop by category</h2>
                <ul className={s.catList}>
                  {tree.map((parent) => (
                    <li key={parent.id}>
                      <Link href={`/category/${parent.slug}`} className={parent.slug === category?.slug ? s.catActive : undefined}>
                        {parent.name} <span>{parent.product_count}</span>
                      </Link>
                      <ul>
                        {parent.children.map((child) => (
                          <li key={child.id}>
                            <Link href={`/category/${child.slug}`} className={child.slug === category?.slug ? s.catActive : undefined}>
                              {child.name} <span>{child.product_count}</span>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </section>

              <section className={s.sideBox}>
                <h2 className={s.sideHeading}>Filter by</h2>
                <FilterForm basePath={basePath} filters={filters} id="d" />
              </section>

              <Link href="/products?on_sale=true" className={s.sidePromo}>
                <Image src="/images/banners/fruit-basket.jpg" alt="" fill sizes="300px" />
                <span>
                  <small>Fresh savings</small>
                  This week&apos;s deals
                </span>
              </Link>

              {bestsellers.status === "fulfilled" && bestsellers.value.items.length > 0 && (
                <section className={s.sideBox}>
                  <h2 className={s.sideHeading}>Bestsellers</h2>
                  {bestsellers.value.items.map((p) => (
                    <Link key={p.id} href={`/product/${p.slug}`} className={s.miniProduct}>
                      <ProductImage src={p.image_path} alt="" size={64} />
                      <span>
                        {p.name}
                        <strong>{rupees(p.price_paise)} / {p.unit}</strong>
                      </span>
                    </Link>
                  ))}
                </section>
              )}
            </div>
          </aside>

          <div className="col-12 col-lg-9">
            <h1 className={s.title}>{title}</h1>
            {category?.description && <p className="km-muted">{category.description}</p>}

            {category && category.children.length > 0 && (
              <>
                <h2 className={s.subTitle}>Subcategories</h2>
                <div className={s.subcats}>
                  {category.children.map((c) => (
                    <Link key={c.id} href={`/category/${c.slug}`} className={s.subcat}>
                      <Image src={c.image_path} alt="" width={96} height={96} />
                      <span>{c.name}</span>
                    </Link>
                  ))}
                </div>
              </>
            )}

            <Form action={basePath} className={s.toolbar}>
              {filters.q && <input type="hidden" name="q" value={filters.q} />}
              {filters.min_price !== undefined && <input type="hidden" name="min_price" value={filters.min_price} />}
              {filters.max_price !== undefined && <input type="hidden" name="max_price" value={filters.max_price} />}
              {filters.in_stock && <input type="hidden" name="in_stock" value="true" />}
              {filters.on_sale && <input type="hidden" name="on_sale" value="true" />}
              {filters.featured && <input type="hidden" name="featured" value="true" />}
              {filters.bestseller && <input type="hidden" name="bestseller" value="true" />}
              <span className="km-note">
                <i className="bi bi-grid-3x3-gap-fill me-2" />
                {page ? `There ${page.total === 1 ? "is 1 product" : `are ${page.total} products`}.` : ""}
              </span>
              <span className="d-flex align-items-center">
                <SortSelect value={filters.sort} />
              </span>
            </Form>

            {error ? (
              <StatusNote error={error instanceof ApiError && error.status === 422 ? new ApiError(422, "Some filters are invalid. Check that the minimum price is not above the maximum.") : error} />
            ) : page && page.items.length ? (
              <>
                <ProductGrid products={page.items} cols={4} />
                <div className={s.pagination}>
                  <span className="km-note">
                    Showing {(page.page - 1) * page.page_size + 1}–{Math.min(page.page * page.page_size, page.total)} of {page.total} item(s)
                  </span>
                  {page.total_pages > 1 && (
                    <nav aria-label="Pagination">
                      <ul className="pagination pagination-sm mb-0">
                        {page.page > 1 && (
                          <li className="page-item">
                            <Link className="page-link" href={pageHref(page.page - 1)} aria-label="Previous page">‹</Link>
                          </li>
                        )}
                        {Array.from({ length: page.total_pages }, (_, i) => i + 1).map((n) => (
                          <li key={n} className={`page-item ${n === page.page ? "active" : ""}`}>
                            <Link className="page-link" href={pageHref(n)} aria-current={n === page.page ? "page" : undefined}>{n}</Link>
                          </li>
                        ))}
                        {page.page < page.total_pages && (
                          <li className="page-item">
                            <Link className="page-link" href={pageHref(page.page + 1)} aria-label="Next page">›</Link>
                          </li>
                        )}
                      </ul>
                    </nav>
                  )}
                </div>
                <p className="km-note mt-2">{page.price_note}</p>
              </>
            ) : (
              <StatusNote empty="No products match these filters. Try clearing some of them." />
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export function ListingSkeleton() {
  return (
    <div className="container py-4" aria-busy="true">
      <div className="km-skeleton mb-4" style={{ height: 28, width: 220 }} />
      <div className="row g-4">
        <div className="col-lg-3 d-none d-lg-block"><div className="km-skeleton" style={{ height: 420 }} /></div>
        <div className="col-12 col-lg-9"><div className="km-skeleton" style={{ height: 600 }} /></div>
      </div>
    </div>
  );
}
