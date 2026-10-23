import Link from "next/link";

export default function Breadcrumb({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <div className="km-breadcrumb-band">
      <nav className="container" aria-label="Breadcrumb">
        <ol className="breadcrumb">
          {items.map((item, i) =>
            item.href && i < items.length - 1 ? (
              <li key={item.label} className="breadcrumb-item">
                <Link href={item.href}>{item.label}</Link>
              </li>
            ) : (
              <li key={item.label} className="breadcrumb-item active" aria-current="page">
                {item.label}
              </li>
            ),
          )}
        </ol>
      </nav>
    </div>
  );
}
