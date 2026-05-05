"""M01 — Pain Point Radar: rank competitor pain points by severity and trend."""

import logging
from datetime import timedelta

import pandas as pd

from database.db import query_df

logger = logging.getLogger(__name__)

_PAIN_SQL = """
    SELECT
        topic_label,
        topic_cluster,
        COUNT(*)                AS mention_count,
        AVG(sentiment_score)    AS avg_sentiment,
        MAX(date)               AS last_seen
    FROM processed_reviews
    WHERE competitor_name = ?
      AND topic_label NOT IN ('misc', 'insufficient_data')
      AND topic_cluster >= 0
    GROUP BY topic_label, topic_cluster
    ORDER BY AVG(sentiment_score) ASC
    LIMIT ?
"""

_ANCHOR_SQL = "SELECT MAX(date) FROM processed_reviews"

_TREND_SQL = """
    SELECT
        SUM(CASE WHEN date >= ? THEN 1 ELSE 0 END)              AS current_count,
        SUM(CASE WHEN date >= ? AND date < ?  THEN 1 ELSE 0 END) AS prior_count
    FROM processed_reviews
    WHERE topic_cluster = ?
"""

_RISING_THRESHOLD = 0.10   # > 10% increase → rising
_DECLINING_THRESHOLD = 0.10  # > 10% decrease → declining

_TREND_ICONS = {"rising": "", "stable": "", "declining": ""}


def compute_trend(topic_id: int, window_days: int = 30) -> str:
    """Compare mention volume in the last window vs the prior equivalent window.

    Uses the global max date in processed_reviews as the anchor so the result
    is meaningful with both live and fixture data.

    Args:
        topic_id: BERTopic cluster id (topic_cluster column).
        window_days: Length of each comparison window in days.

    Returns:
        "rising" if mention count increased > 10%, "declining" if decreased
        > 10%, "stable" otherwise.
    """
    anchor_raw = query_df(_ANCHOR_SQL).iloc[0, 0]
    if not anchor_raw:
        return "stable"

    anchor = pd.Timestamp(anchor_raw)
    current_start = (anchor - timedelta(days=window_days)).strftime("%Y-%m-%d")
    prior_start = (anchor - timedelta(days=2 * window_days)).strftime("%Y-%m-%d")
    prior_end = current_start

    row = query_df(_TREND_SQL, (current_start, prior_start, prior_end, topic_id))
    if row.empty:
        return "stable"

    current_count = int(row.iloc[0]["current_count"] or 0)
    prior_count = int(row.iloc[0]["prior_count"] or 0)

    if prior_count == 0:
        return "rising" if current_count > 0 else "stable"

    change = (current_count - prior_count) / prior_count
    if change > _RISING_THRESHOLD:
        return "rising"
    if change < -_DECLINING_THRESHOLD:
        return "declining"
    return "stable"


def get_pain_points(competitor: str, top_n: int = 10) -> pd.DataFrame:
    """Return the top N pain points for a competitor ranked by severity.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        top_n: Number of pain points to return.

    Returns:
        DataFrame with columns:
        topic_label (str), mention_count (int), avg_severity (float 0–1),
        trend_direction (str), trend_icon (str).
        Sorted by avg_severity descending (worst pain first).
        Returns empty DataFrame if no data exists for the competitor.
    """
    df = query_df(_PAIN_SQL, (competitor, top_n))

    if df.empty:
        logger.warning("[%s] No processed reviews found — run pipeline first.", competitor)
        return pd.DataFrame(
            columns=["topic_label", "mention_count", "avg_severity", "trend_direction", "trend_icon"]
        )

    # avg_severity: maps [-1, 1] sentiment → [1, 0] severity
    # (sentiment = -1 → severity = 1.0, i.e. maximum pain)
    df["avg_severity"] = ((1.0 - df["avg_sentiment"]) / 2.0).clip(0.0, 1.0).round(3)
    df["mention_count"] = df["mention_count"].astype(int)

    df["trend_direction"] = df["topic_cluster"].apply(
        lambda tc: compute_trend(int(tc))
    )
    df["trend_icon"] = df["trend_direction"].map(_TREND_ICONS)

    return df[
        ["topic_label", "mention_count", "avg_severity", "trend_direction", "trend_icon"]
    ].reset_index(drop=True)
