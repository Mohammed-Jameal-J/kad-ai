"use client";

import { useCallback, useEffect, useSyncExternalStore } from "react";
import { isLang, LANGUAGES, translate, type Lang, type TKey } from "@/lib/i18n";

const STORAGE_KEY = "kadai-lang";
const CHANGE_EVENT = "kadai:lang";
let memoryLang: Lang = "en"; // used when localStorage is blocked (private mode)

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange); // other tabs
  window.addEventListener(CHANGE_EVENT, onChange); // this tab
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}

function readLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return isLang(stored) ? stored : memoryLang;
  } catch {
    return memoryLang;
  }
}

/** Current UI language. The server always renders English; the browser switches after hydration. */
export function useLanguage() {
  const lang = useSyncExternalStore(subscribe, readLang, () => "en" as Lang);

  const setLang = useCallback((next: Lang) => {
    memoryLang = next;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {}
    window.dispatchEvent(new Event(CHANGE_EVENT));
  }, []);

  const t = useCallback((key: TKey, vars?: Record<string, string>) => translate(lang, key, vars), [lang]);
  return { lang, setLang, t };
}

/** Translated text for use inside Server Components: <T k="cart" />. */
export function T({ k, vars }: { k: TKey; vars?: Record<string, string> }) {
  const { t } = useLanguage();
  return t(k, vars);
}

export function LanguageSelector({ className }: { className?: string }) {
  const { lang, setLang, t } = useLanguage();

  useEffect(() => {
    document.documentElement.lang = lang; // screen readers and fonts pick the right language
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"; // Arabic reads right to left (styles/rtl.css)
  }, [lang]);

  return (
    <label className={className}>
      <i className="bi bi-translate" aria-hidden="true" />
      <span className="visually-hidden">{t("language")}</span>
      <select value={lang} onChange={(e) => setLang(e.target.value as Lang)} aria-label={t("language")}>
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code} lang={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}
