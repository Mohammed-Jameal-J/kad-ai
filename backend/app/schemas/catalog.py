from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.core.config import PRICE_NOTE

SortOption = Literal["relevance", "price_asc", "price_desc", "name_asc", "name_desc", "newest"]


class CategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class CategoryOut(CategoryRef):
    description: str
    image_path: str
    product_count: int
    children: list["CategoryOut"] = []


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    category: CategoryRef
    price_paise: int
    original_price_paise: int | None
    unit: str
    stock_quantity: int
    image_path: str
    rating: float
    is_featured: bool
    is_bestseller: bool

    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @computed_field
    @property
    def discount_percent(self) -> int:
        if not self.original_price_paise:
            return 0
        return (self.original_price_paise - self.price_paise) * 100 // self.original_price_paise


class NutritionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_description: str
    source_name: str
    source_id: str | None
    source_url: str | None
    serving_size_g: int
    energy_kcal: float | None
    protein_g: float | None
    carbohydrate_g: float | None
    fiber_g: float | None
    sugars_g: float | None
    fat_g: float | None
    vitamin_c_mg: float | None
    potassium_mg: float | None


class ProductDetailOut(ProductOut):
    nutrition: NutritionOut | None = None
    price_note: str = PRICE_NOTE


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    price_note: str = PRICE_NOTE


class ProductQuery(BaseModel):
    """Filters shared by GET /api/products and /api/products/search (and later the AI)."""

    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(None, max_length=100, description="Keyword in name, description or category")
    category: str | None = Field(None, max_length=80, description="Category slug; includes subcategories")
    min_price: int | None = Field(None, ge=0, description="Minimum price in whole rupees")
    max_price: int | None = Field(None, ge=0, description="Maximum price in whole rupees")
    in_stock: bool = False
    featured: bool | None = None
    bestseller: bool | None = None
    on_sale: bool = False
    sort: SortOption = "relevance"
    page: int = Field(1, ge=1)
    page_size: int = Field(12, ge=1, le=60)

    @model_validator(mode="after")
    def _check_price_range(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price must not be greater than max_price")
        if self.q is not None:
            self.q = self.q.strip() or None
        return self


class SearchQuery(ProductQuery):
    q: str = Field(..., min_length=1, max_length=100, description="Search keyword")
