from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import PRICE_NOTE

DeliverySlot = Literal["08-12", "12-16", "16-20"]
DEMO_NOTICE = "This is a demo order: no payment was taken and nothing will be delivered."


class CheckoutRequest(BaseModel):
    """No payment fields on purpose: the demo never collects card or UPI details."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_name: str = Field(..., min_length=2, max_length=80)
    phone: str = Field(..., pattern=r"^\+?[0-9][0-9 \-]{6,18}$")
    address: str = Field(..., min_length=5, max_length=300)
    delivery_slot: DeliverySlot


class OrderLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    unit: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_name: str
    delivery_slot: str
    payment_method: str
    status: str
    total_paise: int
    items: list[OrderLine]
    notice: str = DEMO_NOTICE
    price_note: str = PRICE_NOTE
