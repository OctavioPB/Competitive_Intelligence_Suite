"""Scrape reviews from a competitor's Capterra product page.

Configure ``capterra_url`` per competitor (the product's reviews page). Reviews
are read from schema.org JSON-LD. Capterra sits behind Cloudflare; when the
challenge page is served instead of reviews, ``ScrapingError`` says so and
ingestion continues with the other sources.
"""

from __future__ import annotations

import logging
from typing import Any

from config import CompetitorConfig
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)


def scrape_reviews(competitor: CompetitorConfig) -> list[dict[str, Any]]:
    """Fetch the reviews on the competitor's Capterra page.

    Raises:
        ScrapingError: No URL configured, the page was blocked, or it had no reviews.
    """
    from ingestion.browser import FetchError, fetch_html
    from ingestion.structured_reviews import jsonld_reviews

    name = competitor["name"]
    url = competitor.get("capterra_url")
    if not url:
        raise ScrapingError(f"No capterra_url configured for {name}.")

    try:
        page = fetch_html(url, lambda html: bool(jsonld_reviews(html)))
    except FetchError as exc:
        raise ScrapingError(f"Capterra gave no reviews for {name}: {exc}") from exc

    reviews = [
        {
            "source": "capterra",
            "competitor_name": name,
            "review_text": r["text"],
            "rating": r["rating"],
            "date": r["date"],
            "author_id": r["author"],
            "helpful_count": 0,
        }
        for r in jsonld_reviews(page.html)
    ]
    logger.info("Capterra: scraped %d reviews for %s", len(reviews), name)
    return reviews
