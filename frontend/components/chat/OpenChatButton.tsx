"use client";

import { OPEN_CHAT_EVENT } from "./ChatWidget";

/** Opens the floating chat widget from anywhere (e.g. the header). */
export default function OpenChatButton({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <button type="button" className={className} onClick={() => window.dispatchEvent(new Event(OPEN_CHAT_EVENT))}>
      {children}
    </button>
  );
}
