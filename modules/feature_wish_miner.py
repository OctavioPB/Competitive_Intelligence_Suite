"""M03 — Feature Wish Miner: cluster feature requests and flag own-product coverage."""

import json
import logging
from typing import Any

import numpy as np
import pandas as pd

from config import OWN_FEATURES
from database.db import query_df

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_CLUSTER_THRESHOLD = 0.80   # cosine similarity required to merge into existing cluster
_OWN_FEATURE_THRESHOLD = 0.45  # cosine similarity to flag own-product coverage

_WISH_SQL = """
    SELECT wish_phrases
    FROM processed_reviews
    WHERE competitor_name = ?
      AND wish_phrases IS NOT NULL
      AND wish_phrases != '[]'
"""

# Module-level lazy cache: the model is ~90 MB and loads in ~2 s.
# Caching at module scope means the Streamlit page only loads it once.
_model: Any = None


def _get_model() -> Any:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore[import]
        _model = SentenceTransformer(_EMBEDDING_MODEL)
    return _model


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
        return pd.DataFrame(columns=["wish_phrase_cluster", "count", "sample_quotes"])

    all_phrases: list[str] = []
    for raw in df["wish_phrases"]:
        try:
            phrases = json.loads(raw) if isinstance(raw, str) else (raw or [])
            all_phrases.extend(p.strip() for p in phrases if p and p.strip())
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse wish_phrases value: %r", raw)
            continue

    if not all_phrases:
        return pd.DataFrame(columns=["wish_phrase_cluster", "count", "sample_quotes"])

    model = _get_model()
    embeddings: np.ndarray = model.encode(
        all_phrases, convert_to_numpy=True, normalize_embeddings=True
    )

    # Greedy clustering: each new phrase is assigned to the first cluster whose
    # seed embedding has cosine similarity ≥ threshold (dot product of L2-normalised
    # vectors equals cosine similarity).
    clusters: list[dict[str, Any]] = []

    for i, phrase in enumerate(all_phrases):
        emb = embeddings[i]
        assigned = False
        for cluster in clusters:
            sim = float(np.dot(emb, cluster["embedding"]))
            if sim >= _CLUSTER_THRESHOLD:
                cluster["members"].append(phrase)
                assigned = True
                break
        if not assigned:
            clusters.append({"seed": phrase, "embedding": emb, "members": [phrase]})

    rows = [
        {
            "wish_phrase_cluster": c["seed"],
            "count": len(c["members"]),
            "sample_quotes": c["members"][:3],
        }
        for c in sorted(clusters, key=lambda c: len(c["members"]), reverse=True)
    ]

    return pd.DataFrame(rows)


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

    model = _get_model()

    wish_embs: np.ndarray = model.encode(
        wish_df["wish_phrase_cluster"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    feature_embs: np.ndarray = model.encode(
        own_feature_list,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    sim_matrix: np.ndarray = wish_embs @ feature_embs.T  # (n_wishes, n_features)
    best_idx = sim_matrix.argmax(axis=1)
    best_sim = sim_matrix.max(axis=1)

    wish_df["your_product_has_it"] = best_sim >= _OWN_FEATURE_THRESHOLD
    wish_df["matched_feature"] = [
        own_feature_list[int(i)] if sim >= _OWN_FEATURE_THRESHOLD else None
        for i, sim in zip(best_idx, best_sim)
    ]

    return wish_df
