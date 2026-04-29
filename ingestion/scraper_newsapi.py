"""Fetch news articles mentioning a competitor via NewsAPI."""

import logging
from typing import Any

from newsapi import NewsApiClient

from config import CompetitorConfig

logger = logging.getLogger(__name__)

_MONTHS_DEFAULT = 18


def fetch_articles(
    competitor: CompetitorConfig,
    months: int = _MONTHS_DEFAULT,
) -> list[dict[str, Any]]:
    """Fetch news articles for a competitor covering the last N months.

    Uses NEWSAPI_KEY from the environment.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        months: How many months of history to fetch (max 1 month on free tier).

    Returns:
        List of article dicts with keys:
        source, competitor_name, review_text (= article body/description),
        rating (None), date, author_id (= source.name), helpful_count (0).
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 1")
