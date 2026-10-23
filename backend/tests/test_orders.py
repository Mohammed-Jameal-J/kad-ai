from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Product

CUSTOMER = {"customer_name": "Test Shopper", "phone": "+91 98765 43210", "address": "12 Demo Street, Chennai", "delivery_slot": "08-12"}


def stock(slug):
    with SessionLocal() as db:
        return db.scalar(select(Product.stock_quantity).where(Product.slug == slug))


def set_stock(slug, value):
    with SessionLocal() as db:
        db.scalar(select(Product).where(Product.slug == slug)).stock_quantity = value
        db.commit()


def fill_cart(client, product_id, lines):
    cart_id = None
    for slug, qty in lines:
        headers = {"X-Cart-Id": cart_id} if cart_id else {}
        cart_id = client.post("/api/cart/items", json={"product_id": product_id(slug), "quantity": qty}, headers=headers).json()["cart_id"]
    return {"X-Cart-Id": cart_id}


def test_place_order(client, product_id):
    before = stock("cucumber"), stock("green-cabbage")
    headers = fill_cart(client, product_id, [("cucumber", 2), ("green-cabbage", 1)])

    r = client.post("/api/orders", json=CUSTOMER, headers=headers)
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["total_paise"] == 2 * 4000 + 3000  # computed from DB prices
    assert [(i["product_name"], i["quantity"]) for i in order["items"]] == [("Cucumber", 2), ("Green Cabbage", 1)]
    assert order["status"] == "placed_demo" and "no payment" in order["notice"]
    assert (stock("cucumber"), stock("green-cabbage")) == (before[0] - 2, before[1] - 1)
    assert client.get("/api/cart", headers=headers).json()["items"] == []  # cart emptied


def test_empty_or_missing_cart(client):
    assert client.post("/api/orders", json=CUSTOMER).status_code == 400
    r = client.post("/api/orders", json=CUSTOMER, headers={"X-Cart-Id": "00000000-0000-4000-8000-000000000000"})
    assert r.status_code == 400 and r.json()["detail"] == "Your cart is empty"


def test_checkout_validation(client, product_id):
    headers = fill_cart(client, product_id, [("beetroot", 1)])
    bad = [
        {**CUSTOMER, "phone": "call me"},
        {**CUSTOMER, "delivery_slot": "midnight"},
        {**CUSTOMER, "customer_name": "A"},
        {**CUSTOMER, "card_number": "4111111111111111"},  # payment details are never accepted
        {k: v for k, v in CUSTOMER.items() if k != "address"},
    ]
    for body in bad:
        assert client.post("/api/orders", json=body, headers=headers).status_code == 422, body


def test_stock_shortage_rolls_back_everything(client, product_id):
    headers = fill_cart(client, product_id, [("beetroot", 2), ("sweet-potato", 3)])
    beet_before, potato_before = stock("beetroot"), stock("sweet-potato")
    set_stock("sweet-potato", 2)  # someone else bought them after they were added to the cart
    try:
        r = client.post("/api/orders", json=CUSTOMER, headers=headers)
        assert r.status_code == 409
        assert "Sweet Potato" in r.json()["detail"]
        assert stock("beetroot") == beet_before  # the first line's stock was not taken
        assert len(client.get("/api/cart", headers=headers).json()["items"]) == 2  # cart kept
    finally:
        set_stock("sweet-potato", potato_before)
