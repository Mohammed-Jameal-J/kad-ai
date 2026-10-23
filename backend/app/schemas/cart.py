from pydantic import BaseModel, ConfigDict, Field

from app.core.config import PRICE_NOTE

MAX_LINE_QUANTITY = 50


class CartItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a client-sent "price" is rejected, not ignored

    product_id: int = Field(..., gt=0)
    quantity: int = Field(1, ge=1, le=MAX_LINE_QUANTITY)


class CartItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(..., ge=1, le=MAX_LINE_QUANTITY)


class CartProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    unit: str
    image_path: str
    stock_quantity: int


class CartLine(BaseModel):
    id: int
    product: CartProduct
    quantity: int
    unit_price_paise: int
    line_total_paise: int
    available: bool  # false if the product was deactivated or stock dropped below quantity


class CartOut(BaseModel):
    cart_id: str | None
    items: list[CartLine]
    item_count: int
    subtotal_paise: int
    currency: str = "INR"
    price_note: str = PRICE_NOTE
