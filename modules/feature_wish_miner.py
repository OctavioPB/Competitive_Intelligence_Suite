"""M03 — Feature Wish Miner: cluster feature requests and flag own-product coverage."""

import json
import logging
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from database.db import query_df
from utils.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

_CLUSTER_THRESHOLD = 0.80   # cosine similarity required to merge into existing cluster
_OWN_FEATURE_THRESHOLD = 0.45  # cosine similarity to flag own-product coverage

_WISH_SQL = """
    SELECT wish_phrases
    FROM processed_reviews
    WHERE competitor_name = ?
      AND wish_phrases IS NOT NULL
      AND wish_phrases != '[]'
"""

_WISH_COLUMNS = ["wish_phrase_cluster", "count", "sample_quotes"]


def _get_model() -> Any:
    """Return the shared sentence-transformer (loaded once per process)."""
    return get_embedding_model()


def _encode(texts: list[str]) -> np.ndarray:
    return _get_model().encode(texts, convert_to_numpy=True, normalize_embeddings=True)


# Embedding is the expensive step (hundreds of ms per request on CPU). Both
# helpers are keyed on the exact input text, so the cache can never serve stale
# results: new reviews produce a different key.
@lru_cache(maxsize=32)
def _cluster_phrases(phrases: tuple[str, ...]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Greedy-cluster phrases; returns ((seed, members), ...) sorted by size desc.

    Each phrase joins the first cluster whose seed embedding has cosine
    similarity ≥ threshold (dot product of L2-normalised vectors), else it
    seeds a new cluster.
    """
    embeddings = _encode(list(phrases))

    seed_embs = np.empty_like(embeddings)   # rows [0, n_clusters) are in use
    members: list[list[str]] = []

    for phrase, emb in zip(phrases, embeddings):
        n = len(members)
        if n:
            hits = np.flatnonzero(seed_embs[:n] @ emb >= _CLUSTER_THRESHOLD)
            if hits.size:
                members[int(hits[0])].append(phrase)
                continue
        seed_embs[n] = emb
        members.append([phrase])

    members.sort(key=len, reverse=True)  # stable: ties keep first-seen order
    return tuple((m[0], tuple(m)) for m in members)


@lru_cache(maxsize=32)
def _best_feature_matches(
    wishes: tuple[str, ...],
    features: tuple[str, ...],
) -> tuple[tuple[int, float], ...]:
    """For each wish return (index of the closest feature, cosine similarity)."""
    sim_matrix = _encode(list(wishes)) @ _encode(list(features)).T
    best_idx = sim_matrix.argmax(axis=1)
    return tuple((int(i), float(sim_matrix[row, i])) for row, i in enumerate(best_idx))


def extract_wishes(competitor: str) -> pd.DataFrame:
    """Extract and cluster feature wish phrases from competitor reviews.

    Args:
        competitor: Competitor name matching processed_reviews.competitor_name.

    Returns:
        DataFrame with columns: wish_phrase_cluster (str, the seed phrase),
        count (int, total mentions), sample_quotes (list[str], up to 3 examples).
        Sorted by count descending.
    """
    df = query_df(_WISH_SQL, (competitor,))
    if df.empty:
        return pd.DataFrame(columns=_WISH_COLUMNS)

    all_phrases: list[str] = []
    for raw in df["wish_phrases"]:
        try:
            phrases = json.loads(raw) if isinstance(raw, str) else (raw or [])
            all_phrases.extend(p.strip() for p in phrases if p and p.strip())
        except (json.JSONDecodeError, TypeError, AttributeError):
            logger.warning("Could not parse wish_phrases value: %r", raw)
            continue

    if not all_phrases:
        return pd.DataFrame(columns=_WISH_COLUMNS)

    return pd.DataFrame(
        [
            {
                "wish_phrase_cluster": seed,
                "count": len(members),
                "sample_quotes": list(members[:3]),
            }
            for seed, members in _cluster_phrases(tuple(all_phrases))
        ]
    )


def flag_own_features(
    wish_df: pd.DataFrame,
    own_feature_list: list[str],
) -> pd.DataFrame:
    """Add coverage columns: does our product already address each wish cluster?

    Uses sentence-transformer cosine similarity between each wish cluster label
    and each entry in own_feature_list. A cluster is flagged as covered when
    the best match exceeds _OWN_FEATURE_THRESHOLD.

    Args:
        wish_df: Output of extract_wishes().
        own_feature_list: List of feature strings (typically config.OWN_FEATURES).

    Returns:
        wish_df copy with two additional columns:
        your_product_has_it (bool), matched_feature (str | None).
    """
    wish_df = wish_df.copy()

    if wish_df.empty or not own_feature_list:
        wish_df["your_product_has_it"] = False
        wish_df["matched_feature"] = None
        return wish_df

    matches = _best_feature_matches(
        tuple(wish_df["wish_phrase_cluster"].tolist()),
        tuple(own_feature_list),
    )

    wish_df["your_product_has_it"] = [sim >= _OWN_FEATURE_THRESHOLD for _, sim in matches]
    wish_df["matched_feature"] = [
        own_feature_list[i] if sim >= _OWN_FEATURE_THRESHOLD else None
        for i, sim in matches
    ]

    return wish_df
