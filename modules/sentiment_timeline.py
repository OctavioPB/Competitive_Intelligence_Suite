"""M02 — Sentiment Timeline: monthly sentiment with news event overlay."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_timeline(competitor: str, months: int = 18) -> pd.DataFrame:
    """Aggregate sentiment by month and join news events.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        months: How many months of history to include.

    Returns:
        DataFrame with columns:
        month (str, YYYY-MM), competitor (str), avg_sentiment (float),
        stddev (float), review_count (int), top_event (str | None),
        event_url (str | None).
    """
    raise NotImplementedError("Implement in Sprint 3 — Day 6")


def fetch_news_events(competitor: str, date_range: tuple[str, str]) -> list[dict]:
    """Return the top negative-sentiment news article per month in the date range.

    Reads NewsAPI records already stored in the reviews table (source='newsapi').

    Args:
        competitor: Competitor name.
        date_range: Tuple of (start_date, end_date) in ISO 8601 format.

    Returns:
        List of dicts with keys: month, headline, url, sentiment_score.
    """
    raise NotImplementedError("Implement in Sprint 3 — Day 6")
