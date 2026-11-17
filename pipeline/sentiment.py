"""Sentiment scoring: VADER + sentence-transformer embedding signal."""

import logging
import re
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

_VADER = SentimentIntensityAnalyzer()

# Transformer is optional — only loaded when sentence_transformers is available
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
    """Lazy-load the shared model plus anchor embeddings. (None, None) if unavailable."""
    try:
        model = get_embedding_model()
    except ImportError:
        logger.warning(
            "sentence_transformers not installed — using VADER-only sentiment scoring."
        )
        return None, None

    anchors = model.encode([_POSITIVE_ANCHOR, _NEGATIVE_ANCHOR], normalize_embeddings=True)
    return model, anchors


def _transformer_scores(
    texts: list[str],
    embeddings: np.ndarray | None = None,
) -> np.ndarray | None:
    """Return transformer sentiment scores in [-1, 1] for all texts, or None on failure.

    Args:
        texts: Texts to score.
        embeddings: Optional pre-computed embeddings for ``texts`` (any norm) —
            lets the pipeline embed each review once and share the result.
    """
    model, anchors = _load_transformer()
    if model is None:
        return None

    try:
        if embeddings is None:
            embs = model.encode(texts, normalize_embeddings=True)
        else:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embs = embeddings / np.where(norms == 0, 1.0, norms)
        # Positive-anchor similarity minus negative-anchor similarity → [-1, 1]
        return np.clip(embs @ anchors[0] - embs @ anchors[1], -1.0, 1.0)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Transformer scoring failed: %s", exc)
        return None


def _transformer_score(text: str) -> float | None:
    """Return a transformer-based sentiment score in [-1, 1], or None on failure."""
    scores = _transformer_scores([text])
    return None if scores is None else float(scores[0])


def _blend(vader_score: float, t_score: float | None) -> dict[str, Any]:
    combined = (
        _VADER_WEIGHT * vader_score + _TRANSFORMER_WEIGHT * t_score
        if t_score is not None
        else vader_score
    )
    return {
        "vader_score": vader_score,
        "transformer_score": t_score,
        "sentiment_score": float(np.clip(combined, -1.0, 1.0)),
    }


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
    return _blend(vader_score, _transformer_score(text))


def score_sentiment_batch(
    texts: list[str],
    embeddings: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    """Score many texts at once — same output per item as score_sentiment().

    Encodes all texts in a single batched forward pass (or reuses
    ``embeddings`` when supplied), which is far faster than one call per text.

    Args:
        texts: Review texts.
        embeddings: Optional pre-computed sentence embeddings aligned with texts.

    Returns:
        List of score dicts, one per input text.
    """
    if not texts:
        return []

    t_scores = _transformer_scores(texts, embeddings)
    return [
        _blend(
            float(_VADER.polarity_scores(text)["compound"]),
            None if t_scores is None else float(t_scores[i]),
        )
        for i, text in enumerate(texts)
    ]


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
        Reviews with no prior window data — or with a missing/unparseable
        date — get delta = 0.0.
    """
    dates = pd.to_datetime(scores_df["date"], errors="coerce")
    scores = scores_df["sentiment_score"].astype(float)

    # Rolling time windows need a sorted DatetimeIndex without NaT. Carry the
    # original position alongside so results map back exactly, even when dates
    # tie or the input index has duplicates.
    valid = dates.notna().to_numpy()
    work = pd.DataFrame(
        {
            "pos": np.flatnonzero(valid),
            "score": scores.to_numpy()[valid],
        },
        index=pd.DatetimeIndex(dates.to_numpy()[valid]),
    ).sort_index(kind="stable")

    rolling_avg = (
        work["score"]
        .rolling(window=f"{window_days}D", min_periods=1)
        .mean()
        .shift(1)   # shift so each row sees prior-window avg, not including itself
        .fillna(0.0)
    )

    deltas = np.zeros(len(scores_df), dtype=float)
    deltas[work["pos"].to_numpy()] = (work["score"] - rolling_avg).to_numpy()
    return pd.Series(deltas, index=scores_df.index, name="sentiment_delta")


def extract_wish_phrases(text: str) -> list[str]:
    """Extract wish/feature-request phrases from review text using regex patterns.

    Args:
        text: Raw review text.

    Returns:
        List of matched wish phrase strings (stripped, length > 10).
    """
    matches = _WISH_RE.findall(text)
    return [m.strip() for m in matches if len(m.strip()) > 10]
