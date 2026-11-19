"""Evidence drill-down: the individual reviews behind an aggregate metric."""

from datetime import date

import pandas as pd

from database.db import query_df

_SORTS = {
    "negative": "sentiment_score ASC, date DESC",
    "positive": "sentiment_score DESC, date DESC",
    "recent": "date DESC, sentiment_score ASC",
}

_REVIEW_COLUMNS = (
    "id, source, date, rating, sentiment_score, review_text, topic_label, is_synthetic"
)

_STATUS_SQL = """
    SELECT
        competitor_name,
        COUNT(*)          AS reviews,
        SUM(is_synthetic) AS synthetic,
        MAX(date)         AS latest_date
    FROM processed_reviews
    GROUP BY competitor_name
"""


def _month_bounds(month: str) -> tuple[str, str]:
    """'2025-12' → ('2025-12-01', '2026-01-01'); raises ValueError if malformed."""
    year, mon = (int(part) for part in month.split("-"))
    start = date(year, mon, 1)
    end = date(year + (mon == 12), mon % 12 + 1, 1)
    return start.isoformat(), end.isoformat()


def get_reviews(
    competitor: str,
    topic: str | None = None,
    month: str | None = None,
    sort: str = "negative",
    limit: int = 10,
) -> dict:
    """Return the reviews matching a competitor plus optional topic / month filter.

    Args:
        competitor: Competitor name.
        topic: Exact topic_label (as returned by the pain-points API).
        month: Calendar month as 'YYYY-MM' (as returned by the sentiment API).
        sort: 'negative' (worst first), 'positive' or 'recent'.
        limit: Maximum reviews to return.

    Returns:
        {"total": int, "reviews": [ {id, source, date, rating, sentiment_score,
        review_text, topic_label, is_synthetic}, ... ]}

    Raises:
        ValueError: If ``sort`` or ``month`` is malformed.
    """
    if sort not in _SORTS:
        raise ValueError(f"sort must be one of {sorted(_SORTS)}")

    where = ["competitor_name = :competitor"]
    params: dict = {"competitor": competitor, "limit": limit}

    if topic:
        where.append("topic_label = :topic")
        params["topic"] = topic
    if month:
        # Range filter instead of strftime() so idx_processed_comp_date is used.
        params["start"], params["end"] = _month_bounds(month)
        where.append("date >= :start AND date < :end")

    clause = " AND ".join(where)
    total = int(query_df(f"SELECT COUNT(*) AS n FROM processed_reviews WHERE {clause}", params).iloc[0]["n"])
    rows = query_df(
        f"SELECT {_REVIEW_COLUMNS} FROM processed_reviews WHERE {clause} "
        f"ORDER BY {_SORTS[sort]} LIMIT :limit",
        params,
    )

    reviews = [
        {
            "id": int(r.id),
            "source": str(r.source),
            "date": r.date if isinstance(r.date, str) else None,
            "rating": None if pd.isna(r.rating) else float(r.rating),
            "sentiment_score": float(r.sentiment_score),
            "review_text": str(r.review_text),
            "topic_label": r.topic_label if isinstance(r.topic_label, str) else None,
            "is_synthetic": bool(r.is_synthetic),
        }
        for r in rows.itertuples(index=False)
    ]
    return {"total": total, "reviews": reviews}


def get_data_status() -> dict[str, dict]:
    """Per-competitor review counts and how many of them are synthetic sample data."""
    df = query_df(_STATUS_SQL)
    return {
        str(r.competitor_name): {
            "reviews": int(r.reviews),
            "synthetic": int(r.synthetic or 0),
            "latest_date": r.latest_date if isinstance(r.latest_date, str) else None,
        }
        for r in df.itertuples(index=False)
    }
