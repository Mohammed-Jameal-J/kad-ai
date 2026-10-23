import type { Metadata } from "next";
import { Suspense } from "react";
import ProductListing, { ListingSkeleton } from "@/components/listing/ProductListing";

export const metadata: Metadata = { title: "All products" };

export default function ProductsPage({ searchParams }: PageProps<"/products">) {
  return (
    <Suspense fallback={<ListingSkeleton />}>
      <ProductListing searchParams={searchParams} />
    </Suspense>
  );
}
