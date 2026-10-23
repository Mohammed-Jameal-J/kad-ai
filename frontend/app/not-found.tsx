import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container py-5 text-center">
      <i className="bi bi-basket2 display-4" style={{ color: "var(--km-green)" }} />
      <h1 className="h3 mt-3">We couldn&apos;t find that page</h1>
      <p className="km-muted">The product or category may have been removed or renamed.</p>
      <Link href="/products" className="btn btn-km">Browse all products</Link>
    </div>
  );
}
