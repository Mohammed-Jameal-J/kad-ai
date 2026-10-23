from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import ContactMessage, User, UserSession

pytestmark = pytest.mark.usefixtures("client")  # creates and seeds the test database
PASSWORD = "correct horse battery"


@pytest.fixture
def browser():
    """A fresh client with its own cookie jar, like a separate browser."""
    with TestClient(app) as c:
        yield c


def new_email() -> str:
    return f"user-{uuid4().hex[:8]}@Example.com"


def register(c, email=None, name="Asha", password=PASSWORD):
    return c.post("/api/auth/register", json={"name": name, "email": email or new_email(), "password": password})


def test_register_logs_in_with_httponly_cookie(browser):
    r = register(browser)
    assert r.status_code == 201
    cookie = r.headers["set-cookie"].lower()
    assert "kadai_session=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    me = browser.get("/api/auth/me").json()
    assert me["name"] == "Asha" and me["email"].endswith("@example.com")  # stored lower-case


def test_password_is_hashed_never_stored(browser):
    email = new_email()
    register(browser, email)
    with SessionLocal() as db:
        stored = db.scalar(select(User.password_hash).where(User.email == email.lower()))
    assert stored.startswith("scrypt$") and PASSWORD not in stored


def test_duplicate_email_is_rejected(browser):
    email = new_email()
    register(browser, email)
    r = register(browser, email.upper())  # same email, different case
    assert r.status_code == 409


def test_login_errors_do_not_reveal_which_part_was_wrong(browser):
    email = new_email()
    register(browser, email)
    browser.post("/api/auth/logout")
    wrong_pw = browser.post("/api/auth/login", json={"email": email, "password": "nope-nope"})
    no_user = browser.post("/api/auth/login", json={"email": new_email(), "password": PASSWORD})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json() == {"detail": "Invalid email or password."}
    assert browser.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_logout_ends_the_session(browser):
    register(browser)
    token = browser.cookies.get("kadai_session")
    assert browser.post("/api/auth/logout").status_code == 204
    browser.cookies.set("kadai_session", token)  # replaying the old cookie must not work
    assert browser.get("/api/auth/me").status_code == 401


def test_expired_session_is_rejected(browser):
    register(browser)
    with SessionLocal() as db:
        for s in db.scalars(select(UserSession)):
            s.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db.commit()
    assert browser.get("/api/auth/me").status_code == 401


def test_validation(browser):
    assert register(browser, password="short").status_code == 422
    assert register(browser, email="not-an-email").status_code == 422
    assert browser.post("/api/auth/register", json={"name": "A", "email": new_email(), "password": PASSWORD, "is_admin": True}).status_code == 422
    assert browser.get("/api/auth/me").status_code == 401
    assert browser.get("/api/orders/mine").status_code == 401


def checkout(c, product_id):
    cart_id = c.post("/api/cart/items", json={"product_id": product_id, "quantity": 1}).json()["cart_id"]
    return c.post("/api/orders", headers={"X-Cart-Id": cart_id}, json={
        "customer_name": "Asha", "phone": "+91 90000 00000", "address": "1 Test Street, Coimbatore", "delivery_slot": "12-16",
    })


def test_orders_are_linked_to_the_account_and_private(browser, product_id):
    register(browser)
    order = checkout(browser, product_id("lemon")).json()
    assert [o["id"] for o in browser.get("/api/orders/mine").json()] == [order["id"]]

    with TestClient(app) as other:  # a second person
        register(other)
        assert other.get("/api/orders/mine").json() == []
        guest_order = checkout(other, product_id("lemon"))  # checkout still works for everyone
        assert guest_order.status_code == 201
    assert len(browser.get("/api/orders/mine").json()) == 1


def test_contact_message_is_stored(browser):
    r = browser.post("/api/contact", json={"name": "Ravi", "email": "ravi@example.com", "message": "Do you deliver to Peelamedu?"})
    assert r.status_code == 201
    with SessionLocal() as db:
        assert db.scalar(select(ContactMessage).where(ContactMessage.name == "Ravi")).message.startswith("Do you deliver")
    assert browser.post("/api/contact", json={"name": "R", "email": "x", "message": "short"}).status_code == 422
