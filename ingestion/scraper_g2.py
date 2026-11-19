"""Scrape product reviews from G2 for a given competitor.

G2 renders reviews with JavaScript and sits behind DataDome, so a plain HTTP
request almost never sees a review. The scraper therefore:

1. fetches the page as plain HTML, then — if Playwright is installed — in
   headless Chromium (``ingestion.browser.fetch_html``);
2. reads reviews from schema.org JSON-LD first, CSS selectors second;
3. when DataDome serves a challenge, raises ``ScrapingError`` naming it.

The browser does not try to hide that it is automated: if G2 blocks it, the
source is reported as blocked and ingestion carries on with the others.
"""

import logging
import random
import time
from typing import Any

from bs4 import BeautifulSoup

from config import CompetitorConfig

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.g2.com/products/{slug}/reviews"
_CARD_SELECTOR = ".paper.paper--white.paper--box"
_REQUEST_DELAY_MIN = 1.0
_REQUEST_DELAY_MAX = 2.0


class ScrapingError(Exception):
    """Raised when a scraping attempt fails and callers should fall back to other sources."""


def _css_reviews(html: str) -> list[dict[str, Any]]:
    """Legacy selector-based parser — kept as a fallback for pages without JSON-LD."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select(_CARD_SELECTOR):
        text_el = card.select_one(".formatted-text")
        if not text_el:
            continue
        rating_el = card.select_one("[data-rating]")
        try:
            rating = float(rating_el["data-rating"]) if rating_el else None
        except (KeyError, ValueError):
            rating = None
        date_el = card.select_one("time")
        author_el = card.select_one(".user-name")
        helpful_el = card.select_one(".helpful-count")
        try:
            helpful = int(helpful_el.get_text(strip=True)) if helpful_el else 0
        except ValueError:
            helpful = 0
        rows.append({
            "text": text_el.get_text(separator=" ", strip=True),
            "rating": rating,
            "date": date_el.get("datetime", "")[:10] if date_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
            "helpful_count": helpful,
        })
    return rows


def parse_reviews(html: str) -> list[dict[str, Any]]:
    """Reviews on one G2 page as {text, rating, date, author[, helpful_count]}."""
    from ingestion.structured_reviews import jsonld_reviews

    return jsonld_reviews(html) or _css_reviews(html)


def scrape_reviews(competitor: CompetitorConfig, max_pages: int = 5) -> list[dict[str, Any]]:
    """Scrape reviews from G2 for a single competitor.

    Waits a randomised 1–2 s between pages.

    Returns:
        List of review dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.

    Raises:
        ScrapingError: The first page is blocked or shows no reviews.
    """
    from ingestion.browser import FetchError, fetch_html

    slug = competitor["g2_slug"]
    name = competitor["name"]
    reviews: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        url = f"{_BASE_URL.format(slug=slug)}?page={page}"
        try:
            fetched = fetch_html(url, lambda html: bool(parse_reviews(html)), wait_for=_CARD_SELECTOR)
        except FetchError as exc:
            if page == 1:
                raise ScrapingError(f"G2 gave no reviews for {name}: {exc}") from exc
            break

        for r in parse_reviews(fetched.html):
            reviews.append({
                "source": "g2",
                "competitor_name": name,
                "review_text": r["text"],
                "rating": r["rating"],
                "date": r["date"],
                "author_id": r["author"],
                "helpful_count": r.get("helpful_count", 0),
            })
        time.sleep(random.uniform(_REQUEST_DELAY_MIN, _REQUEST_DELAY_MAX))

    if not reviews:
        raise ScrapingError(f"G2 scraper returned 0 reviews for {name}.")

    logger.info("G2: scraped %d reviews for %s", len(reviews), name)
    return reviews
