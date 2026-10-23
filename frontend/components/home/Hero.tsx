import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import { getProduct } from "@/lib/api";
import { rupees } from "@/lib/format";
import s from "./home.module.css";

const HERO_PRODUCT = "nagpur-orange";

async function HeroPrice() {
  const product = await getProduct(HERO_PRODUCT).catch(() => null);
  if (!product) return null;
  return (
    <p className={s.heroPrice}>
      <span>Starting at</span>
      {rupees(product.price_paise)} <small>/ {product.unit}</small>
    </p>
  );
}

export default function Hero() {
  return (
    <section className="container pt-4">
      <div className="row g-3">
        <div className="col-12 col-lg-8">
          <div className={s.hero}>
            <div className={s.heroText}>
              <span className="km-eyebrow">Citrus season is here</span>
              <h1>Fresh Nagpur oranges, sweet and tangy</h1>
              <Suspense fallback={<div className="km-skeleton my-3" style={{ height: 52, width: 160 }} />}>
                <HeroPrice />
              </Suspense>
              <Link href={`/product/${HERO_PRODUCT}`} className="btn btn-km">
                Shop now <i className="bi bi-arrow-right ms-1" />
              </Link>
            </div>
            <div className={s.heroImage}>
              <Image src="/images/products/nagpur-orange.jpg" alt="Nagpur oranges with leaves" fill sizes="(max-width: 992px) 60vw, 420px" loading="eager" fetchPriority="high" />
            </div>
          </div>
        </div>
        <div className="col-12 col-lg-4 d-flex flex-column gap-3">
          <Link href="/category/fruits" className={`${s.sideBanner} ${s.sideCream}`}>
            <div>
              <span className="km-eyebrow">Fruit bowl favourites</span>
              <h2>Sweet, juicy fruit every day</h2>
              <span className={s.fakeBtn}>Shop fruits</span>
            </div>
            <div className={s.sideImage}>
              <Image src="/images/banners/fruit-basket.jpg" alt="Basket of apples, pears, grapes and bananas" fill sizes="160px" />
            </div>
          </Link>
          <Link href="/category/vegetables" className={`${s.sideBanner} ${s.sideGreen}`}>
            <div>
              <span className="km-eyebrow">Market fresh</span>
              <h2>Vegetables for everyday cooking</h2>
              <span className={s.fakeBtn}>Shop vegetables</span>
            </div>
            <div className={s.sideImage}>
              <Image src="/images/categories/everyday-vegetables.jpg" alt="Potatoes and tomatoes in baskets" fill sizes="160px" />
            </div>
          </Link>
        </div>
      </div>
    </section>
  );
}
