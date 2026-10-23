import { describe, expect, it } from "vitest";
import { parseFilters } from "@/components/listing/filters";
import { toQuery } from "@/lib/api";
import { rupees } from "@/lib/format";

describe("rupees", () => {
  it("formats integer paise without float maths", () => {
    expect(rupees(18000)).toBe("₹180");
    expect(rupees(18050)).toBe("₹180.50");
    expect(rupees(5)).toBe("₹0.05");
    expect(rupees(12345600)).toBe("₹1,23,456"); // Indian digit grouping
  });
});

describe("toQuery", () => {
  it("drops empty and false values", () => {
    expect(toQuery({ q: "mango", page: 2, in_stock: false, category: undefined, sort: "" })).toBe("?q=mango&page=2");
    expect(toQuery({})).toBe("");
  });
});

describe("parseFilters (untrusted URL params)", () => {
  it("keeps valid values", () => {
    expect(parseFilters({ q: " mango ", min_price: "10", max_price: "200", sort: "price_asc", page: "2", in_stock: "true" }, "fruits")).toEqual({
      q: "mango", category: "fruits", min_price: 10, max_price: 200, in_stock: true, on_sale: undefined,
      featured: undefined, bestseller: undefined, sort: "price_asc", page: 2, page_size: 12,
    });
  });

  it("ignores junk instead of passing it to the API", () => {
    const f = parseFilters({ sort: "drop table", min_price: "-5", max_price: "abc", page: "0", in_stock: "maybe" });
    expect(f.sort).toBeUndefined();
    expect(f.min_price).toBeUndefined();
    expect(f.max_price).toBeUndefined();
    expect(f.page).toBe(1);
    expect(f.in_stock).toBeUndefined();
  });

  it("caps the search length and takes the first of repeated params", () => {
    expect(parseFilters({ q: "x".repeat(300) }).q).toHaveLength(100);
    expect(parseFilters({ sort: ["newest", "price_desc"] }).sort).toBe("newest");
  });
});
