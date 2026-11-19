"""Fetch customer reviews of a competitor's iOS app from Apple's public RSS feed.

https://itunes.apple.com/<country>/rss/customerreviews/page=<n>/id=<app>/sortBy=mostRecent/json

An official, unauthenticated feed: up to 10 pages × 50 of the most recent
reviews per country. Unlike G2 or Capterra it is not behind an anti-bot wall,
so it is the dependable source of rated reviews.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import CompetitorConfig
from ingestion.browser import USER_AGENT
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_FEED = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
_MAX_PAGES = 10                 # the feed stops at page 10
_DELAY = 0.5


def _label(entry: dict, key: str) -> str:
    value = entry.get(key) or {}
    return str(value.get("label", "")) if isinstance(value, dict) else ""


def parse_feed(payload: dict, competitor_name: str) -> list[dict[str, Any]]:
    """Turn one feed page into review rows (entries without a rating are app metadata)."""
    entries = (payload.get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):           # a page with one entry is not a list
        entries = [entries]
    rows = []
    for e in entries:
        if "im:rating" not in e:
            continue
        title, body = _label(e, "title").strip(), _label(e, "content").strip()
        text = f"{title}. {body}" if title and body and not body.startswith(title) else body or title
        if not text:
            continue
        try:
            rating: float | None = float(_label(e, "im:rating"))
        except ValueError:
            rating = None
        try:
            helpful = int(_label(e, "im:voteSum") or 0)
        except ValueError:
            helpful = 0
        author = ((e.get("author") or {}).get("name") or {}).get("label", "")
        rows.append({
            "source": "app_store",
            "competitor_name": competitor_name,
            "review_text": text,
            "rating": rating,
            "date": _label(e, "updated")[:10],
            "author_id": author,
            "helpful_count": max(helpful, 0),
        })
    return rows


def scrape_reviews(
    competitor: CompetitorConfig, max_pages: int = _MAX_PAGES, country: str = "us"
) -> list[dict[str, Any]]:
    """Fetch the most recent App Store reviews for the competitor's app.

    Raises:
        ScrapingError: No app id configured, the feed is unreachable, or it is empty.
    """
    app_id = competitor.get("app_store_id")
    name = competitor["name"]
    if not app_id:
        raise ScrapingError(f"No app_store_id configured for {name}.")

    reviews: list[dict[str, Any]] = []
    for page in range(1, min(max_pages, _MAX_PAGES) + 1):
        url = _FEED.format(country=country, page=page, app_id=app_id)
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        except requests.RequestException as exc:
            if page == 1:
                raise ScrapingError(f"App Store feed request failed for {name}: {exc}") from exc
            break
        if resp.status_code != 200:
            if page == 1:
                raise ScrapingError(f"App Store feed returned HTTP {resp.status_code} for {name}.")
            break
        rows = parse_feed(resp.json(), name)
        if not rows:
            break
        reviews.extend(rows)
        time.sleep(_DELAY)

    if not reviews:
        raise ScrapingError(f"App Store feed returned 0 reviews for {name} (app {app_id}).")
    logger.info("App Store: fetched %d reviews for %s", len(reviews), name)
    return reviews
