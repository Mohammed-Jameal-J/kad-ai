import type { ProductFilters, SortOption } from "@/lib/types";

export const PAGE_SIZE = 12;

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "relevance", label: "Relevance" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "name_asc", label: "Name: A to Z" },
  { value: "name_desc", label: "Name: Z to A" },
  { value: "newest", label: "Newest" },
];

type RawParams = Record<string, string | string[] | undefined>;

const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)?.trim() || undefined;
const flag = (v: string | string[] | undefined) => ["true", "1", "on"].includes(one(v) ?? "") || undefined;
const whole = (v: string | string[] | undefined) => {
  const n = Number(one(v));
  return Number.isInteger(n) && n >= 0 ? n : undefined;
};

/** Turn untrusted URL search params into API filters. The backend validates again. */
export function parseFilters(params: RawParams, category?: string): ProductFilters {
  const sort = one(params.sort) as SortOption | undefined;
  return {
    q: one(params.q)?.slice(0, 100),
    category,
    min_price: whole(params.min_price),
    max_price: whole(params.max_price),
    in_stock: flag(params.in_stock),
    on_sale: flag(params.on_sale),
    featured: flag(params.featured),
    bestseller: flag(params.bestseller),
    sort: SORT_OPTIONS.some((o) => o.value === sort) ? sort : undefined,
    page: Math.max(1, whole(params.page) ?? 1),
    page_size: PAGE_SIZE,
  };
}
