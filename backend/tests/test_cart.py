def _add(client, product_id, quantity=1, cart_id=None, **extra):
    headers = {"X-Cart-Id": cart_id} if cart_id else {}
    return client.post("/api/cart/items", json={"product_id": product_id, "quantity": quantity, **extra}, headers=headers)


def test_add_creates_cart_and_backend_calculates_total(client, product_id):
    r = _add(client, product_id("shimla-apple"))
    assert r.status_code == 201
    cart = r.json()
    cart_id = cart["cart_id"]
    assert cart_id

    cart = _add(client, product_id("robusta-banana"), cart_id=cart_id).json()
    # 1 kg apple (₹180) + 1 dozen banana (₹60) = ₹240, computed server-side in paise
    assert cart["subtotal_paise"] == 24000
    assert cart["item_count"] == 2
    assert client.get("/api/cart", headers={"X-Cart-Id": cart_id}).json() == cart


def test_adding_same_product_merges_lines(client, product_id):
    cart_id = _add(client, product_id("hybrid-tomato"), 2).json()["cart_id"]
    cart = _add(client, product_id("hybrid-tomato"), 3, cart_id=cart_id).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 5
    assert cart["subtotal_paise"] == 5 * 4000


def test_client_cannot_send_price(client, product_id):
    assert _add(client, product_id("shimla-apple"), price_paise=1).status_code == 422


def test_quantity_and_stock_validation(client, product_id):
    assert _add(client, product_id("shimla-apple"), 0).status_code == 422
    r = _add(client, product_id("kiran-watermelon"), 36)  # stock is 35
    assert r.status_code == 409
    assert "Only 35" in r.json()["detail"]
    assert _add(client, product_id("kiran-watermelon"), 35).status_code == 201
    assert _add(client, 999999).status_code == 404


def test_out_of_stock_and_inactive_products(client, product_id):
    r = _add(client, product_id("green-kiwi"))
    assert r.status_code == 409
    assert "out of stock" in r.json()["detail"]
    # jamun is inactive, so it has no public id; look it up directly
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import Product
    with SessionLocal() as db:
        jamun_id = db.scalar(select(Product.id).where(Product.slug == "jamun"))
    assert _add(client, jamun_id).status_code == 404


def test_update_and_remove_item(client, product_id):
    cart = _add(client, product_id("ooty-carrot"), 1).json()
    cart_id, item_id = cart["cart_id"], cart["items"][0]["id"]
    headers = {"X-Cart-Id": cart_id}

    cart = client.patch(f"/api/cart/items/{item_id}", json={"quantity": 4}, headers=headers).json()
    assert cart["items"][0]["quantity"] == 4
    assert cart["subtotal_paise"] == 4 * 6000

    assert client.patch(f"/api/cart/items/{item_id}", json={"quantity": 101}, headers=headers).status_code == 422
    assert client.patch(f"/api/cart/items/{item_id}", json={"quantity": 0}, headers=headers).status_code == 422

    cart = client.delete(f"/api/cart/items/{item_id}", headers=headers).json()
    assert cart["items"] == [] and cart["subtotal_paise"] == 0


def test_cannot_touch_another_carts_items(client, product_id):
    item_id = _add(client, product_id("potato")).json()["items"][0]["id"]
    other_cart = _add(client, product_id("garlic")).json()["cart_id"]
    headers = {"X-Cart-Id": other_cart}
    assert client.patch(f"/api/cart/items/{item_id}", json={"quantity": 2}, headers=headers).status_code == 404
    assert client.delete(f"/api/cart/items/{item_id}", headers=headers).status_code == 404
    assert client.delete(f"/api/cart/items/{item_id}").status_code == 404  # no cart header


def test_missing_and_malformed_cart_id(client):
    empty = client.get("/api/cart").json()
    assert empty == {**empty, "cart_id": None, "items": [], "subtotal_paise": 0}
    assert client.get("/api/cart", headers={"X-Cart-Id": "not-a-uuid"}).status_code == 422


def test_request_body_size_limit(client):
    r = client.post("/api/cart/items", content=b"x" * (65 * 1024), headers={"Content-Type": "application/json"})
    assert r.status_code == 413
