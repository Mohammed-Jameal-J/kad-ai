import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import OpenChatButton from "@/components/chat/OpenChatButton";
import { LanguageSelector, T } from "@/hooks/useLanguage";
import { getCategories, settle } from "@/lib/api";
import type { TKey } from "@/lib/i18n";
import AccountLink from "./AccountLink";
import CartButton from "./CartButton";
import CategoryMenu from "./CategoryMenu";
import SearchForm from "./SearchForm";
import s from "./header.module.css";

const NAV: { href: string; label: TKey }[] = [
  { href: "/category/fruits", label: "navFruits" },
  { href: "/category/vegetables", label: "navVegetables" },
  { href: "/category/citrus-fruits", label: "navCitrus" },
  { href: "/category/tropical-fruits", label: "navTropical" },
  { href: "/category/root-vegetables", label: "navRoot" },
  { href: "/category/leafy-greens", label: "navLeafy" },
  { href: "/products", label: "navAll" },
];

/** Brand logo (transparent PNG, 410x160 source). Height is set in CSS; width follows the aspect ratio. */
export function Logo({ small = false }: { small?: boolean }) {
  return (
    <Link href="/" className={small ? s.logoSmall : s.logo}>
      <Image
        src="/brand/kad-ai-logo.png"
        alt="Kad AI logo"
        width={410}
        height={160}
        loading={small ? "lazy" : "eager"}
        fetchPriority={small ? "auto" : "high"}
      />
    </Link>
  );
}

async function CategoryMenuLoader() {
  const result = await settle(getCategories());
  return <CategoryMenu categories={result.ok ? result.data : []} />;
}

export default function Header() {
  return (
    <header className={s.header}>
      <div className={s.announce}>
        <T k="announce" />
        <Link href="/products?on_sale=true" className={s.announceBtn}>
          <T k="shopDeals" />
        </Link>
      </div>

      <div className={s.topbar}>
        <div className="container d-flex justify-content-between align-items-center gap-3">
          <span>
            <i className="bi bi-truck me-1" /> <T k="delivery" />
            <span className="d-none d-md-inline"> · <T k="demoNote" /></span>
          </span>
          <span className="d-flex align-items-center gap-3">
            <LanguageSelector className={s.lang} />
            <Link href="/cart" className="d-none d-sm-inline"><T k="myCart" /></Link>
          </span>
        </div>
      </div>

      <div className="container">
        <div className={s.main}>
          <Logo />
          <SearchForm className={s.search} />
          <OpenChatButton className={s.help}>
            <Image src="/brand/ask-kad-ai-icon.png" alt="" width={192} height={192} className={s.helpIcon} />
            <span>
              <small><T k="helpQuestion" /></small>
              <strong><T k="askAi" /></strong>
            </span>
          </OpenChatButton>
          <AccountLink />
          <CartButton />
        </div>
      </div>

      <nav className={s.nav} aria-label="Main">
        <div className="container d-flex align-items-center gap-3">
          <Suspense fallback={<CategoryMenu categories={[]} />}>
            <CategoryMenuLoader />
          </Suspense>
          <ul className={s.navLinks}>
            {NAV.map((item) => (
              <li key={item.href}>
                <Link href={item.href}><T k={item.label} /></Link>
              </li>
            ))}
          </ul>
          <Link href="/products?on_sale=true" className={s.deals}>
            <i className="bi bi-fire" /> <T k="todaysDeals" />
          </Link>
        </div>
      </nav>
    </header>
  );
}
