"""Scrape reviews from Trustpilot for a given competitor."""

import logging
import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import CompetitorConfig
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.trustpilot.com/review/{slug}"
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


def scrape_reviews(competitor: CompetitorConfig, max_pages: int = 10) -> list[dict[str, Any]]:
    """Scrape reviews from Trustpilot for a single competitor.

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
    slug = competitor["trustpilot_slug"]
    name = competitor["name"]
    reviews: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        url = f"{_BASE_URL.format(slug=slug)}?page={page}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
        except requests.RequestException as exc:
            raise ScrapingError(f"Trustpilot request failed for {name}: {exc}") from exc

        if resp.status_code in (403, 429):
            raise ScrapingError(
                f"Trustpilot returned {resp.status_code} for {name} — likely rate-limited."
            )
        if resp.status_code != 200:
            logger.warning("Trustpilot returned %s for %s page %d", resp.status_code, name, page)
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("[data-service-review-card-paper]")

        if not cards:
            if page == 1:
                raise ScrapingError(
                    f"Trustpilot returned no review cards for {name}."
                )
            break

        for card in cards:
            body_el = card.select_one("[data-service-review-text-typography]")
            if not body_el:
                continue
            review_text = body_el.get_text(separator=" ", strip=True)

            # Trustpilot star rating stored as data attribute on the rating element
            star_el = card.select_one("[data-rating-typography]")
            if not star_el:
                star_el = card.select_one("img[alt*='Rated']")
            rating: float | None = None
            if star_el:
                try:
                    rating = float(star_el.get("alt", "").split()[1])
                except (IndexError, ValueError):
                    pass

            date_el = card.select_one("time")
            date = date_el.get("datetime", "")[:10] if date_el else ""

            author_el = card.select_one("[data-consumer-name-typography]")
            author_id = author_el.get_text(strip=True) if author_el else ""

            reviews.append(
                {
                    "source": "trustpilot",
                    "competitor_name": name,
                    "review_text": review_text,
                    "rating": rating,
                    "date": date,
                    "author_id": author_id,
                    "helpful_count": 0,  # Trustpilot does not expose helpful counts
                }
            )

        time.sleep(random.uniform(_REQUEST_DELAY_MIN, _REQUEST_DELAY_MAX))

    if not reviews:
        raise ScrapingError(f"Trustpilot scraper returned 0 reviews for {name}.")

    logger.info("Trustpilot: scraped %d reviews for %s", len(reviews), name)
    return reviews
