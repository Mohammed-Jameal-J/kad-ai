from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.catalog import (
    CategoryOut, NutritionOut, ProductDetailOut, ProductPage, ProductQuery, SearchQuery,
)
from app.services import catalog

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]


def _page(db: Session, f: ProductQuery) -> dict:
    items, total = catalog.list_products(db, f)
    return {
        "items": items, "total": total, "page": f.page, "page_size": f.page_size,
        "total_pages": (total + f.page_size - 1) // f.page_size,
    }


@router.get("/health", tags=["system"])
def health(db: DB):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "app": settings.app_name, "database": "ok"}


@router.get("/categories", response_model=list[CategoryOut], tags=["catalog"])
def get_categories(db: DB):
    return catalog.list_categories(db)


@router.get("/products", response_model=ProductPage, tags=["catalog"])
def get_products(db: DB, f: Annotated[ProductQuery, Query()]):
    """List active products with optional filters, sorting and pagination. Prices are in paise."""
    return _page(db, f)


# Declared before /products/{product_id} so "search" is not treated as a product id.
@router.get("/products/search", response_model=ProductPage, tags=["catalog"])
def search_products(db: DB, f: Annotated[SearchQuery, Query()]):
    """Same as /products but `q` is required."""
    return _page(db, f)


@router.get("/products/{product_id}", response_model=ProductDetailOut, tags=["catalog"])
def get_product(db: DB, product_id: str):
    """`product_id` may be the numeric id or the slug (e.g. `shimla-apple`)."""
    product, nutrition = catalog.get_product(db, product_id)
    out = ProductDetailOut.model_validate(product)
    out.nutrition = NutritionOut.model_validate(nutrition) if nutrition else None
    return out
