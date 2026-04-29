"""M01 — Pain Point Radar: rank competitor pain points by severity and trend."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def get_pain_points(competitor: str, top_n: int = 10) -> pd.DataFrame:
    """Return the top N pain points for a competitor ranked by severity.

    Queries processed_reviews, groups by topic_label, computes mention_count,
    avg_severity (inverse of avg sentiment_score), and trend_direction.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        top_n: Number of pain points to return.

    Returns:
        DataFrame with columns:
        topic_label (str), mention_count (int), avg_severity (float 0–1),
        trend_direction (str: "rising" | "stable" | "declining").
        Sorted by avg_severity descending.
    """
    raise NotImplementedError("Implement in Sprint 2 — Day 3")


def compute_trend(topic_id: int, window_days: int = 30) -> str:
    """Compare mention volume in the last window vs the prior equivalent window.

    Args:
        topic_id: BERTopic cluster id (topic_cluster column).
        window_days: Length of each comparison window in days.

    Returns:
        "rising" if mention count increased > 10%, "declining" if decreased > 10%,
        "stable" otherwise.
    """
    raise NotImplementedError("Implement in Sprint 2 — Day 3")
