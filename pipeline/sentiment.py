"""Sentiment scoring: VADER + sentence-transformer embedding signal."""

import logging
import re
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

_VADER = SentimentIntensityAnalyzer()

# Transformer is optional — only loaded when sentence_transformers is available
_ST_MODEL_NAME = "all-MiniLM-L6-v2"
_POSITIVE_ANCHOR = "This product is excellent and I highly recommend it."
_NEGATIVE_ANCHOR = "This product is terrible and a complete waste of money."

# Weighted blend: VADER carries more weight because it's calibrated for reviews
_VADER_WEIGHT = 0.65
_TRANSFORMER_WEIGHT = 0.35

_WISH_PATTERNS: list[str] = [
    r"I wish\b[^.!?]*",
    r"[Ww]ould be nice if[^.!?]*",
    r"[Pp]lease add[^.!?]*",
    r"[Mm]issing[^.!?]{10,}",
    r"[Nn]eed[s]?\s+(?:a |an |the )?[a-z][^.!?]{10,}",
    r"[Ss]hould have[^.!?]*",
    r"[Ff]eature request[^.!?]*",
    r"[Ll]acking[^.!?]{10,}",
]
_WISH_RE = re.compile("|".join(_WISH_PATTERNS))


@lru_cache(maxsize=1)
def _load_transformer():
    """Lazy-load sentence-transformer model. Returns None if package unavailable."""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(_ST_MODEL_NAME)
        anchors = model.encode([_POSITIVE_ANCHOR, _NEGATIVE_ANCHOR], normalize_embeddings=True)
        return model, anchors
    except ImportError:
        logger.warning(
            "sentence_transformers not installed — using VADER-only sentiment scoring."
        )
        return None, None


def _transformer_score(text: str) -> float | None:
    """Return a transformer-based sentiment score in [-1, 1], or None on failure."""
    model, anchors = _load_transformer()
    if model is None:
        return None

    try:
        emb = model.encode([text], normalize_embeddings=True)[0]
        pos_sim = float(np.dot(emb, anchors[0]))
        neg_sim = float(np.dot(emb, anchors[1]))
        # Maps to [-1, 1]: positive anchor similarity dominates → positive score
        return float(np.clip(pos_sim - neg_sim, -1.0, 1.0))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Transformer scoring failed: %s", exc)
        return None


def score_sentiment(text: str) -> dict[str, Any]:
    """Compute sentiment score for a single review text.

    Combines VADER compound score with a sentence-transformer cosine
    similarity signal against positive/negative anchor embeddings.

    Args:
        text: Raw review or post text.

    Returns:
        Dict with keys:
        - vader_score (float, [-1, 1])
        - transformer_score (float | None, [-1, 1])
        - sentiment_score (float, [-1, 1]) — weighted blend
    """
    vader_score = float(_VADER.polarity_scores(text)["compound"])
    t_score = _transformer_score(text)

    if t_score is not None:
        combined = _VADER_WEIGHT * vader_score + _TRANSFORMER_WEIGHT * t_score
    else:
        combined = vader_score

    return {
        "vader_score": vader_score,
        "transformer_score": t_score,
        "sentiment_score": float(np.clip(combined, -1.0, 1.0)),
    }


def compute_sentiment_delta(
    scores_df: pd.DataFrame,
    window_days: int = 30,
) -> pd.Series:
    """Compute per-review sentiment delta vs the trailing 30-day average.

    Args:
        scores_df: DataFrame with columns 'date' (str ISO 8601) and
                   'sentiment_score' (float). Must be for a single competitor.
        window_days: Rolling window length in calendar days.

    Returns:
        Series of sentiment_delta values aligned with scores_df index.
        Reviews with no prior window data get delta = 0.0.
    """
    df = scores_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    # Rolling mean using a time-based window (requires DatetimeIndex)
    df = df.set_index("date")
    rolling_avg = (
        df["sentiment_score"]
        .rolling(window=f"{window_days}D", min_periods=1)
        .mean()
        .shift(1)   # shift so each row sees prior-window avg, not including itself
        .fillna(0.0)
    )
    df["sentiment_delta"] = df["sentiment_score"] - rolling_avg

    # Restore original index order
    df = df.reset_index()
    df = df.set_index(scores_df.sort_values("date").index)
    return df["sentiment_delta"].reindex(scores_df.index).fillna(0.0)


def extract_wish_phrases(text: str) -> list[str]:
    """Extract wish/feature-request phrases from review text using regex patterns.

    Args:
        text: Raw review text.

    Returns:
        List of matched wish phrase strings (stripped, length > 10).
    """
    matches = _WISH_RE.findall(text)
    return [m.strip() for m in matches if len(m.strip()) > 10]
