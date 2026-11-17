"""BERTopic training and inference for review topic clustering."""

import logging
from pathlib import Path

import numpy as np

from config import PROJECT_ROOT
from utils.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

_MIN_REVIEWS_FOR_TRAINING = 100
_MODEL_DIR = PROJECT_ROOT / "data" / "models"
_INSUFFICIENT_LABEL = "insufficient_data"
_OUTLIER_LABEL = "misc"

# BERTopic params tuned for small-to-medium review datasets (~100–500 docs)
_BERTOPIC_KWARGS = {
    "min_topic_size": 5,
    "nr_topics": "auto",
    "calculate_probabilities": False,
    "verbose": False,
}


def _model_path(competitor: str) -> Path:
    """Return the .pkl file path for a competitor's BERTopic model."""
    return _MODEL_DIR / f"bertopic_{competitor.lower().replace(' ', '_')}.pkl"


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed texts once with the shared model.

    The result can be passed to train_topics(), assign_topics() and
    pipeline.sentiment.score_sentiment_batch() so each review is encoded a
    single time per pipeline run instead of once per stage.
    """
    return get_embedding_model().encode(texts, show_progress_bar=False)


def train_topics(
    competitor: str,
    texts: list[str],
    embeddings: np.ndarray | None = None,
) -> None:
    """Train a BERTopic model on review texts for the given competitor and save it.

    Skips training and logs a warning if fewer than _MIN_REVIEWS_FOR_TRAINING
    texts are provided.

    Args:
        competitor: Competitor name — used to derive the save path.
        texts: List of review text strings.
        embeddings: Optional pre-computed embeddings aligned with texts.
    """
    if len(texts) < _MIN_REVIEWS_FOR_TRAINING:
        logger.warning(
            "[%s] Only %d reviews — below %d minimum for BERTopic. "
            "All reviews will receive topic_label='%s'.",
            competitor,
            len(texts),
            _MIN_REVIEWS_FOR_TRAINING,
            _INSUFFICIENT_LABEL,
        )
        # A model left over from an earlier, larger run would otherwise still be
        # picked up by assign_topics() and contradict the warning above.
        _model_path(competitor).unlink(missing_ok=True)
        return

    from bertopic import BERTopic

    logger.info("[%s] Training BERTopic on %d reviews ...", competitor, len(texts))
    model = BERTopic(embedding_model=get_embedding_model(), **_BERTOPIC_KWARGS)
    model.fit(texts, embeddings=embeddings)

    save_path = _model_path(competitor)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path), serialization="pickle", save_embedding_model=False)
    logger.info("[%s] BERTopic model saved to %s", competitor, save_path)


def assign_topics(
    texts: list[str],
    competitor: str,
    embeddings: np.ndarray | None = None,
) -> list[dict[str, int | str]]:
    """Assign topic cluster and label to each text using the saved model.

    If fewer texts than the training minimum were provided (and thus no model
    was saved), all texts receive topic_cluster=-1 and topic_label='insufficient_data'.

    Args:
        texts: List of review text strings.
        competitor: Competitor name — used to locate the saved model.
        embeddings: Optional pre-computed embeddings aligned with texts.

    Returns:
        List of dicts with keys: topic_cluster (int), topic_label (str).
        topic_cluster == -1 indicates BERTopic outlier (topic_label 'misc').
    """
    save_path = _model_path(competitor)

    if not save_path.exists():
        logger.info(
            "[%s] No saved BERTopic model — assigning '%s' to all reviews.",
            competitor,
            _INSUFFICIENT_LABEL,
        )
        return [
            {"topic_cluster": -1, "topic_label": _INSUFFICIENT_LABEL} for _ in texts
        ]

    from bertopic import BERTopic

    model = BERTopic.load(str(save_path), embedding_model=get_embedding_model())
    topics, _ = model.transform(texts, embeddings=embeddings)
    topic_info = model.get_topic_info()

    # Build cluster → human-readable label mapping.
    # BERTopic names look like "0_word1_word2_word3" — strip the id prefix.
    label_map: dict[int, str] = {}
    for _, row in topic_info.iterrows():
        cluster_id = int(row["Topic"])
        name_parts = str(row["Name"]).split("_", 1)
        label_map[cluster_id] = name_parts[1] if len(name_parts) > 1 else str(row["Name"])
    label_map[-1] = _OUTLIER_LABEL  # outlier bucket has keywords too, but is not a topic

    return [
        {"topic_cluster": int(t), "topic_label": label_map.get(int(t), str(t))}
        for t in topics
    ]
