import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import Breadcrumb from "@/components/listing/Breadcrumb";
import s from "./blog.module.css";

export const metadata: Metadata = { title: "Blog" };

// Original, general kitchen tips. No health or medical claims.
const POSTS = [
  {
    id: "store-onions-potatoes",
    date: "20 Oct 2026",
    title: "Storing onions and potatoes the right way",
    image: "/images/products/nashik-red-onion.jpg",
    body: [
      "Onions and potatoes both like a cool, dark, airy place, but they should not share a basket. Onions give off moisture and gases that make potatoes sprout sooner.",
      "Keep potatoes away from sunlight so they don't turn green, and use a basket or paper bag rather than a sealed plastic bag so air can move around them.",
    ],
    link: { href: "/category/everyday-vegetables", label: "Shop everyday vegetables" },
  },
  {
    id: "ripen-mangoes",
    date: "14 Oct 2026",
    title: "How to ripen mangoes at home",
    image: "/images/products/alphonso-mango.jpg",
    body: [
      "Firm mangoes ripen best at room temperature. Wrapping them loosely in newspaper keeps the warmth in and speeds things up a little.",
      "A ripe mango smells sweet near the stem and gives slightly when pressed. Once ripe, move it to the fridge to slow it down for a few days.",
    ],
    link: { href: "/category/tropical-fruits", label: "Shop tropical fruits" },
  },
  {
    id: "fresh-herbs",
    date: "6 Oct 2026",
    title: "Keeping coriander fresh for longer",
    image: "/images/products/coriander-leaves.jpg",
    body: [
      "Trim the stems, stand the bunch in a glass with a little water, and loosely cover the leaves with a bag before putting it in the fridge.",
      "Change the water every couple of days and pick off any yellow leaves. Wash the leaves just before using them, not before storing.",
    ],
    link: { href: "/category/leafy-greens", label: "Shop leafy greens" },
  },
  {
    id: "budget-basket",
    date: "29 Sep 2026",
    title: "Planning a weekly fruit basket on a budget",
    image: "/images/banners/fruit-basket.jpg",
    body: [
      "Start with a few staples that keep well, such as bananas, oranges and apples, then add one or two seasonal fruits for variety.",
      "Our Ask Kad AI assistant can build a basket for a budget you choose. Every price and the total come straight from our database, and nothing is added to your cart until you confirm.",
    ],
    link: { href: "/products?on_sale=true", label: "See this week's deals" },
  },
];

export default function BlogPage() {
  return (
    <>
      <Breadcrumb items={[{ label: "Home", href: "/" }, { label: "Blog" }]} />
      <div className="container py-4">
        <h1 className="h3">From our kitchen</h1>
        <p className="km-muted">Storage tips, seasonal picks and simple ways to shop smarter.</p>
        <div className="row g-4 mt-1">
          {POSTS.map((post) => (
            <div key={post.id} className="col-12 col-md-6">
              <article id={post.id} className={s.post}>
                <div className={s.image}>
                  <Image src={post.image} alt="" fill sizes="(max-width: 768px) 100vw, 50vw" />
                </div>
                <div className={s.body}>
                  <time className="km-note">{post.date}</time>
                  <h2>{post.title}</h2>
                  {post.body.map((p) => <p key={p.slice(0, 20)}>{p}</p>)}
                  <Link href={post.link.href} className="btn btn-km-outline btn-sm">{post.link.label}</Link>
                </div>
              </article>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
