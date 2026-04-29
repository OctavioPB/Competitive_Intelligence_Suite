"""BERTopic training and inference for review topic clustering."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_MIN_REVIEWS_FOR_TRAINING = 100
_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def train_topics(competitor: str) -> None:
    """Train a BERTopic model on all reviews for the given competitor.

    Skips training and logs a warning if fewer than _MIN_REVIEWS_FOR_TRAINING
    reviews exist; those reviews will receive topic_label='insufficient_data'.

    Args:
        competitor: Competitor name matching reviews.competitor_name.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")


def assign_topics(texts: list[str]) -> list[dict[str, int | str]]:
    """Assign topic cluster and label to each text using the trained model.

    Args:
        texts: List of review text strings.

    Returns:
        List of dicts with keys: topic_cluster (int), topic_label (str).
        topic_cluster == -1 indicates BERTopic outlier.
    """
    raise NotImplementedError("Implement in Sprint 1 — Day 2")
