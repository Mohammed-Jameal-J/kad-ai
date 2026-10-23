// Homepage sections that need no API data. Copy is original; reviews and partner names are samples.
import Image from "next/image";
import Link from "next/link";
import { SectionHead } from "./ProductSection";
import s from "./home.module.css";

const SERVICES = [
  { icon: "bi-sunrise", title: "Packed fresh daily", text: "Sorted and packed every morning" },
  { icon: "bi-truck", title: "Next-day delivery", text: "Choose a slot from 8 AM to 8 PM" },
  { icon: "bi-shield-check", title: "Server-verified prices", text: "Totals are always calculated by our backend" },
  { icon: "bi-cpu", title: "Local AI assistant", text: "Runs on your machine with Ollama" },
];

export function ServiceStrip() {
  return (
    <section className="container mt-3">
      <div className={s.services}>
        {SERVICES.map((item) => (
          <div key={item.title} className={s.service}>
            <i className={`bi ${item.icon}`} />
            <div>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const PROMOS = [
  { img: "/images/banners/salad.jpg", eyebrow: "Crunchy and colourful", title: "Fresh vegetables for every salad", href: "/category/vegetables" },
  { img: "/images/categories/tropical-fruits.jpg", eyebrow: "On sale now", title: "Save on farm-fresh fruit", href: "/products?on_sale=true" },
  { img: "/images/banners/juice.jpg", eyebrow: "Juice season", title: "Citrus picks for fresh juice", href: "/category/citrus-fruits" },
];

export function PromoBanners() {
  return (
    <section className="container km-section pb-0">
      <div className="row g-3">
        {PROMOS.map((p) => (
          <div key={p.title} className="col-12 col-md-4">
            <Link href={p.href} className={s.promo}>
              <Image src={p.img} alt="" fill sizes="(max-width: 768px) 100vw, 33vw" />
              <div className={s.promoText}>
                <span>{p.eyebrow}</span>
                <h3>{p.title}</h3>
                <span className={s.fakeBtnLight}>Shop now</span>
              </div>
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}

export function DeliveryBanners() {
  return (
    <section className="container">
      <div className="row g-3">
        <div className="col-12 col-lg-4">
          <Link href="/category/root-vegetables" className={s.promo}>
            <Image src="/images/banners/vegetable-market.jpg" alt="" fill sizes="(max-width: 992px) 100vw, 33vw" />
            <div className={s.promoText}>
              <span>Kitchen staples</span>
              <h3>Root vegetables, big savings</h3>
              <span className={s.fakeBtnLight}>Shop now</span>
            </div>
          </Link>
        </div>
        <div className="col-12 col-lg-8">
          <div className={s.delivery}>
            <i className="bi bi-truck" aria-hidden="true" />
            <div>
              <h3>Delivery next day, 8 AM to 8 PM</h3>
              <p>Order today and pick a delivery slot that suits you. (Demo store: no real deliveries.)</p>
              <Link href="/products" className="btn btn-km btn-sm">
                Start shopping
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const REVIEWS = [
  { name: "Priya S.", text: "The oranges were sweet and the tomatoes lasted the whole week. Packing was neat and plastic-light." },
  { name: "Arun K.", text: "I asked the assistant for fruits under ₹300 and it gave me a basket that actually fit my budget." },
  { name: "Meena R.", text: "Good palak and coriander, fresh enough for chutney the next day. Delivery slot was on time." },
  { name: "Karthik V.", text: "Clear prices per kg and per dozen, so I always know what I am paying for. Easy to reorder." },
];

export function Testimonials() {
  return (
    <section className="km-section" style={{ background: "var(--km-cream)" }}>
      <div className="container">
        <SectionHead eyebrow="Testimonials" title="What shoppers say" />
        <div className="row g-3">
          {REVIEWS.map((r) => (
            <div key={r.name} className="col-12 col-sm-6 col-lg-3">
              <figure className={s.review}>
                <span className={s.reviewStars} aria-label="5 out of 5">
                  {"★★★★★"}
                </span>
                <blockquote>{r.text}</blockquote>
                <figcaption>
                  <span className={s.avatar}>{r.name[0]}</span>
                  {r.name}
                </figcaption>
              </figure>
            </div>
          ))}
        </div>
        <p className="km-note text-center mt-3 mb-0">Sample reviews for this demo store.</p>
      </div>
    </section>
  );
}

const PARTNERS = ["Nilgiri Greens", "Ratnagiri Orchards", "Nashik Fresh", "Himachal Harvest", "Deccan Farms", "Konkan Coast"];

export function PartnerStrip() {
  return (
    <section className="km-section">
      <div className="container">
        <SectionHead eyebrow="Grown with care" title="Our partner farms" />
        <div className={s.partners}>
          {PARTNERS.map((name) => (
            <div key={name} className={s.partner}>
              <i className="bi bi-flower1" /> {name}
            </div>
          ))}
        </div>
        <p className="km-note text-center mt-3 mb-0">Illustrative partner names for this demo.</p>
      </div>
    </section>
  );
}

export function FarmerStory() {
  return (
    <section className="km-section">
      <div className="container">
        <div className="row g-4 align-items-center">
          <div className="col-12 col-lg-6">
            <div className={s.farmerImage}>
              <Image src="/images/banners/farmer.jpg" alt="Farmer sorting freshly harvested potatoes" fill sizes="(max-width: 992px) 100vw, 50vw" />
            </div>
          </div>
          <div className="col-12 col-lg-6">
            <span className="km-eyebrow">About us</span>
            <h2 className={s.farmerTitle}>From the farm to your kitchen, without the long wait</h2>
            <p className="km-muted">
              We buy directly from growers wherever we can, so produce spends less time in storage and more time on your
              plate. Every price you see comes straight from our product database.
            </p>
            <ul className={s.checks}>
              <li><i className="bi bi-check-circle-fill" /> Picked and packed for next-day delivery</li>
              <li><i className="bi bi-check-circle-fill" /> Clear units: per kg, per dozen, per bunch</li>
              <li><i className="bi bi-check-circle-fill" /> Live stock levels straight from our database</li>
            </ul>
            <Link href="/category/vegetables" className="btn btn-km">
              Shop vegetables
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

const TIPS = [
  { img: "/images/products/nashik-red-onion.jpg", title: "Keep onions and potatoes apart", text: "Store both in a cool, dry, airy place, but not together, so each keeps longer." },
  { img: "/images/products/coriander-leaves.jpg", title: "Coriander that lasts", text: "Trim the stems, stand the bunch in a glass of water and loosely cover the leaves in the fridge." },
  { img: "/images/products/alphonso-mango.jpg", title: "Ripening mangoes at home", text: "Leave firm mangoes at room temperature; refrigerate only once they smell sweet and give slightly." },
  { img: "/images/products/robusta-banana.jpg", title: "Slow down banana browning", text: "Hang bananas or keep them away from other fruit; they ripen faster in a closed bag." },
];

export function KitchenTips() {
  return (
    <section className="km-section">
      <div className="container">
        <SectionHead eyebrow="From our kitchen" title="Storage tips" />
        <div className="row g-3">
          {TIPS.map((t) => (
            <div key={t.title} className="col-12 col-sm-6 col-lg-3">
              <article className={s.tip}>
                <div className={s.tipImage}>
                  <Image src={t.img} alt="" fill sizes="(max-width: 576px) 100vw, 25vw" />
                </div>
                <h3>{t.title}</h3>
                <p>{t.text}</p>
              </article>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
