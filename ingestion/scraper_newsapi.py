"""Fetch news articles mentioning a competitor via NewsAPI."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

from config import CompetitorConfig
from ingestion.scraper_g2 import ScrapingError

logger = logging.getLogger(__name__)

_MONTHS_DEFAULT = 18
# NewsAPI free tier only provides articles from the last 30 days.
# Paid plans support up to 5 years. The scraper requests the full range
# and returns whatever the tier allows.


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
    from_date = (datetime.utcnow() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    to_date = datetime.utcnow().strftime("%Y-%m-%d")

    client = NewsApiClient(api_key=api_key)
    articles: list[dict[str, Any]] = []

    try:
        response = client.get_everything(
            q=name,
            from_param=from_date,
            to=to_date,
            language="en",
            sort_by="publishedAt",
            page_size=100,
        )
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
