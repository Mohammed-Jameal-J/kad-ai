"""Web search through Serper (https://serper.dev) for general produce questions: recipes, storage,
ripeness, season. One POST with httpx, no SDK.

Results are untrusted data: they are only summarised (with sources shown), never used for prices,
stock or nutrition numbers, which come only from our database. Two caps keep the free quota safe:
SEARCH_DAILY_LIMIT for all visitors together and SEARCH_PER_IP_PER_HOUR per visitor.
"""
import logging

import httpx

from app.core.config import settings
from app.core.ratelimit import RateLimiter

logger = logging.getLogger("kadai.search")
DAILY = RateLimiter(limit=settings.search_daily_limit, window_seconds=24 * 3600)
PER_IP = RateLimiter(limit=settings.search_per_ip_per_hour, window_seconds=3600)

# A question has to be about food to be searched; "who won the match?" never reaches Serper.
FOOD_TOPICS = {
    "recipe", "recipes", "cook", "cooking", "dish", "curry", "salad", "juice", "smoothie", "chutney",
    "pickle", "dessert", "breakfast", "snack", "ripe", "ripen", "ripening", "season", "seasonal",
    "storage", "store", "keep", "fresh", "freshness", "wash", "peel", "cut", "grow", "harvest",
    "energy", "advantage", "advantages", "benefit", "benefits", "healthy", "health", "eat", "eating",
    "fruit", "fruits", "vegetable", "vegetables", "veggies", "sweet", "sour",
}


class SearchUnavailable(Exception):
    pass


def available() -> bool:
    return bool(settings.serper_api_key)


def search(query: str, client: str, transport: httpx.BaseTransport | None = None) -> list[dict]:
    """Up to 4 results as {title, url, snippet}. Raises SearchUnavailable when off, over a cap or failing."""
    if not settings.serper_api_key:
        raise SearchUnavailable("Web search is not set up.")
    if DAILY.retry_after("all") or PER_IP.retry_after(client):
        raise SearchUnavailable("Web search limit reached for now.")
    DAILY.record("all")
    PER_IP.record(client)
    try:
        with httpx.Client(timeout=10, transport=transport) as http:
            r = http.post("https://google.serper.dev/search",
                          headers={"X-API-KEY": settings.serper_api_key},
                          json={"q": query, "gl": "in", "num": 6})
        r.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("serper failed: %s", type(e).__name__)  # never log the query
        raise SearchUnavailable("Web search is not reachable right now.")
    results = [
        {"title": o.get("title", "")[:120], "url": o["link"], "snippet": o.get("snippet", "")[:400]}
        for o in r.json().get("organic", [])
        if str(o.get("link", "")).startswith("https://")  # no http:, javascript: or other schemes
    ]
    return results[:4]
