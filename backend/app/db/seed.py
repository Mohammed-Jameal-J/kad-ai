"""Create tables and insert the demo catalog.

Safe to run any number of times: rows are matched by slug and only missing ones are
inserted. Existing rows are never overwritten, so stock changes made later survive restarts.

Run manually:  python -m app.db.seed
"""
import json

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR
from app.db.session import SessionLocal, engine
from app.models import Category, NutritionReference, Product

CATALOG_FILE = BACKEND_DIR / "data" / "catalog.json"
NUTRITION_FILE = BACKEND_DIR / "data" / "nutrition.json"


def seed(db: Session) -> dict[str, int]:
    data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    categories = {c.slug: c for c in db.scalars(select(Category))}
    existing_products = set(db.scalars(select(Product.slug)))
    added = {"categories": 0, "products": 0, "nutrition": 0}

    def add_category(raw: dict, order: int, parent: Category | None = None) -> None:
        cat = categories.get(raw["slug"])
        if cat is None:
            cat = Category(
                slug=raw["slug"],
                name=raw["name"],
                description=raw.get("description", ""),
                image_path=f"/images/categories/{raw['slug']}.jpg",
                sort_order=order,
                parent=parent,
            )
            db.add(cat)
            categories[cat.slug] = cat
            added["categories"] += 1
        for i, child in enumerate(raw.get("children", [])):
            add_category(child, i, cat)

    for i, raw in enumerate(data["categories"]):
        add_category(raw, i)

    for raw in data["products"]:
        if raw["slug"] in existing_products:
            continue
        original = raw.get("original_price_inr")
        db.add(Product(
            slug=raw["slug"],
            name=raw["name"],
            description=raw["description"],
            category=categories[raw["category"]],
            price_paise=raw["price_inr"] * 100,
            original_price_paise=original * 100 if original else None,
            unit=raw["unit"],
            stock_quantity=raw["stock"],
            image_path=f"/images/products/{raw['slug']}.jpg",
            rating=raw.get("rating", 0),
            is_active=raw.get("active", True),
            is_featured=raw.get("featured", False),
            is_bestseller=raw.get("bestseller", False),
            nutrition_key=raw.get("nutrition_key"),
        ))
        added["products"] += 1

    existing_refs = set(db.scalars(select(NutritionReference.key)))
    refs = json.loads(NUTRITION_FILE.read_text(encoding="utf-8"))["references"]
    for raw in refs:
        if raw["key"] not in existing_refs:
            db.add(NutritionReference(**raw))
            added["nutrition"] += 1

    db.commit()
    return added


BASELINE_REVISION = "d156f4eb1686"  # migrations/versions/d156f4eb1686_baseline_schema.py


def run_migrations() -> None:
    """Bring the schema up to date with Alembic (replaces create_all, which could not alter tables)."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        tables = inspect(connection).get_table_names()
        if "products" in tables and "alembic_version" not in tables:
            # Database created by create_all before migrations existed: it matches the baseline.
            command.stamp(cfg, BASELINE_REVISION)
        command.upgrade(cfg, "head")


def init_db() -> dict[str, int]:
    run_migrations()
    with SessionLocal() as db:
        return seed(db)


if __name__ == "__main__":
    print("Seed result (rows added):", init_db())
