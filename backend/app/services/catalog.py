import re

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import NotFoundError
from app.models import Category, NutritionReference, Product
from app.schemas.catalog import ProductQuery


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_category(db: Session, slug: str) -> Category:
    category = db.scalar(select(Category).where(Category.slug == slug))
    if category is None:
        raise NotFoundError(f"Category '{slug}' not found")
    return category


def list_categories(db: Session) -> list[dict]:
    """Category tree (parents with children) with active product counts."""
    counts = dict(db.execute(
        select(Product.category_id, func.count())
        .where(Product.is_active)
        .group_by(Product.category_id)
    ).all())

    def to_dict(cat: Category) -> dict:
        children = [to_dict(c) for c in cat.children]
        return {
            "id": cat.id, "slug": cat.slug, "name": cat.name,
            "description": cat.description, "image_path": cat.image_path,
            "product_count": counts.get(cat.id, 0) + sum(c["product_count"] for c in children),
            "children": children,
        }

    roots = db.scalars(
        select(Category).where(Category.parent_id.is_(None)).order_by(Category.sort_order)
    )
    return [to_dict(c) for c in roots]


def list_products(db: Session, f: ProductQuery) -> tuple[list[Product], int]:
    stmt = select(Product).join(Product.category).where(Product.is_active)

    like = None
    if f.q:
        like = f"%{_escape_like(f.q)}%"
        stmt = stmt.where(or_(
            Product.name.ilike(like, escape="\\"),
            Product.description.ilike(like, escape="\\"),
            Category.name.ilike(like, escape="\\"),
        ))
    if f.category:
        category = get_category(db, f.category)
        # ponytail: one level of subcategories, matching the seed data. Use a recursive CTE if deeper trees appear.
        ids = [category.id] + [c.id for c in category.children]
        stmt = stmt.where(Product.category_id.in_(ids))
    if f.min_price is not None:
        stmt = stmt.where(Product.price_paise >= f.min_price * 100)
    if f.max_price is not None:
        stmt = stmt.where(Product.price_paise <= f.max_price * 100)
    if f.in_stock:
        stmt = stmt.where(Product.stock_quantity > 0)
    if f.featured is not None:
        stmt = stmt.where(Product.is_featured == f.featured)
    if f.bestseller is not None:
        stmt = stmt.where(Product.is_bestseller == f.bestseller)
    if f.on_sale:
        stmt = stmt.where(Product.original_price_paise > Product.price_paise)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    order = {
        "price_asc": [Product.price_paise, Product.id],
        "price_desc": [Product.price_paise.desc(), Product.id],
        "name_asc": [Product.name, Product.id],
        "name_desc": [Product.name.desc(), Product.id],
        "newest": [Product.id.desc()],
    }.get(f.sort)
    if order is None:  # relevance: name matches first, then featured/bestsellers
        order = [Product.is_featured.desc(), Product.is_bestseller.desc(), Product.id]
        if like:
            order.insert(0, case((Product.name.ilike(like, escape="\\"), 0), else_=1))

    items = db.scalars(
        stmt.options(joinedload(Product.category))
        .order_by(*order)
        .offset((f.page - 1) * f.page_size)
        .limit(f.page_size)
    ).all()
    return list(items), total


def find_by_keyword(db: Session, keyword: str, **filters) -> list[Product]:
    """Products matching one keyword, preferring name matches ("orange" -> Nagpur Orange,
    not carrots whose description says "bright orange"). `filters` are ProductQuery fields."""
    items, _ = list_products(db, ProductQuery(q=keyword, page_size=20, **filters))
    # Match at the start of a word: "apple" finds "Shimla Apple" but not "Queen Pineapple".
    starts_word = re.compile(rf"\b{re.escape(keyword.lower())}")
    name_hits = [p for p in items if starts_word.search(p.name.lower())]
    return name_hits or items


def verified_nutrition(db: Session, keys: set[str]) -> dict[str, NutritionReference]:
    rows = db.scalars(select(NutritionReference).where(
        NutritionReference.key.in_(keys), NutritionReference.verified
    ))
    return {r.key: r for r in rows}


def get_product(db: Session, id_or_slug: str) -> tuple[Product, NutritionReference | None]:
    """Look up an active product by numeric id or slug, plus its verified nutrition reference."""
    column = Product.id if id_or_slug.isdigit() else Product.slug
    value = int(id_or_slug) if id_or_slug.isdigit() else id_or_slug
    product = db.scalar(
        select(Product).options(joinedload(Product.category))
        .where(column == value, Product.is_active)
    )
    if product is None:
        raise NotFoundError(f"Product '{id_or_slug}' not found")
    refs = verified_nutrition(db, {product.nutrition_key}) if product.nutrition_key else {}
    return product, refs.get(product.nutrition_key)
