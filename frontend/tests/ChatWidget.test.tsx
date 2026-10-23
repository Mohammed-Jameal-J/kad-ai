import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ChatWidget from "@/components/chat/ChatWidget";
import { CartProvider } from "@/hooks/useCart";
import type { ChatResponse } from "@/lib/types";

vi.mock("next/image", () => ({
  // eslint-disable-next-line @next/next/no-img-element
  default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));

const EMPTY_CART = { cart_id: null, items: [], item_count: 0, subtotal_paise: 0, currency: "INR", price_note: "" };

function reply(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    reply: "Please confirm: add 2 x kg Shimla Apple (₹360) to your cart? Nothing has been added yet.",
    intent: "add_to_cart", products: [], basket: null, nutrition: [], notes: [],
    pending_action: { type: "add_to_cart", items: [{ product_id: 1, quantity: 2 }], total_paise: 36000, summary: "Add 2 x kg Shimla Apple (₹360)" },
    parser: "qwen3:4b", writer: "template", duration_ms: 1200, price_note: "", ...overrides,
  };
}

type Call = { url: string; method: string; body: unknown };
let calls: Call[];

function mockFetch(chat: () => Response) {
  calls = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (url === "/api/assistant/chat") return chat();
    if (url === "/api/cart/items" && method === "POST") {
      return Response.json({ ...EMPTY_CART, cart_id: "c1", item_count: 2, subtotal_paise: 36000 }, { status: 201 });
    }
    return Response.json(EMPTY_CART);
  }));
}

const cartWrites = () => calls.filter((c) => c.url.startsWith("/api/cart/items"));

async function ask(text: string) {
  render(<CartProvider><ChatWidget /></CartProvider>);
  fireEvent.click(screen.getByRole("button", { name: /open the kad ai/i }));
  fireEvent.change(screen.getByLabelText("Message"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));
}

beforeEach(() => {
  sessionStorage.clear();
  Element.prototype.scrollTo = () => {}; // not implemented in jsdom
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ChatWidget", () => {
  it("never changes the cart until the customer confirms", async () => {
    mockFetch(() => Response.json(reply()));
    await ask("Add two kilograms of apples to my cart");

    await screen.findByText("Add 2 x kg Shimla Apple (₹360)");
    expect(calls.find((c) => c.url === "/api/assistant/chat")?.body).toMatchObject({ message: "Add two kilograms of apples to my cart", history: [], lang: "en" });
    expect(cartWrites()).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Confirm, add to cart" }));
    await screen.findByText("Added to your cart", { selector: "span" });
    expect(cartWrites()).toEqual([{ url: "/api/cart/items", method: "POST", body: { product_id: 1, quantity: 2 } }]);
  });

  it("cancel leaves the cart untouched", async () => {
    mockFetch(() => Response.json(reply()));
    await ask("add apples");
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
    expect(screen.getByText("Cancelled, nothing was added")).toBeTruthy();
    expect(cartWrites()).toHaveLength(0);
  });

  it("shows the server error and lets the customer retry", async () => {
    mockFetch(() => Response.json({ detail: "Ollama is not running." }, { status: 503 }));
    await ask("hello");
    await screen.findByText("Ollama is not running.");
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    await waitFor(() => expect(calls.filter((c) => c.url === "/api/assistant/chat")).toHaveLength(2));
  });

  it("renders reply text as text, never as HTML", async () => {
    mockFetch(() => Response.json(reply({ reply: '<img src=x onerror="alert(1)">hi', pending_action: null })));
    const { container } = render(<div />);
    await ask("test");
    await screen.findByText('<img src=x onerror="alert(1)">hi');
    expect(container.ownerDocument.querySelector('img[src="x"]')).toBeNull();
  });

  it("remembers the conversation and sends it as history", async () => {
    mockFetch(() => Response.json(reply({ reply: "We have Alphonso Mango.", pending_action: null })));
    await ask("find mangoes");
    await screen.findByText("We have Alphonso Mango.");
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "add 2 of those" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await waitFor(() => expect(calls.filter((c) => c.url === "/api/assistant/chat")).toHaveLength(2));
    expect(calls.filter((c) => c.url === "/api/assistant/chat")[1].body).toMatchObject({
      history: [{ role: "user", content: "find mangoes" }, { role: "assistant", content: "We have Alphonso Mango." }],
    });
    await waitFor(() => expect(screen.getAllByText("We have Alphonso Mango.")).toHaveLength(2));
    expect(JSON.parse(sessionStorage.getItem("kadai-chat") ?? "[]")).toHaveLength(4); // 2 questions + 2 replies
  });
});
