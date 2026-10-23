import { Suspense } from "react";
import ProductListing, { ListingSkeleton } from "@/components/listing/ProductListing";

async function CategoryListing({ params, searchParams }: PageProps<"/category/[slug]">) {
  const { slug } = await params;
  return <ProductListing searchParams={searchParams} categorySlug={slug} />;
}

export default function CategoryPage(props: PageProps<"/category/[slug]">) {
  return (
    <Suspense fallback={<ListingSkeleton />}>
      <CategoryListing {...props} />
    </Suspense>
  );
}
