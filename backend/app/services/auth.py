"""Accounts and login sessions, using only the standard library for crypto.

- Passwords: scrypt with a random 16-byte salt per user; compared in constant time.
- Sessions: random 32-byte token in an HttpOnly cookie; the DB stores only its SHA-256.
"""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ServiceError
from app.models import User, UserSession

SESSION_DAYS = 7
SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


class AuthError(ServiceError):
    status_code = 401


class EmailTaken(ServiceError):
    status_code = 409


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_b64, digest_b64 = stored.split("$")
        salt, expected = base64.b64decode(salt_b64), base64.b64decode(digest_b64)
    except ValueError:
        return False
    return hmac.compare_digest(hashlib.scrypt(password.encode(), salt=salt, **SCRYPT), expected)


# Used when the email doesn't exist, so a failed login takes as long as a wrong password
# (an attacker can't tell registered emails apart by timing).
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # SQLite stores naive UTC


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def register(db: Session, name: str, email: str, password: str) -> User:
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise EmailTaken("An account with this email already exists. Try logging in.")
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    # ponytail: no login rate limiting yet; add per-IP/email throttling before going public.
    user = db.scalar(select(User).where(User.email == email))
    if not verify_password(password, user.password_hash if user else _DUMMY_HASH) or user is None:
        raise AuthError("Invalid email or password.")
    return user


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.execute(delete(UserSession).where(UserSession.expires_at < _now()))  # tidy expired sessions
    db.add(UserSession(token_hash=_token_hash(token), user_id=user.id, expires_at=_now() + timedelta(days=SESSION_DAYS)))
    db.commit()
    return token


def user_for_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    session = db.get(UserSession, _token_hash(token))
    if session is None or session.expires_at < _now():
        return None
    return session.user


def end_session(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == _token_hash(token)))
        db.commit()
