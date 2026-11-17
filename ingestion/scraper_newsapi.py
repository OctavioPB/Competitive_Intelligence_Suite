"""Fetch news articles mentioning a competitor via NewsAPI."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

from config import CompetitorConfig
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_MONTHS_DEFAULT = 18
# NewsAPI's free tier only serves the last ~30 days and rejects older `from`
# dates outright; paid plans go back years. The scraper asks for the full range
# first and retries with the free-tier window if that is refused.
_FREE_TIER_DAYS = 29


def fetch_articles(
    competitor: CompetitorConfig,
    months: int = _MONTHS_DEFAULT,
) -> list[dict[str, Any]]:
    """Fetch news articles for a competitor covering the last N months.

    Uses NEWSAPI_KEY from the environment.

    Args:
        competitor: Competitor config dict from config.COMPETITORS.
        months: How many months of history to request.

    Returns:
        List of article dicts with keys:
        source, competitor_name, review_text, rating, date, author_id, helpful_count.

    Raises:
        ScrapingError: If NEWSAPI_KEY is missing or the API call fails.
    """
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        raise ScrapingError("NEWSAPI_KEY must be set to use the NewsAPI scraper.")

    name = competitor["name"]
    now = datetime.now(timezone.utc)
    to_date = now.strftime("%Y-%m-%d")

    client = NewsApiClient(api_key=api_key)
    articles: list[dict[str, Any]] = []

    def _fetch(days_back: int) -> dict:
        return client.get_everything(
            q=name,
            from_param=(now - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            to=to_date,
            language="en",
            sort_by="publishedAt",
            page_size=100,
        )

    try:
        try:
            response = _fetch(months * 30)
        except NewsAPIException as exc:
            if months * 30 <= _FREE_TIER_DAYS:
                raise
            logger.info(
                "NewsAPI refused %d-month range for %s (%s) — retrying with last %d days.",
                months, name, exc, _FREE_TIER_DAYS,
            )
            response = _fetch(_FREE_TIER_DAYS)
    except NewsAPIException as exc:
        raise ScrapingError(f"NewsAPI error for {name}: {exc}") from exc

    for article in response.get("articles", []):
        text = " ".join(
            filter(None, [article.get("title"), article.get("description"), article.get("content")])
        ).strip()
        if not text:
            continue

        pub_date = (article.get("publishedAt") or "")[:10]
        source_name = (article.get("source") or {}).get("name", "")

        articles.append(
            {
                "source": "newsapi",
                "competitor_name": name,
                "review_text": text,
                "rating": None,
                "date": pub_date,
                "author_id": source_name,
                "helpful_count": 0,
            }
        )

    if not articles:
        raise ScrapingError(f"NewsAPI returned 0 articles for {name}.")

    logger.info("NewsAPI: fetched %d articles for %s", len(articles), name)
    return articles
