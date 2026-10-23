"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import ProductImage from "@/components/product/ProductImage";
import { useCart } from "@/hooks/useCart";
import { useLanguage } from "@/hooks/useLanguage";
import { rupees } from "@/lib/format";
import type { ChatResponse, ChatTurn } from "@/lib/types";
import { sendChat } from "@/services/assistantApi";
import s from "./chat.module.css";

export const OPEN_CHAT_EVENT = "kadai:open-chat";
export const ASK_LOGO_ALT = "Ask Kad AI – AI shopping assistant with human support";

type ActionState = "pending" | "done" | "cancelled" | "failed";
type Message = {
  id: string;
  role: ChatTurn["role"];
  text: string;
  data?: ChatResponse;
  error?: boolean;
  retry?: string; // the user message to resend after an error
  action?: ActionState;
};

const STORAGE_KEY = "kadai-chat";
const MAX_CARDS = 4;
const SUGGESTIONS = [
  "Show me fruits below ₹200",
  "Compare apples and oranges",
  "Suggest fruits for my family within ₹500",
  "Add two kilograms of apples to my cart",
  "What vegetables do you have in stock?",
];

function loadMessages(): Message[] {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return []; // server render, private mode or corrupt data: start fresh
  }
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  // Safe to read storage in the initializer: messages only render while the panel is open,
  // and the panel is closed on the server render, so hydration output matches.
  const [messages, setMessages] = useState<Message[]>(loadMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { add, addMany } = useCart();
  const { t, lang } = useLanguage();

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-30)));
    } catch {}
  }, [messages]);

  useEffect(() => {
    const openChat = () => setOpen(true);
    window.addEventListener(OPEN_CHAT_EVENT, openChat);
    return () => window.removeEventListener(OPEN_CHAT_EVENT, openChat);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading, open]);

  useEffect(() => {
    if (!loading) return;
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [loading]);

  async function send(text: string) {
    const message = text.trim().slice(0, 500);
    if (!message || loading) return;
    const history: ChatTurn[] = messages
      .filter((m) => !m.error)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.text.slice(0, 1000) }));
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: message }]);
    setInput("");
    setElapsed(0);
    setLoading(true);
    try {
      const data = await sendChat(message, history, lang);
      setMessages((m) => [
        ...m,
        { id: crypto.randomUUID(), role: "assistant", text: data.reply, data, action: data.pending_action ? "pending" : undefined },
      ]);
    } catch (e) {
      const text = e instanceof Error ? e.message : "Something went wrong.";
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", text, error: true, retry: message }]);
    } finally {
      setLoading(false);
    }
  }

  function setAction(id: string, action: ActionState) {
    setMessages((m) => m.map((msg) => (msg.id === id ? { ...msg, action } : msg)));
  }

  async function confirm(msg: Message) {
    if (!msg.data?.pending_action) return;
    const ok = await addMany(msg.data.pending_action.items);
    setAction(msg.id, ok ? "done" : "failed");
  }

  if (!open) {
    return (
      <button type="button" className={s.launcher} onClick={() => setOpen(true)} aria-label={t("chatOpen")}>
        <Image src="/brand/ask-kad-ai-icon.png" alt="" width={192} height={192} className={s.launcherIcon} />
        <span className={s.launcherLabel} aria-hidden="true">Ask Kad AI</span>
      </button>
    );
  }

  return (
    <section className={s.panel} role="dialog" aria-label="Ask Kad AI shopping assistant" onKeyDown={(e) => e.key === "Escape" && setOpen(false)}>
      <header className={s.head}>
        <div className={s.headBrand}>
          <Image src="/brand/ask-kad-ai-logo.png" alt={ASK_LOGO_ALT} width={527} height={160} className={s.headLogo} />
          <small>{t("chatSubtitle")}</small>
        </div>
        <button type="button" className={s.iconBtn} onClick={() => setMessages([])} aria-label={t("chatNewChat")} title={t("chatNewChat")} disabled={loading}>
          <i className="bi bi-arrow-counterclockwise" />
        </button>
        <button type="button" className={s.iconBtn} onClick={() => setOpen(false)} aria-label={t("chatClose")} title={t("chatClose")}>
          <i className="bi bi-x-lg" />
        </button>
      </header>

      <div className={s.messages} ref={listRef} aria-live="polite">
        <div className={s.bot}>
          <p className={s.bubble}>{t("chatWelcome")}</p>
          {messages.length === 0 && (
            <div className={s.chips}>
              {SUGGESTIONS.map((q) => (
                <button key={q} type="button" onClick={() => send(q)}>{q}</button>
              ))}
            </div>
          )}
        </div>

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className={s.user}><p className={s.bubble}>{m.text}</p></div>
          ) : (
            <div key={m.id} className={s.bot}>
              <p className={`${s.bubble} ${m.error ? s.errorBubble : ""}`}>{m.text}</p>
              {m.error && m.retry && (
                <button type="button" className={s.linkBtn} onClick={() => send(m.retry!)} disabled={loading}>
                  <i className="bi bi-arrow-repeat me-1" />{t("chatTryAgain")}
                </button>
              )}
              {m.data && <Extras msg={m} onAdd={add} onConfirm={() => confirm(m)} onCancel={() => setAction(m.id, "cancelled")} />}
            </div>
          ),
        )}

        {loading && (
          <div className={s.bot}>
            <p className={`${s.bubble} ${s.typing}`}>
              <span className={s.dots}><i /><i /><i /></span>
              {t("chatThinking")}{elapsed >= 4 ? ` · ${elapsed}s (${t("chatSlow")})` : "…"}
            </p>
          </div>
        )}
      </div>

      <form className={s.inputRow} onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <label htmlFor="chat-input" className="visually-hidden">{t("chatMessage")}</label>
        <input id="chat-input" ref={inputRef} value={input} maxLength={500} onChange={(e) => setInput(e.target.value)} placeholder={t("chatPlaceholder")} autoComplete="off" />
        <button type="submit" disabled={loading || !input.trim()} aria-label={t("chatSend")}><i className="bi bi-send-fill" /></button>
      </form>
      <p className={s.disclaimer}>
        {t("chatDisclaimer")}{" "}
        <Link href="/contact" onClick={() => setOpen(false)}>{t("chatHuman")}</Link>
      </p>
    </section>
  );
}

type ExtrasProps = {
  msg: Message;
  onAdd: (productId: number, quantity: number, name: string) => Promise<boolean>;
  onConfirm: () => void;
  onCancel: () => void;
};

function Extras({ msg, onAdd, onConfirm, onCancel }: ExtrasProps) {
  const { t } = useLanguage();
  const data = msg.data!;
  const notes = data.notes.filter((n) => !data.reply.includes(n));
  const action = data.pending_action;
  return (
    <>
      {data.products.length > 0 && (
        <ul className={s.cards}>
          {data.products.slice(0, MAX_CARDS).map((p) => (
            <li key={p.id} className={s.card}>
              <ProductImage src={p.image_path} alt="" size={52} className={s.cardImg} />
              <div className={s.cardBody}>
                <Link href={`/product/${p.slug}`}>{p.name}</Link>
                <span>{rupees(p.price_paise)} / {p.unit}</span>
              </div>
              <button type="button" className={s.addBtn} disabled={!p.in_stock} onClick={() => onAdd(p.id, 1, p.name)} aria-label={p.in_stock ? `Add ${p.name} to cart` : `${p.name} is out of stock`}>
                {p.in_stock ? <i className="bi bi-cart-plus" /> : "Out"}
              </button>
            </li>
          ))}
          {data.products.length > MAX_CARDS && <li className={s.more}>+{data.products.length - MAX_CARDS} more listed above</li>}
        </ul>
      )}

      {action && (
        <div className={s.action}>
          <strong>{action.summary}</strong>
          <span>Total {rupees(action.total_paise)} · calculated by our server</span>
          {msg.action === "pending" || msg.action === "failed" ? (
            <div className="d-flex gap-2 mt-2">
              <button type="button" className="btn btn-km btn-sm" onClick={onConfirm}>
                {msg.action === "failed" ? t("chatTryAgain") : t("chatConfirm")}
              </button>
              <button type="button" className="btn btn-km-outline btn-sm" onClick={onCancel}>{t("chatCancel")}</button>
            </div>
          ) : (
            <span className={msg.action === "done" ? s.done : s.cancelled}>
              {msg.action === "done" ? <><i className="bi bi-check-circle-fill me-1" />{t("chatAdded")}</> : t("chatCancelled")}
            </span>
          )}
        </div>
      )}

      {data.sources?.length ? (
        <ol className={s.sources}>
          {data.sources
            .filter((src) => src.url.startsWith("https://")) // backend checks too; never render other schemes
            .map((src) => (
              <li key={src.url}>
                <a href={src.url} target="_blank" rel="noopener noreferrer nofollow">
                  {src.title} <i className="bi bi-box-arrow-up-right" aria-hidden="true" />
                </a>
              </li>
            ))}
        </ol>
      ) : null}
      {notes.length > 0 && <ul className={s.notes}>{notes.map((n) => <li key={n}>{n}</li>)}</ul>}
    </>
  );
}
