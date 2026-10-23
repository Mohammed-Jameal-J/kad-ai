from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.errors import TooManyAttempts
from app.core.ratelimit import RateLimiter, client_ip, enforce
from app.db.session import get_db
from app.models import ContactMessage, NewsletterSubscriber, Order, User
from app.schemas.order import OrderOut
from app.schemas.user import ContactRequest, LoginRequest, NewsletterRequest, RegisterRequest, UserOut
from app.services import auth, email

router = APIRouter(prefix="/api", tags=["account"])
DB = Annotated[Session, Depends(get_db)]
COOKIE = "kadai_session"
SessionToken = Annotated[str | None, Cookie(alias=COOKIE)]


def current_user(db: DB, token: SessionToken = None) -> User | None:
    """Dependency: the logged-in user, or None for guests."""
    return auth.user_for_token(db, token)


def require_user(user: Annotated[User | None, Depends(current_user)]) -> User:
    if user is None:
        raise auth.AuthError("Please log in first.")
    return user


def _start_session(db: Session, user: User, response: Response) -> None:
    # HttpOnly: page scripts can't read it. SameSite=Lax: not sent on cross-site POSTs (CSRF).
    # Secure (HTTPS only) is a setting: off for http://localhost, on when deployed.
    response.set_cookie(
        COOKIE, auth.create_session(db, user), httponly=True, samesite="lax", secure=settings.cookie_secure,
        max_age=auth.SESSION_DAYS * 24 * 3600, path="/",
    )


# Brute-force protection. Failed logins are counted per email+IP and per IP (password spraying).
LOGIN_FAILURES = RateLimiter(limit=5, window_seconds=15 * 60)
LOGIN_FAILURES_PER_IP = RateLimiter(limit=20, window_seconds=15 * 60)
REGISTRATIONS_PER_IP = RateLimiter(limit=10, window_seconds=60 * 60)
CONTACT_PER_IP = RateLimiter(limit=5, window_seconds=60 * 60)
NEWSLETTER_PER_IP = RateLimiter(limit=5, window_seconds=60 * 60)


def _check(limiter: RateLimiter, key: str) -> None:
    if wait := limiter.retry_after(key):
        raise TooManyAttempts(wait)


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, db: DB, request: Request, response: Response, background: BackgroundTasks):
    ip = client_ip(request)
    enforce(REGISTRATIONS_PER_IP, ip)
    user = auth.register(db, body.name, body.email, body.password)
    _start_session(db, user, response)  # registering also logs you in
    background.add_task(email.send_welcome, user.email, user.name)  # after the response: no waiting on Resend
    return user


@router.post("/auth/login", response_model=UserOut)
def login(body: LoginRequest, db: DB, request: Request, response: Response):
    ip = client_ip(request)
    key = f"{ip}|{body.email}"
    _check(LOGIN_FAILURES, key)
    _check(LOGIN_FAILURES_PER_IP, ip)
    try:
        user = auth.authenticate(db, body.email, body.password)
    except auth.AuthError:
        LOGIN_FAILURES.record(key)
        LOGIN_FAILURES_PER_IP.record(ip)
        raise
    LOGIN_FAILURES.reset(key)
    _start_session(db, user, response)
    return user


@router.post("/auth/logout", status_code=204)
def logout(db: DB, response: Response, token: SessionToken = None):
    auth.end_session(db, token)
    response.delete_cookie(COOKIE, path="/")


@router.get("/auth/me", response_model=UserOut)
def me(user: Annotated[User, Depends(require_user)]):
    return user


@router.get("/orders/mine", response_model=list[OrderOut])
def my_orders(db: DB, user: Annotated[User, Depends(require_user)]):
    return db.scalars(
        select(Order).options(selectinload(Order.items))
        .where(Order.user_id == user.id).order_by(Order.created_at.desc())
    ).all()


@router.post("/contact", status_code=201)
def contact(body: ContactRequest, db: DB, request: Request):
    # ponytail: stored only, no email is sent; rate limited per IP against spam.
    ip = client_ip(request)
    enforce(CONTACT_PER_IP, ip)
    db.add(ContactMessage(name=body.name, email=body.email, message=body.message))
    db.commit()
    return {"status": "received"}


@router.post("/newsletter", status_code=201)
def subscribe(body: NewsletterRequest, db: DB, request: Request, background: BackgroundTasks):
    """Same answer for new and existing addresses, so the endpoint can't be used to test who subscribed.
    The confirmation email goes only to new subscribers."""
    enforce(NEWSLETTER_PER_IP, client_ip(request))
    if db.scalar(select(NewsletterSubscriber).where(NewsletterSubscriber.email == body.email)) is None:
        db.add(NewsletterSubscriber(email=body.email))
        db.commit()
        background.add_task(email.send_newsletter_confirmation, body.email)
    return {"status": "subscribed"}
