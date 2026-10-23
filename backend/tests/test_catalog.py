from app.db.seed import seed
from app.db.session import SessionLocal

ACTIVE_PRODUCTS = 33  # catalog.json has 34 products, one (jamun) inactive


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_is_repeatable(client):
    with SessionLocal() as db:
        assert seed(db) == {"categories": 0, "products": 0, "nutrition": 0}
    assert client.get("/api/products").json()["total"] == ACTIVE_PRODUCTS


def test_category_tree_and_counts(client):
    cats = client.get("/api/categories").json()
    assert [c["slug"] for c in cats] == ["fruits", "vegetables"]
    fruits = cats[0]
    assert [c["slug"] for c in fruits["children"]] == ["everyday-fruits", "citrus-fruits", "tropical-fruits"]
    assert fruits["product_count"] == 16
    assert cats[1]["product_count"] == 17


def test_list_products_pagination(client):
    body = client.get("/api/products", params={"page_size": 5, "page": 7}).json()
    assert body["total"] == ACTIVE_PRODUCTS
    assert body["total_pages"] == 7
    assert len(body["items"]) == 3
    assert "Demonstration" in body["price_note"]


def test_prices_are_integer_paise_and_discount(client):
    p = client.get("/api/products/shimla-apple").json()
    assert p["price_paise"] == 18000
    assert p["original_price_paise"] == 22000
    assert p["discount_percent"] == 18
    assert p["in_stock"] is True
    assert p["nutrition"] is None  # no verified reference seeded yet


def test_product_by_id_matches_slug(client, product_id):
    pid = product_id("robusta-banana")
    assert client.get(f"/api/products/{pid}").json()["slug"] == "robusta-banana"


def test_inactive_and_unknown_products_are_404(client):
    assert client.get("/api/products/jamun").status_code == 404
    assert client.get("/api/products/999999").status_code == 404
    slugs = [p["slug"] for p in client.get("/api/products", params={"page_size": 60}).json()["items"]]
    assert "jamun" not in slugs


def test_category_and_price_filter(client):
    body = client.get("/api/products", params={"category": "fruits", "max_price": 100, "page_size": 60}).json()
    assert body["total"] > 0
    fruit_subcats = {"fruits", "everyday-fruits", "citrus-fruits", "tropical-fruits"}
    for p in body["items"]:
        assert p["price_paise"] <= 10000
        assert p["category"]["slug"] in fruit_subcats


def test_sort_by_price(client):
    items = client.get("/api/products", params={"sort": "price_asc", "page_size": 60}).json()["items"]
    prices = [p["price_paise"] for p in items]
    assert prices == sorted(prices)
    items = client.get("/api/products", params={"sort": "price_desc", "page_size": 60}).json()["items"]
    assert items[0]["slug"] == "alphonso-mango"


def test_in_stock_filter_hides_out_of_stock(client):
    slugs = [p["slug"] for p in client.get("/api/products", params={"in_stock": True, "page_size": 60}).json()["items"]]
    assert "green-kiwi" not in slugs


def test_search(client):
    body = client.get("/api/products/search", params={"q": "mango"}).json()
    assert body["items"][0]["slug"] == "alphonso-mango"
    # matching on category name: "citrus" finds the citrus fruits
    assert client.get("/api/products/search", params={"q": "citrus"}).json()["total"] == 3
    # LIKE wildcards in user input are treated literally
    assert client.get("/api/products/search", params={"q": "%"}).json()["total"] == 0


def test_validation_errors(client):
    assert client.get("/api/products/search").status_code == 422
    assert client.get("/api/products", params={"min_price": 200, "max_price": 100}).status_code == 422
    assert client.get("/api/products", params={"sort": "cheapest"}).status_code == 422
    assert client.get("/api/products", params={"page_size": 500}).status_code == 422
    assert client.get("/api/products", params={"category": "nope"}).status_code == 404
