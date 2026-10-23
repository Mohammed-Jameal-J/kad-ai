import CategoryCards from "@/components/home/CategoryCards";
import DealAndCollection from "@/components/home/DealAndCollection";
import Hero from "@/components/home/Hero";
import Newsletter from "@/components/home/Newsletter";
import ProductSection from "@/components/home/ProductSection";
import {
  DeliveryBanners,
  FarmerStory,
  KitchenTips,
  PartnerStrip,
  PromoBanners,
  ServiceStrip,
  Testimonials,
} from "@/components/home/StaticSections";

// Static parts render instantly; each product section streams in from FastAPI inside its own <Suspense>.
export default function HomePage() {
  return (
    <>
      <Hero />
      <ServiceStrip />
      <CategoryCards />
      <PromoBanners />
      <ProductSection eyebrow="Fresh in" title="New products" filters={{ sort: "newest" }} viewAll="/products?sort=newest" />
      <ProductSection eyebrow="Picked for you" title="Featured products" filters={{ featured: true }} viewAll="/products?featured=true" />
      <DeliveryBanners />
      <DealAndCollection />
      <Testimonials />
      <ProductSection eyebrow="Customer favourites" title="Bestseller products" filters={{ bestseller: true }} viewAll="/products?bestseller=true" />
      <PartnerStrip />
      <FarmerStory />
      <KitchenTips />
      <Newsletter />
    </>
  );
}
