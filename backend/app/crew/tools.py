"""Read-only tools for the CrewAI agents (plain functions, no CrewAI import, so they are testable).

Permission boundary: every function opens its own session, only READS through existing services
and returns JSON-friendly data. Nothing here writes to the database, the cart or orders, runs SQL
from the model, or touches the filesystem.
"""
from app.ai.parser import CATEGORY_WORDS, normalize
from app.core.config import PRICE_NOTE
from app.db.session import SessionLocal
from app.schemas.catalog import ProductQuery
from app.services import catalog
from app.services.assistant import rupees
from app.crew.validation import validate_basket

MAX_RESULTS = 8


def _row(p) -> dict:
    return {
        "product_id": p.id, "name": p.name, "category": p.category.name,
        "price": f"{rupees(p.price_paise)} per {p.unit}", "unit": p.unit, "stock": p.stock_quantity,
    }


def search_products(keyword: str = "", category: str = "", max_price_inr: int = 0) -> list[dict]:
    """In-stock products matching a keyword and/or category ("fruits" / "vegetables")."""
    category = CATEGORY_WORDS.get(normalize(category or "")) if category else None
    filters = {"category": category, "max_price": max_price_inr if max_price_inr and max_price_inr > 0 else None, "in_stock": True}
    with SessionLocal() as db:
        if keyword.strip():
            items = catalog.find_by_keyword(db, normalize(keyword.strip()[:40]), **filters)
        else:
            items, _ = catalog.list_products(db, ProductQuery(**filters, page_size=MAX_RESULTS))
        return [_row(p) for p in items[:MAX_RESULTS]]


def get_nutrition(product_id: int) -> dict:
    """Verified nutrition reference for a product, or an explicit 'not available'."""
    with SessionLocal() as db:
        try:
            product, ref = catalog.get_product(db, str(int(product_id)))
        except Exception:
            return {"product_id": product_id, "error": "No such product."}
        if ref is None:
            return {"product": product.name, "verified": False,
                    "message": "No verified nutrition data is available. Do not guess nutrient amounts or health effects."}
        values = {k: getattr(ref, k) for k in ("energy_kcal", "protein_g", "carbohydrate_g", "fiber_g", "sugars_g", "fat_g", "vitamin_c_mg", "potassium_mg") if getattr(ref, k) is not None}
        return {"product": product.name, "verified": True, "per_grams": ref.serving_size_g, "values": values, "source": ref.source_name}


def quote_basket(product_ids: list[int], quantities: list[int], budget_inr: int = 0) -> dict:
    """Price a proposed basket with database prices and stock. The returned total is authoritative."""
    pairs = [(int(pid), int(q)) for pid, q in zip(product_ids, quantities)]
    budget = budget_inr * 100 if budget_inr and budget_inr > 0 else None
    with SessionLocal() as db:
        proposed = validate_basket(db, pairs, None)  # judge the basket as proposed, not a trimmed one
        within = budget is None or proposed["total_paise"] <= budget
        trimmed = None if within else validate_basket(db, pairs, budget)

    def lines(r):
        return [f"{l['quantity']} x {l['unit']} {l['name']} = {rupees(l['line_total_paise'])}" for l in r["lines"]]

    result = {
        "lines": lines(proposed),
        "total": rupees(proposed["total_paise"]),
        "within_budget": within,
        "changes_made": proposed["problems"],
        "note": PRICE_NOTE,
    }
    if trimmed:
        result["suggestion_within_budget"] = {"lines": lines(trimmed), "total": rupees(trimmed["total_paise"])}
    return result
