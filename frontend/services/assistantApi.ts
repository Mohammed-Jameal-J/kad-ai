import type { Lang } from "@/lib/i18n";
import type { ChatResponse, ChatTurn } from "@/lib/types";

// Local models can take over a minute (load + swap). Slightly above the backend's Ollama timeout.
const TIMEOUT_MS = 200_000;

export async function sendChat(message: string, history: ChatTurn[], lang: Lang = "en"): Promise<ChatResponse> {
  let res: Response;
  try {
    res = await fetch("/api/assistant/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history, lang }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (e) {
    throw new Error(
      e instanceof DOMException && e.name === "TimeoutError"
        ? "The assistant took too long to answer. Please try again."
        : "Couldn't reach the assistant. Is the backend running?",
    );
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === "string" ? body.detail : "The assistant couldn't handle that message.");
  }
  return body as ChatResponse;
}
