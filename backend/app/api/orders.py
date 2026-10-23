from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.api.cart import CartId
from app.core.ratelimit import RateLimiter, client_ip, enforce
from app.db.session import get_db
from app.models import User
from app.schemas.order import CheckoutRequest, OrderOut
from app.services.orders import place_order

router = APIRouter(prefix="/api/orders", tags=["orders"])
# Orders reduce stock without payment, so a script could "buy out" the shop. Cap per IP.
ORDERS_PER_IP = RateLimiter(limit=5, window_seconds=60 * 60)


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    body: CheckoutRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
    request: Request,
    x_cart_id: CartId = None,
):
    """Demo checkout for the cart in `X-Cart-Id`. Re-checks stock, uses current DB prices,
    reduces stock and empties the cart. No payment is taken. Linked to the account when logged in."""
    enforce(ORDERS_PER_IP, client_ip(request))
    return place_order(db, str(x_cart_id) if x_cart_id else None, body, user.id if user else None)
