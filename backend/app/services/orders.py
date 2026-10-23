"""Demo checkout: turn a cart into an order in one transaction."""
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.errors import ServiceError, StockError
from app.models import Order, OrderItem, Product
from app.schemas.order import CheckoutRequest
from app.services.cart import get_cart


def place_order(db: Session, cart_id: str | None, data: CheckoutRequest, user_id: int | None = None) -> Order:
    cart = get_cart(db, cart_id)
    if cart is None or not cart.items:
        raise ServiceError("Your cart is empty")

    order = Order(**data.model_dump(), total_paise=0, user_id=user_id)
    for item in cart.items:
        p = item.product
        # Atomic check-and-decrement: succeeds only if the product is active and still has enough
        # stock at this moment, so two shoppers can never both buy the last unit.
        result = db.execute(
            update(Product)
            .where(Product.id == p.id, Product.is_active, Product.stock_quantity >= item.quantity)
            .values(stock_quantity=Product.stock_quantity - item.quantity)
        )
        if result.rowcount != 1:
            db.rollback()  # undo any stock already taken for earlier lines
            raise StockError(f"Not enough stock for {p.name}. Please update your cart and try again.")
        order.items.append(OrderItem(
            product_id=p.id, product_name=p.name, unit=p.unit, quantity=item.quantity,
            unit_price_paise=p.price_paise, line_total_paise=p.price_paise * item.quantity,
        ))
        order.total_paise += p.price_paise * item.quantity

    db.add(order)
    db.delete(cart)  # cart items cascade
    db.commit()
    return order
