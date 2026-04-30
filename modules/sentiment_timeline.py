"""M02 — Sentiment Timeline: monthly sentiment with news event overlay."""

import logging

import pandas as pd

from database.db import query_df

logger = logging.getLogger(__name__)

_SENTIMENT_SQL = """
    SELECT
        strftime('%Y-%m', date) AS month,
        sentiment_score
    FROM processed_reviews
    WHERE competitor_name = ?
    ORDER BY date ASC
"""

_NEWS_SQL = """
    SELECT
        strftime('%Y-%m', date) AS month,
        review_text             AS headline,
        sentiment_score
    FROM processed_reviews
    WHERE competitor_name = ?
      AND source = 'newsapi'
      AND date BETWEEN ? AND ?
    ORDER BY sentiment_score ASC
"""

_EMPTY_COLS = [
    "month", "competitor", "avg_sentiment",
    "stddev", "review_count", "top_event", "event_url",
]


def build_timeline(competitor: str, months: int = 18) -> pd.DataFrame:
    """Aggregate sentiment by month and join the worst news event per month.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        months: How many months of history to include (newest N months).

    Returns:
        DataFrame with columns: month, competitor, avg_sentiment, stddev,
        review_count, top_event (str | None), event_url (always None —
        URL is not stored in the current schema).
    """
    df = query_df(_SENTIMENT_SQL, (competitor,))
    if df.empty:
        return pd.DataFrame(columns=_EMPTY_COLS)

    # Select the newest `months` calendar months available in the data
    all_months = sorted(df["month"].unique())
    if months < len(all_months):
        cutoff = all_months[-months]
        df = df[df["month"] >= cutoff]

    agg = (
        df.groupby("month")["sentiment_score"]
        .agg(avg_sentiment="mean", stddev="std", review_count="count")
        .reset_index()
    )
    agg["stddev"] = agg["stddev"].fillna(0.0).round(4)
    agg["avg_sentiment"] = agg["avg_sentiment"].round(4)
    agg["competitor"] = competitor

    # Overlay news events
    start = agg["month"].min() + "-01"
    end = agg["month"].max() + "-31"
    events = fetch_news_events(competitor, (start, end))
    event_map: dict[str, str] = {e["month"]: e["headline"] for e in events}

    agg["top_event"] = agg["month"].map(event_map)
    agg["event_url"] = None  # URL column not in current DB schema

    return agg[_EMPTY_COLS]


def fetch_news_events(competitor: str, date_range: tuple[str, str]) -> list[dict]:
    """Return the most negative-sentiment news headline per month in the date range.

    Reads newsapi-sourced records already stored in processed_reviews.

    Args:
        competitor: Competitor name.
        date_range: (start_date, end_date) in ISO 8601 format (YYYY-MM-DD).

    Returns:
        List of dicts with keys: month (YYYY-MM), headline (str),
        url (None), sentiment_score (float).
    """
    df = query_df(_NEWS_SQL, (competitor, date_range[0], date_range[1]))
    if df.empty:
        return []

    # Already sorted ascending by sentiment_score — first row per month = worst
    worst_per_month = (
        df.sort_values("sentiment_score")
        .groupby("month", sort=False)
        .first()
        .reset_index()
    )

    return [
        {
            "month": str(row["month"]),
            "headline": str(row["headline"]),
            "url": None,
            "sentiment_score": float(row["sentiment_score"]),
        }
        for _, row in worst_per_month.iterrows()
    ]
