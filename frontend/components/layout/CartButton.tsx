"use client";

import Link from "next/link";
import { useCart } from "@/hooks/useCart";
import { useLanguage } from "@/hooks/useLanguage";
import s from "./header.module.css";

export default function CartButton() {
  const { count } = useCart();
  const { t } = useLanguage();
  return (
    <Link href="/cart" className={s.cart} aria-label={`${t("cart")}, ${count}`}>
      <i className="bi bi-bag" />
      <span className={s.cartBadge}>{count}</span>
      <span className="d-none d-lg-inline">{t("cart")}</span>
    </Link>
  );
}
