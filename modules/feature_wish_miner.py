"""M03 — Feature Wish Miner: cluster feature requests and flag own-product coverage."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

_WISH_PATTERNS = [
    r"I wish",
    r"would be nice if",
    r"please add",
    r"missing",
    r"need[s]?\s+(?:a|an|the)?",
    r"lack[s]?\s+(?:a|an|the)?",
    r"should have",
    r"feature request",
]

_CLUSTER_SIMILARITY_THRESHOLD = 0.80


def extract_wishes(competitor: str) -> pd.DataFrame:
    """Extract and cluster feature wish phrases from competitor reviews.

    Applies regex patterns to wish_phrases column, then clusters similar
    phrases using sentence-transformer cosine similarity > _CLUSTER_SIMILARITY_THRESHOLD.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.

    Returns:
        DataFrame with columns:
        wish_phrase_cluster (str), count (int), sample_quotes (list[str]).
    """
    raise NotImplementedError("Implement in Sprint 3 — Day 7")


def flag_own_features(
    wish_df: pd.DataFrame,
    own_feature_list: list[str],
) -> pd.DataFrame:
    """Add a column indicating whether each wish cluster is covered by our product.

    Uses sentence-transformer cosine similarity between wish_phrase_cluster
    and each entry in own_feature_list.

    Args:
        wish_df: Output of extract_wishes().
        own_feature_list: List of feature strings from config.OWN_FEATURES.

    Returns:
        wish_df with two additional columns:
        your_product_has_it (bool), matched_feature (str | None).
    """
    raise NotImplementedError("Implement in Sprint 3 — Day 7")
