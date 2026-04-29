"""BERTopic training and inference for review topic clustering."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_MIN_REVIEWS_FOR_TRAINING = 100
_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_MODEL_DIR = Path("data/models")
_INSUFFICIENT_LABEL = "insufficient_data"
_OUTLIER_LABEL = "misc"

# BERTopic params tuned for small-to-medium review datasets (~100–500 docs)
_BERTOPIC_KWARGS = {
    "embedding_model": _EMBEDDING_MODEL,
    "min_topic_size": 5,
    "nr_topics": "auto",
    "calculate_probabilities": False,
    "verbose": False,
}


def _model_path(competitor: str) -> Path:
    """Return the .pkl file path for a competitor's BERTopic model."""
    return _MODEL_DIR / f"bertopic_{competitor.lower().replace(' ', '_')}.pkl"


def train_topics(competitor: str, texts: list[str]) -> None:
    """Train a BERTopic model on review texts for the given competitor and save it.

    Skips training and logs a warning if fewer than _MIN_REVIEWS_FOR_TRAINING
    texts are provided.

    Args:
        competitor: Competitor name — used to derive the save path.
        texts: List of review text strings.
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
        return

    from bertopic import BERTopic

    logger.info("[%s] Training BERTopic on %d reviews ...", competitor, len(texts))
    model = BERTopic(**_BERTOPIC_KWARGS)
    model.fit(texts)

    save_path = _model_path(competitor)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path), serialization="pickle", save_embedding_model=False)
    logger.info("[%s] BERTopic model saved to %s", competitor, save_path)


def assign_topics(texts: list[str], competitor: str) -> list[dict[str, int | str]]:
    """Assign topic cluster and label to each text using the saved model.

    If fewer texts than the training minimum were provided (and thus no model
    was saved), all texts receive topic_cluster=-1 and topic_label='insufficient_data'.

    Args:
        texts: List of review text strings.
        competitor: Competitor name — used to locate the saved model.

    Returns:
        List of dicts with keys: topic_cluster (int), topic_label (str).
        topic_cluster == -1 indicates BERTopic outlier.
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
    from sentence_transformers import SentenceTransformer

    model = BERTopic.load(str(save_path), embedding_model=SentenceTransformer(_EMBEDDING_MODEL))
    topics, _ = model.transform(texts)
    topic_info = model.get_topic_info()

    # Build cluster → human-readable label mapping
    # BERTopic labels look like "0_word1_word2_word3" — use cleaned name
    label_map: dict[int, str] = {}
    for _, row in topic_info.iterrows():
        cluster_id = int(row["Topic"])
        # Use the BERTopic-generated name; strip the leading number prefix
        name_parts = str(row["Name"]).split("_", 1)
        label_map[cluster_id] = name_parts[1] if len(name_parts) > 1 else row["Name"]

    return [
        {
            "topic_cluster": int(t),
            "topic_label": label_map.get(int(t), _OUTLIER_LABEL if t == -1 else str(t)),
        }
        for t in topics
    ]
