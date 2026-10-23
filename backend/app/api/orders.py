from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.api.cart import CartId
from app.db.session import get_db
from app.models import User
from app.schemas.order import CheckoutRequest, OrderOut
from app.services.orders import place_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    body: CheckoutRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
    x_cart_id: CartId = None,
):
    """Demo checkout for the cart in `X-Cart-Id`. Re-checks stock, uses current DB prices,
    reduces stock and empties the cart. No payment is taken. Linked to the account when logged in."""
    return place_order(db, str(x_cart_id) if x_cart_id else None, body, user.id if user else None)
