"use client";

import Form from "next/form";
import { useLanguage } from "@/hooks/useLanguage";

export default function SearchForm({ className }: { className?: string }) {
  const { t } = useLanguage();
  return (
    <Form action="/products" role="search" className={className}>
      <label htmlFor="site-search" className="visually-hidden">{t("searchLabel")}</label>
      <input id="site-search" name="q" type="search" placeholder={t("searchPlaceholder")} maxLength={100} />
      <button type="submit" aria-label={t("searchLabel")}>
        <i className="bi bi-search" />
      </button>
    </Form>
  );
}
