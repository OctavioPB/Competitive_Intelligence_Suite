"""Scrape product reviews from G2 for a given competitor."""

import logging
import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import CompetitorConfig

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.g2.com/products/{slug}/reviews"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_REQUEST_DELAY_MIN = 1.0
_REQUEST_DELAY_MAX = 2.0


class ScrapingError(Exception):
    """Raised when a scraping attempt fails and callers should fall back to fixtures."""


def scrape_reviews(competitor: CompetitorConfig, max_pages: int = 10) -> list[dict[str, Any]]:
    """Scrape reviews from G2 for a single competitor.

    Respects robots.txt intent by including a randomised 1–2 s delay between
    page requests.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        max_pages: Maximum number of paginated result pages to fetch.

    Returns:
        List of review dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.

    Raises:
        ScrapingError: If the first request is blocked or returns no reviews.
    """
    slug = competitor["g2_slug"]
    name = competitor["name"]
    reviews: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        url = f"{_BASE_URL.format(slug=slug)}?page={page}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
        except requests.RequestException as exc:
            raise ScrapingError(f"G2 request failed for {name}: {exc}") from exc

        if resp.status_code in (403, 429):
            raise ScrapingError(
                f"G2 returned {resp.status_code} for {name} — likely rate-limited."
            )
        if resp.status_code != 200:
            logger.warning("G2 returned %s for %s page %d", resp.status_code, name, page)
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".paper.paper--white.paper--box")

        if not cards:
            # G2 may render reviews via JavaScript — no cards on first page means blocked
            if page == 1:
                raise ScrapingError(
                    f"G2 returned no review cards for {name} — page may be JS-rendered."
                )
            break

        for card in cards:
            text_el = card.select_one(".formatted-text")
            if not text_el:
                continue
            review_text = text_el.get_text(separator=" ", strip=True)

            # Rating: G2 uses data-rating or star icons
            rating_el = card.select_one("[data-rating]")
            rating = float(rating_el["data-rating"]) if rating_el else None

            date_el = card.select_one("time")
            date = date_el.get("datetime", "")[:10] if date_el else ""

            author_el = card.select_one(".user-name")
            author_id = author_el.get_text(strip=True) if author_el else ""

            helpful_el = card.select_one(".helpful-count")
            try:
                helpful_count = int(helpful_el.get_text(strip=True)) if helpful_el else 0
            except ValueError:
                helpful_count = 0

            reviews.append(
                {
                    "source": "g2",
                    "competitor_name": name,
                    "review_text": review_text,
                    "rating": rating,
                    "date": date,
                    "author_id": author_id,
                    "helpful_count": helpful_count,
                }
            )

        time.sleep(random.uniform(_REQUEST_DELAY_MIN, _REQUEST_DELAY_MAX))

    if not reviews:
        raise ScrapingError(f"G2 scraper returned 0 reviews for {name}.")

    logger.info("G2: scraped %d reviews for %s", len(reviews), name)
    return reviews
