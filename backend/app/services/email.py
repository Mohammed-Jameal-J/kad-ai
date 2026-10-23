"""Transactional email through Resend's HTTP API (https://resend.com/docs/api-reference/emails/send-email).

No SDK: one POST with httpx. Without RESEND_API_KEY nothing is sent (local dev, tests) and the app
behaves the same. Sending never raises: a failed email must not fail a registration.
Logs never contain addresses or content.
"""
import html
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("kadai.email")
RESEND_URL = "https://api.resend.com/emails"


def send(to: str, subject: str, body_html: str) -> bool:
    if not settings.resend_api_key:
        logger.info("Email skipped, RESEND_API_KEY not set: %s", subject)
        return False
    try:
        r = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": body_html},
            timeout=10,
        )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        # 403 with the onboarding@resend.dev sender = recipient is not the Resend account owner.
        logger.warning("Email not sent (%s): Resend returned %s", subject, e.response.status_code)
        return False
    except httpx.HTTPError as e:
        logger.warning("Email not sent (%s): %s", subject, type(e).__name__)
        return False
    logger.info("Email sent: %s", subject)
    return True


def _layout(heading: str, paragraphs: list[str]) -> str:
    """Simple inline-styled HTML (email clients ignore stylesheets). Callers escape user text."""
    body = "".join(f'<p style="margin:0 0 14px;line-height:1.6">{p}</p>' for p in paragraphs)
    return (
        '<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:24px;'
        'background:#faf0dc;border-radius:16px;color:#1f2a1f">'
        f'<h1 style="font-family:Georgia,serif;color:#235e36;font-size:24px;margin:0 0 16px">{heading}</h1>'
        f'{body}'
        f'<p style="margin:20px 0 0"><a href="{html.escape(settings.site_url)}" style="background:#235e36;color:#fff;'
        'padding:10px 18px;border-radius:999px;text-decoration:none">Visit Kad AI</a></p>'
        '<p style="margin:20px 0 0;font-size:12px;color:#6b6b6b">Kad AI demo store, Coimbatore. '
        'Prices on the site are demonstration prices.</p></div>'
    )


def send_welcome(to: str, name: str) -> bool:
    first = html.escape(name.split()[0] if name.split() else name)
    return send(to, "Welcome to Kad AI", _layout(f"Welcome, {first}!", [
        "Your Kad AI account is ready. You can now see all your orders in one place.",
        "Try the AI assistant: ask for <em>fruits within ₹300</em> or <em>compare apples and oranges</em>.",
    ]))


def send_newsletter_confirmation(to: str) -> bool:
    return send(to, "You're on the Kad AI list", _layout("Thanks for subscribing!", [
        "You'll get seasonal picks, storage tips and weekly deals from Kad AI.",
        "Didn't sign up? Just ignore this email, or reply and we'll remove you.",
    ]))
