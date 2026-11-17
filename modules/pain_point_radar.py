"""M01 — Pain Point Radar: rank competitor pain points by severity and trend."""

import logging

import pandas as pd

from database.db import query_df

logger = logging.getLogger(__name__)

_TREND_WINDOW_DAYS = 30

# One round-trip: severity ranking plus the two trend windows per topic.
# Windows anchor on the competitor's own MAX(date) so fixture data keeps working
# and one competitor's activity never shifts another's trend.
_PAIN_SQL = """
    WITH anchor AS (
        SELECT MAX(date) AS d FROM processed_reviews WHERE competitor_name = ?
    )
    SELECT
        topic_label,
        topic_cluster,
        COUNT(*)                AS mention_count,
        AVG(sentiment_score)    AS avg_sentiment,
        MAX(date)               AS last_seen,
        SUM(CASE WHEN date >= date((SELECT d FROM anchor), ?) THEN 1 ELSE 0 END)
                                AS current_count,
        SUM(CASE WHEN date >= date((SELECT d FROM anchor), ?)
                  AND date <  date((SELECT d FROM anchor), ?) THEN 1 ELSE 0 END)
                                AS prior_count
    FROM processed_reviews
    WHERE competitor_name = ?
      AND topic_label NOT IN ('misc', 'insufficient_data')
      AND topic_cluster >= 0
    GROUP BY topic_label, topic_cluster
    ORDER BY AVG(sentiment_score) ASC
    LIMIT ?
"""

# Topic cluster ids are only unique within a competitor (one BERTopic model each),
# so the single-topic query is scoped by competitor when one is given.
_TREND_SQL = """
    WITH anchor AS (
        SELECT MAX(date) AS d FROM processed_reviews
        WHERE (:competitor IS NULL OR competitor_name = :competitor)
    )
    SELECT
        SUM(CASE WHEN date >= date((SELECT d FROM anchor), :cur) THEN 1 ELSE 0 END)
            AS current_count,
        SUM(CASE WHEN date >= date((SELECT d FROM anchor), :prior)
                  AND date <  date((SELECT d FROM anchor), :cur) THEN 1 ELSE 0 END)
            AS prior_count
    FROM processed_reviews
    WHERE topic_cluster = :topic
      AND (:competitor IS NULL OR competitor_name = :competitor)
"""

_RISING_THRESHOLD = 0.10   # > 10% increase → rising
_DECLINING_THRESHOLD = 0.10  # > 10% decrease → declining

_COLUMNS = ["topic_label", "mention_count", "avg_severity", "trend_direction"]


def _classify_trend(current_count: int, prior_count: int) -> str:
    """Map two window counts to 'rising' | 'stable' | 'declining'."""
    if prior_count == 0:
        return "rising" if current_count > 0 else "stable"

    change = (current_count - prior_count) / prior_count
    if change > _RISING_THRESHOLD:
        return "rising"
    if change < -_DECLINING_THRESHOLD:
        return "declining"
    return "stable"


def _count(value) -> int:
    """SQL SUM() yields NULL (None/NaN) on empty sets — treat as zero."""
    return 0 if pd.isna(value) else int(value)


def compute_trend(
    topic_id: int,
    window_days: int = _TREND_WINDOW_DAYS,
    competitor: str | None = None,
) -> str:
    """Compare mention volume in the last window vs the prior equivalent window.

    Anchors on MAX(date) in processed_reviews (scoped to the competitor when
    given) so the result is meaningful with both live and fixture data.

    Args:
        topic_id: BERTopic cluster id (topic_cluster column).
        window_days: Length of each comparison window in days.
        competitor: Competitor the cluster belongs to. Cluster ids repeat across
            competitors, so always pass this outside of single-competitor DBs.

    Returns:
        "rising" if mention count increased > 10%, "declining" if decreased
        > 10%, "stable" otherwise.
    """
    row = query_df(
        _TREND_SQL,
        {
            "competitor": competitor,
            "topic": topic_id,
            "cur": f"-{window_days} days",
            "prior": f"-{2 * window_days} days",
        },
    )
    if row.empty:
        return "stable"

    return _classify_trend(
        _count(row.iloc[0]["current_count"]),
        _count(row.iloc[0]["prior_count"]),
    )


def get_pain_points(competitor: str, top_n: int = 10) -> pd.DataFrame:
    """Return the top N pain points for a competitor ranked by severity.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        top_n: Number of pain points to return.

    Returns:
        DataFrame with columns:
        topic_label (str), mention_count (int), avg_severity (float 0–1),
        trend_direction (str).
        Sorted by avg_severity descending (worst pain first).
        Returns empty DataFrame if no data exists for the competitor.
    """
    cur = f"-{_TREND_WINDOW_DAYS} days"
    prior = f"-{2 * _TREND_WINDOW_DAYS} days"
    df = query_df(_PAIN_SQL, (competitor, cur, prior, cur, competitor, top_n))

    if df.empty:
        logger.warning("[%s] No processed reviews found — run pipeline first.", competitor)
        return pd.DataFrame(columns=_COLUMNS)

    # avg_severity: maps [-1, 1] sentiment → [1, 0] severity
    # (sentiment = -1 → severity = 1.0, i.e. maximum pain)
    df["avg_severity"] = ((1.0 - df["avg_sentiment"]) / 2.0).clip(0.0, 1.0).round(3)
    df["mention_count"] = df["mention_count"].astype(int)
    df["trend_direction"] = [
        _classify_trend(_count(c), _count(p))
        for c, p in zip(df["current_count"], df["prior_count"])
    ]

    return df[_COLUMNS].reset_index(drop=True)
