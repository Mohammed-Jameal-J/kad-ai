from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str] = mapped_column(String(255), default="")
    sort_order: Mapped[int] = mapped_column(default=0)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    parent: Mapped["Category | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", order_by="Category.sort_order"
    )
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_paise > 0", name="ck_price_positive"),
        CheckConstraint(
            "original_price_paise IS NULL OR original_price_paise >= price_paise",
            name="ck_original_price",
        ),
        CheckConstraint("stock_quantity >= 0", name="ck_stock_non_negative"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    # Money is stored as integer paise (₹1 = 100 paise) so totals never hit float rounding.
    price_paise: Mapped[int]
    original_price_paise: Mapped[int | None]
    unit: Mapped[str] = mapped_column(String(30))  # "kg", "dozen", "piece", "500 g" ...
    stock_quantity: Mapped[int] = mapped_column(default=0)  # counted in `unit`s
    image_path: Mapped[str] = mapped_column(String(255), default="")
    # Float stated explicitly: SQLAlchemy 2.1 maps bare Mapped[float] to DOUBLE, 2.0 to FLOAT.
    rating: Mapped[float] = mapped_column(Float, default=0)  # demo rating, there is no reviews table yet
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    is_featured: Mapped[bool] = mapped_column(default=False)
    is_bestseller: Mapped[bool] = mapped_column(default=False)
    # ponytail: plain string key, no FK, so products can be seeded before their nutrition
    # reference exists. Make it a real FK once every product has a verified reference.
    nutrition_key: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    category: Mapped[Category] = relationship(back_populates="products")


class NutritionReference(Base):
    """Per-serving nutrient values copied from a cited public source (e.g. USDA FoodData Central).

    Rows are only trusted when `verified` is true. Nothing here should come from an LLM.
    """

    __tablename__ = "nutrition_references"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    food_description: Mapped[str] = mapped_column(String(200))
    source_name: Mapped[str] = mapped_column(String(120))
    source_id: Mapped[str | None] = mapped_column(String(40))
    source_url: Mapped[str | None] = mapped_column(String(255))
    serving_size_g: Mapped[int] = mapped_column(default=100)
    energy_kcal: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbohydrate_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    sugars_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    vitamin_c_mg: Mapped[float | None] = mapped_column(Float)
    potassium_mg: Mapped[float | None] = mapped_column(Float)
    verified: Mapped[bool] = mapped_column(default=False)
