from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import PRICE_NOTE
from app.schemas.catalog import NutritionOut, ProductOut

Intent = Literal["search", "nutrition", "compare", "budget_basket", "add_to_cart", "other"]


class ParsedRequest(BaseModel):
    """What the intent model (or the rule parser) extracts. Validated before any DB query."""

    intent: Intent
    keywords: list[str] = Field(default=[], max_length=6)
    category: Literal["fruits", "vegetables"] | None = None
    budget_inr: int | None = Field(None, ge=1, le=100_000)
    quantity: int | None = Field(None, ge=1, le=50)
    quantity_unit: Literal["kg", "g", "dozen", "piece", "bunch", "pack"] | None = None
    in_stock_only: bool = False

    @field_validator("keywords")
    @classmethod
    def _clean_keywords(cls, words: list[str]) -> list[str]:
        cleaned = [w.strip().lower()[:40] for w in words]
        return list(dict.fromkeys(w for w in cleaned if w))  # drop blanks and duplicates


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=1000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=500)
    history: list[ChatTurn] = Field(default=[], max_length=10)
    lang: Literal["en", "es", "ar", "hi"] = "en"  # language for the reply (the site's UI language)


class BasketLine(BaseModel):
    product_id: int
    name: str
    unit: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int


class Basket(BaseModel):
    lines: list[BasketLine]
    total_paise: int
    budget_paise: int | None = None
    remaining_paise: int | None = None


class PendingCartItem(BaseModel):
    product_id: int
    quantity: int


class PendingAction(BaseModel):
    """A cart change the assistant proposes. It is NOT applied: the customer must confirm,
    and the frontend then calls POST /api/cart/items, which re-validates everything."""

    type: Literal["add_to_cart"] = "add_to_cart"
    items: list[PendingCartItem]
    total_paise: int
    summary: str


class ProductNutrition(BaseModel):
    product_id: int
    product_name: str
    nutrition: NutritionOut | None  # None = no verified reference available


class ChatResponse(BaseModel):
    reply: str
    intent: Intent
    products: list[ProductOut] = []
    basket: Basket | None = None
    pending_action: PendingAction | None = None
    nutrition: list[ProductNutrition] = []
    notes: list[str] = []
    parser: str  # "rules", the intent model name, or "fallback"
    writer: str  # "template" or the response model name
    duration_ms: int
    price_note: str = PRICE_NOTE
