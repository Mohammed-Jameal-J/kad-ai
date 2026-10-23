"""Server-side cart rules. Prices and totals are always computed here from product rows;
nothing price-related is ever accepted from the client."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError, StockError
from app.models import Cart, CartItem, Product
from app.schemas.cart import MAX_LINE_QUANTITY


def get_cart(db: Session, cart_id: str | None) -> Cart | None:
    if not cart_id:
        return None
    return db.scalar(
        select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product))
        .where(Cart.id == cart_id)
    )


def check_quantity(product: Product, quantity: int) -> None:
    if quantity > MAX_LINE_QUANTITY:
        raise StockError(f"At most {MAX_LINE_QUANTITY} x {product.unit} of one product per order")
    if quantity > product.stock_quantity:
        raise StockError(
            f"Only {product.stock_quantity} x {product.unit} of {product.name} in stock"
            if product.stock_quantity else f"{product.name} is out of stock"
        )


def _get_item(cart: Cart | None, item_id: int) -> CartItem:
    item = next((i for i in cart.items if i.id == item_id), None) if cart else None
    if item is None:
        raise NotFoundError("Cart item not found")
    return item


def add_item(db: Session, cart_id: str | None, product_id: int, quantity: int) -> Cart:
    """Add quantity to the cart (merging with an existing line). Creates the cart if needed."""
    product = db.scalar(select(Product).where(Product.id == product_id, Product.is_active))
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")

    cart = get_cart(db, cart_id)
    if cart is None:
        cart = Cart()
        db.add(cart)

    item = next((i for i in cart.items if i.product_id == product_id), None)
    new_quantity = quantity + (item.quantity if item else 0)
    check_quantity(product, new_quantity)

    if item:
        item.quantity = new_quantity
    else:
        cart.items.append(CartItem(product=product, quantity=new_quantity))
    db.commit()
    return cart


def update_item(db: Session, cart_id: str | None, item_id: int, quantity: int) -> Cart:
    cart = get_cart(db, cart_id)
    item = _get_item(cart, item_id)
    if not item.product.is_active:
        raise NotFoundError(f"{item.product.name} is no longer available")
    check_quantity(item.product, quantity)
    item.quantity = quantity
    db.commit()
    return cart


def remove_item(db: Session, cart_id: str | None, item_id: int) -> Cart:
    cart = get_cart(db, cart_id)
    item = _get_item(cart, item_id)
    cart.items.remove(item)
    db.commit()
    return cart


def summarize(cart: Cart | None) -> dict:
    """Build the cart response. All arithmetic is integer paise."""
    lines = []
    for item in cart.items if cart else []:
        p = item.product
        lines.append({
            "id": item.id,
            "product": p,
            "quantity": item.quantity,
            "unit_price_paise": p.price_paise,
            "line_total_paise": p.price_paise * item.quantity,
            "available": p.is_active and item.quantity <= p.stock_quantity,
        })
    return {
        "cart_id": cart.id if cart else None,
        "items": lines,
        "item_count": sum(line["quantity"] for line in lines),
        "subtotal_paise": sum(line["line_total_paise"] for line in lines),
    }


def quote(pairs: list[tuple[Product, int]]) -> dict:
    """Price (product, quantity) pairs with current DB prices, without touching any cart."""
    lines = [{
        "product_id": p.id, "name": p.name, "unit": p.unit, "quantity": qty,
        "unit_price_paise": p.price_paise, "line_total_paise": p.price_paise * qty,
    } for p, qty in pairs]
    return {"lines": lines, "total_paise": sum(line["line_total_paise"] for line in lines)}
