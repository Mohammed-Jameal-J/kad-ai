import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";
import { getProduct } from "@/lib/api";
import { rupees } from "@/lib/format";
import AutoSlider from "./AutoSlider";
import s from "./home.module.css";

// Each slide links to a real product; its price is read live from the API.
const SLIDES = [
  { slug: "nagpur-orange", eyebrow: "Citrus season is here", title: "Fresh Nagpur oranges, sweet and tangy", alt: "Nagpur oranges with leaves", tone: "" },
  { slug: "alphonso-mango", eyebrow: "King of fruits", title: "Alphonso mangoes, rich and golden", alt: "Ripe Alphonso mangoes", tone: s.slideGold },
  { slug: "ooty-carrot", eyebrow: "Straight from the hills", title: "Crunchy Ooty carrots for every curry", alt: "Fresh orange carrots", tone: s.slideGreen },
  { slug: "palak-spinach", eyebrow: "Leafy and green", title: "Tender palak for dal, saag and smoothies", alt: "Bunch of fresh spinach leaves", tone: s.slideGreen },
];

async function HeroPrice({ slug }: { slug: string }) {
  const product = await getProduct(slug).catch(() => null);
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
          <AutoSlider label="Seasonal picks" slideClassName={s.slide}>
            {SLIDES.map((slide, i) => (
              <div key={slide.slug} className={`${s.hero} ${slide.tone}`}>
                <div className={s.heroText}>
                  <span className="km-eyebrow">{slide.eyebrow}</span>
                  {i === 0 ? <h1>{slide.title}</h1> : <h2 className={s.heroTitle}>{slide.title}</h2>}
                  <Suspense fallback={<div className="km-skeleton my-3" style={{ height: 52, width: 160 }} />}>
                    <HeroPrice slug={slide.slug} />
                  </Suspense>
                  <Link href={`/product/${slide.slug}`} className="btn btn-km">
                    Shop now <i className="bi bi-arrow-right ms-1" />
                  </Link>
                </div>
                <div className={s.heroImage}>
                  <Image
                    src={`/images/products/${slide.slug}.jpg`} alt={slide.alt} fill sizes="(max-width: 768px) 40vw, 340px"
                    {...(i === 0 ? { loading: "eager", fetchPriority: "high" } : {})}
                  />
                </div>
              </div>
            ))}
          </AutoSlider>
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
