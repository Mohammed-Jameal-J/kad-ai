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


def send(to: str, subject: str, body_html: str, reply_to: str | None = None) -> bool:
    if not settings.resend_api_key:
        logger.info("Email skipped, RESEND_API_KEY not set: %s", subject)
        return False
    try:
        r = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": body_html,
                  **({"reply_to": reply_to} if reply_to else {})},
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


def _button(label: str, url: str) -> str:
    return (f'<a href="{html.escape(url)}" style="display:inline-block;margin:0 8px 8px 0;background:#235e36;'
            f'color:#fff;padding:10px 18px;border-radius:999px;text-decoration:none">{html.escape(label)}</a>')


def _layout(heading: str, paragraphs: list[str], buttons: list[tuple[str, str]] | None = None) -> str:
    """Simple inline-styled HTML (email clients ignore stylesheets). Callers escape user text."""
    body = "".join(f'<p style="margin:0 0 14px;line-height:1.6">{p}</p>' for p in paragraphs)
    links = "".join(_button(label, url) for label, url in (buttons or [("Visit Kad AI", settings.site_url)]))
    return (
        '<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:24px;'
        'background:#faf0dc;border-radius:16px;color:#1f2a1f">'
        f'<h1 style="font-family:Georgia,serif;color:#235e36;font-size:24px;margin:0 0 16px">{heading}</h1>'
        f'{body}<p style="margin:16px 0 0">{links}</p>'
        '<p style="margin:20px 0 0;font-size:12px;color:#6b6b6b">Kad AI demo store, Coimbatore. '
        'Prices on the site are demonstration prices.</p></div>'
    )


def send_welcome(to: str, name: str) -> bool:
    first = html.escape(name.split()[0] if name.split() else name)
    return send(to, "Welcome to Kad AI", _layout(f"Welcome, {first}!", [
        "Your Kad AI account is ready. You can now see all your orders in one place.",
        "Try the AI assistant: ask for <em>fruits within ₹300</em> or <em>compare apples and oranges</em>.",
    ]))


OWNER_EMAIL = "mohammedjameal031@gmail.com"
GITHUB = "https://github.com/Mohammed-Jameal-J"
LINKEDIN = "https://www.linkedin.com/in/mohammed-jameal-j/"


def send_newsletter_confirmation(to: str) -> bool:
    return send(to, "Thanks for testing Kad AI", _layout("Thanks for testing Kad AI!", [
        "Thanks for trying my AI e-commerce website. Create a free account on the site to walk through "
        "the complete experience: AI assistant, cart and checkout.",
        "Need a website, AI work, automation or cyber security? Reply to this email or write to "
        f'<a href="mailto:{OWNER_EMAIL}" style="color:#235e36">{OWNER_EMAIL}</a>.',
        "Let's connect:",
    ], buttons=[("Sign up", f"{settings.site_url}/register"), ("LinkedIn", LINKEDIN), ("GitHub", GITHUB)]),
        reply_to=OWNER_EMAIL)  # the sender may be onboarding@resend.dev: replies must reach a real inbox
