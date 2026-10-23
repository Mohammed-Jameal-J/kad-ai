from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartOut
from app.services import cart as cart_service

router = APIRouter(prefix="/api/cart", tags=["cart"])
DB = Annotated[Session, Depends(get_db)]
# The browser stores the cart_id returned by POST /api/cart/items and sends it back in this header.
CartId = Annotated[UUID | None, Header(alias="X-Cart-Id")]


def _id(cart_id: UUID | None) -> str | None:
    return str(cart_id) if cart_id else None


@router.get("", response_model=CartOut)
def get_cart(db: DB, x_cart_id: CartId = None):
    """Unknown or missing cart id returns an empty cart (cart_id = null)."""
    return cart_service.summarize(cart_service.get_cart(db, _id(x_cart_id)))


@router.post("/items", response_model=CartOut, status_code=201)
def add_item(db: DB, body: CartItemCreate, x_cart_id: CartId = None):
    """Add a product. Creates a new cart when no valid X-Cart-Id is sent; keep the returned cart_id."""
    cart = cart_service.add_item(db, _id(x_cart_id), body.product_id, body.quantity)
    return cart_service.summarize(cart)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_item(db: DB, item_id: int, body: CartItemUpdate, x_cart_id: CartId = None):
    """Set the absolute quantity of a cart line."""
    return cart_service.summarize(cart_service.update_item(db, _id(x_cart_id), item_id, body.quantity))


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(db: DB, item_id: int, x_cart_id: CartId = None):
    return cart_service.summarize(cart_service.remove_item(db, _id(x_cart_id), item_id))
