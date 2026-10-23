"""Deterministic basket check used both as a CrewAI tool and as the final validation step.

Agents can propose anything; this code decides what is real: product ids must exist and be active,
quantities are clamped to stock and the per-line limit, and lines are dropped until the basket fits
the budget. Totals come from cart.quote() in integer paise.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas.cart import MAX_LINE_QUANTITY
from app.services import cart as cart_service


def validate_basket(db: Session, items: list[tuple[int, int]], budget_paise: int | None) -> dict:
    problems: list[str] = []
    merged: dict[int, int] = {}
    for product_id, quantity in items:
        merged[product_id] = merged.get(product_id, 0) + quantity

    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(merged), Product.is_active))}
    pairs: list[tuple[Product, int]] = []
    for product_id, wanted in merged.items():
        p = products.get(product_id)
        if p is None:
            problems.append(f"Product {product_id} does not exist, removed.")
            continue
        if p.stock_quantity == 0:
            problems.append(f"{p.name} is out of stock, removed.")
            continue
        quantity = max(1, min(wanted, p.stock_quantity, MAX_LINE_QUANTITY))
        if quantity != wanted:
            problems.append(f"{p.name}: quantity changed from {wanted} to {quantity} (stock or limit).")
        pairs.append((p, quantity))

    # Over budget: drop the most expensive line first, which keeps the most products in the basket.
    # ponytail: whole lines only; reduce quantities first if baskets with large quantities appear.
    while budget_paise and pairs and sum(p.price_paise * q for p, q in pairs) > budget_paise:
        priciest = max(pairs, key=lambda pq: pq[0].price_paise * pq[1])
        pairs.remove(priciest)
        problems.append(f"Removed {priciest[0].name} to stay within the budget.")

    quote = cart_service.quote(pairs)
    return {
        **quote,
        "budget_paise": budget_paise,
        "remaining_paise": budget_paise - quote["total_paise"] if budget_paise else None,
        "problems": problems,
        "products": [p for p, _ in pairs],
    }
