"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useLanguage } from "@/hooks/useLanguage";
import s from "./header.module.css";

export default function AccountLink() {
  const { user } = useAuth();
  const { t } = useLanguage();
  return (
    <Link href={user ? "/account" : "/login"} className={s.account} aria-label={user ? t("account") : t("login")}>
      <i className="bi bi-person-circle" aria-hidden="true" />
      <span className="d-none d-lg-inline">{user ? t("hello", { name: user.name.split(" ")[0] }) : t("login")}</span>
    </Link>
  );
}
