import Link from "next/link";
import { T } from "@/hooks/useLanguage";
import type { TKey } from "@/lib/i18n";
import { Logo } from "./Header";
import s from "./footer.module.css";

const COLUMNS: { title: TKey; links: [TKey, string][] }[] = [
  {
    title: "footerShop",
    links: [
      ["allProducts", "/products"],
      ["todaysDeals", "/products?on_sale=true"],
      ["bestsellers", "/products?bestseller=true"],
      ["featured", "/products?featured=true"],
    ],
  },
  {
    title: "footerCategories",
    links: [
      ["navFruits", "/category/fruits"],
      ["navVegetables", "/category/vegetables"],
      ["citrusFruits", "/category/citrus-fruits"],
      ["leafyGreens", "/category/leafy-greens"],
    ],
  },
  {
    title: "footerCompany",
    links: [
      ["contact", "/contact"],
      ["blog", "/blog"],
      ["account", "/account"],
      ["register", "/register"],
      ["myCart", "/cart"],
    ],
  },
];

export default function Footer() {
  return (
    <footer className={s.footer}>
      <div className="container">
        <div className="row g-4">
          <div className="col-12 col-lg-4">
            <p className={s.about}><T k="footerAbout" /></p>
            <p className={s.contact}>
              <i className="bi bi-geo-alt" /> <T k="footerAddress" />
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title} className="col-6 col-md-4 col-lg-2">
              <h3 className={s.heading}><T k={col.title} /></h3>
              <ul className={s.links}>
                {col.links.map(([label, href]) => (
                  <li key={href}>
                    <Link href={href}><T k={label} /></Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <div className={s.bottom}>
        <div className="container d-flex flex-wrap align-items-center justify-content-between gap-2">
          <span className="d-flex align-items-center gap-3">
            <Logo small />
            <T k="footerRights" />
          </span>
          <span><T k="priceNote" /></span>
        </div>
      </div>
    </footer>
  );
}
