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
_REQUEST_DELAY_MIN = 1.0
_REQUEST_DELAY_MAX = 2.0


def scrape_reviews(competitor: CompetitorConfig, max_pages: int = 10) -> list[dict[str, Any]]:
    """Scrape reviews from G2 for a single competitor.

    Respects robots.txt by including a randomised 1–2 s delay between requests.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        max_pages: Maximum number of paginated result pages to fetch.

    Returns:
        List of review dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 1")
