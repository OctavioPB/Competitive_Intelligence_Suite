"""Sentiment scoring: VADER baseline + sentence-transformer embedding score."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def score_sentiment(text: str) -> dict[str, float]:
    """Compute sentiment score for a single review text.

    Combines VADER compound score with a sentence-transformer cosine
    similarity against positive/negative anchor embeddings.

    Args:
        text: Raw review or post text.

    Returns:
        Dict with keys: vader_score (float), embedding_score (float),
        sentiment_score (float, weighted average in [-1, 1]).
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")


def compute_sentiment_delta(competitor: str, window_days: int = 30) -> pd.DataFrame:
    """Compute per-review sentiment delta vs the prior window average.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.
        window_days: Rolling window length in days for the baseline average.

    Returns:
        DataFrame with columns: review_id, sentiment_score, sentiment_delta.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")
